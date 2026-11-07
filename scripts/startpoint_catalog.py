#!/usr/bin/env python3
"""Build/query a disposable SQLite index of curated, trusted offline research JSON.

Never reads linked recordings, scores, receipts or actor files; never generates actions.
The versioned JSON is canonical. SQLite is only a rebuildable search index.
"""
import argparse
from contextlib import closing
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import tempfile
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / 'docs/collection/catalog/catalog.v1.json'
DEFAULT_DB = ROOT / 'output/indices/startpoint-catalog.sqlite3'
AXES = ('grasp_arrangement', 'entry_target', 'approach', 'order', 'view', 'action_encoding')
SUPPORT = ('unknown', 'uncertain', 'observed_unilateral', 'observed_bilateral')
METHOD_STATUS = ('proposed', 'ready', 'tested', 'retired')
ATTEMPT_STATUS = ('planned', 'in_progress', 'completed', 'failed')
RUN_KIND = ('demonstration', 'integration_test', 'failed_start', 'unknown')
QC_STATUS = ('unknown', 'pending', 'passed', 'failed')
BACKUP_STATUS = ('unknown', 'pending', 'verified', 'failed')
READY = "(sr.qc_status='passed' AND sr.backup_status='verified' AND sr.recorded_transitions IS NOT NULL AND s.boundary<=sr.recorded_transitions)"


class CatalogError(ValueError):
    pass


def require(value, message):
    if not value:
        raise CatalogError(message)


def fields(value, keys, where, optional=()):
    require(type(value) is dict, f'{where}: expected object')
    require(set(keys) <= value.keys(), f'{where}: missing fields {sorted(set(keys)-value.keys())}')
    require(value.keys() <= set(keys) | set(optional), f'{where}: unknown fields {sorted(value.keys()-set(keys)-set(optional))}')


def string(value, where, nullable=False):
    require((nullable and value is None) or (type(value) is str and bool(value.strip())), f'{where}: expected nonempty string' + (' or null' if nullable else ''))


def integer(value, where, nullable=False):
    require((nullable and value is None) or (type(value) is int and 0 <= value <= 2**63-1), f'{where}: expected nonnegative SQLite integer' + (' or null' if nullable else ''))


def boolean(value, where, nullable=False):
    require(type(value) is bool or (nullable and value is None), f'{where}: expected boolean' + (' or null' if nullable else ''))


def score(value, where):
    require(value is None or (type(value) in (int, float) and 0 <= value <= 50 and math.isfinite(value)), f'{where}: expected null or score in [0,50]')


def strings(value, where):
    require(type(value) is list, f'{where}: expected array')
    for item in value:
        string(item, where)


def enum(value, choices, where):
    require(type(value) is str and value in choices, f'{where}: expected one of {choices}')


def identifier(value, where):
    require(type(value) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,119}', value), f'{where}: invalid ID')


def digest(value, length, where):
    require(value is None or (type(value) is str and re.fullmatch(r'[0-9a-f]{'+str(length)+'}', value)), f'{where}: expected {length} lowercase hex digits or null')


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f'duplicate JSON key: {key}')
        result[key] = value
    return result


def reject_constant(value):
    raise CatalogError('nonfinite JSON value: ' + value)


def validate_catalog(raw):
    """Validate curated claims/relations, not original recording or score truth."""
    data = deepcopy(raw)
    fields(data, ('schema_version', 'catalog_id', 'runs', 'startpoints', 'methods', 'attempts'), 'catalog')
    require(type(data['schema_version']) is int and data['schema_version'] == 1, 'unsupported schema_version')
    identifier(data['catalog_id'], 'catalog_id')
    tables = {}
    for name in ('runs', 'startpoints', 'methods', 'attempts'):
        require(type(data[name]) is list, f'{name}: expected array')
        tables[name] = {}
        for item in data[name]:
            require(type(item) is dict and 'id' in item, f'{name}: record needs id')
            identifier(item['id'], name + '.id')
            require(item['id'] not in tables[name], f'{name}: duplicate id {item["id"]}')
            tables[name][item['id']] = item
    runs, points, methods, attempts = (tables[k] for k in ('runs', 'startpoints', 'methods', 'attempts'))
    for r in runs.values():
        where = 'run ' + r['id']
        fields(r, ('id', 'kind', 'source_group', 'source_commit', 'source_working_tree_modified',
                   'parent_run_id', 'replay_prefix_steps', 'replay_completed_steps',
                   'recorded_transitions', 'qc_status', 'backup'), where)
        enum(r['kind'], RUN_KIND, where + '.kind'); string(r['source_group'], where + '.source_group')
        digest(r['source_commit'], 40, where + '.source_commit')
        boolean(r['source_working_tree_modified'], where + '.source_working_tree_modified', True)
        integer(r['replay_prefix_steps'], where + '.replay_prefix_steps')
        integer(r['replay_completed_steps'], where + '.replay_completed_steps', True)
        integer(r['recorded_transitions'], where + '.recorded_transitions', True)
        completed, recorded = r['replay_completed_steps'], r['recorded_transitions']
        require(completed is None or completed <= r['replay_prefix_steps'], where + ': replay completed exceeds intended prefix')
        require(completed is None or recorded is None or completed <= recorded, where + ': replay completed exceeds recorded transitions')
        enum(r['qc_status'], QC_STATUS, where + '.qc_status')
        parent = r['parent_run_id']
        require(parent is None or (type(parent) is str and parent in runs and parent != r['id']), where + ': unknown/self parent')
        require(r['replay_prefix_steps'] == 0 or parent is not None, where + ': replay requires parent')
        backup = r['backup']
        fields(backup, ('status', 'receipt', 'revision', 'sha256'), where + '.backup')
        enum(backup['status'], BACKUP_STATUS, where + '.backup.status')
        for key in ('receipt', 'revision'):
            string(backup[key], where + '.backup.' + key, True)
        digest(backup['sha256'], 64, where + '.backup.sha256')
        require(backup['status'] != 'verified' or all(backup[k] is not None for k in ('receipt', 'revision', 'sha256')), where + ': verified backup needs receipt/revision/sha256')
        if backup['status'] == 'verified':
            digest(backup['revision'], 40, where + '.backup.revision (fixed commit)')
    for r in runs.values():
        if r['parent_run_id'] is not None and r['replay_prefix_steps']:
            parent = runs[r['parent_run_id']]
            require(r['source_group'] == parent['source_group'], 'run ' + r['id'] + ': replay source_group differs from parent')
            length = parent['recorded_transitions']
            require(length is None or r['replay_prefix_steps'] <= length, 'run ' + r['id'] + ': intended replay exceeds parent recording')
        seen = {r['id']}; parent = r['parent_run_id']
        while parent is not None:
            require(parent not in seen, 'parent cycle at ' + r['id'])
            seen.add(parent); parent = runs[parent]['parent_run_id']
    for p in points.values():
        where = 'startpoint ' + p['id']
        fields(p, ('id', 'source_run_id', 'boundary', 'history', 'support', 'score_at_boundary'), where,
               ('exact_checkpoint', 'training_approval'))
        p.setdefault('exact_checkpoint', False); p.setdefault('training_approval', 'unreviewed')
        require(p['exact_checkpoint'] is False, where + ': action replay is not an exact checkpoint')
        require(p['training_approval'] == 'unreviewed', where + ': this catalog cannot grant training approval')
        require(type(p['source_run_id']) is str and p['source_run_id'] in runs, where + ': unknown source run')
        integer(p['boundary'], where + '.boundary')
        length = runs[p['source_run_id']]['recorded_transitions']
        require(length is None or p['boundary'] <= length, where + ': boundary exceeds source recording')
        require(type(p['history']) is list, where + '.history: expected array')
        for h in p['history']:
            integer(h, where + '.history'); require(h < p['boundary'], where + ': history must precede boundary')
        require(all(a < b for a, b in zip(p['history'], p['history'][1:])), where + ': history must be unique and ascending')
        s = p['support']
        fields(s, ('status', 'evidence', 'uncertainty', 'window_start', 'window_end'), where + '.support')
        enum(s['status'], SUPPORT, where + '.support.status')
        strings(s['evidence'], where + '.support.evidence'); strings(s['uncertainty'], where + '.support.uncertainty')
        for key in ('window_start', 'window_end'):
            integer(s[key], where + '.support.' + key, True)
        require((s['window_start'] is None) == (s['window_end'] is None), where + ': support window must be both null or both integers')
        if s['window_start'] is not None:
            require(s['window_start'] <= s['window_end'] <= p['boundary'], where + ': invalid support window')
        require(not s['status'].startswith('observed_') or bool(s['evidence']), where + ': observed support needs public evidence')
        scored = p['score_at_boundary']
        fields(scored, ('raw_points', 'evidence'), where + '.score_at_boundary')
        score(scored['raw_points'], where + '.score_at_boundary.raw_points')
        string(scored['evidence'], where + '.score_at_boundary.evidence', True)
        require(scored['raw_points'] is None or scored['evidence'] is not None, where + ': known boundary score needs trusted evidence reference')
    for m in methods.values():
        where = 'method ' + m['id']
        fields(m, ('id', 'name', 'status', 'axes', 'description'), where)
        string(m['name'], where + '.name'); string(m['description'], where + '.description')
        enum(m['status'], METHOD_STATUS, where + '.status'); fields(m['axes'], AXES, where + '.axes')
        for axis in AXES:
            string(m['axes'][axis], where + '.axes.' + axis, True)
    used_runs = set()
    for a in attempts.values():
        where = 'attempt ' + a['id']
        fields(a, ('id', 'status', 'run_id', 'startpoint_id', 'method_id', 'result', 'notes'), where)
        enum(a['status'], ATTEMPT_STATUS, where + '.status'); string(a['notes'], where + '.notes', True)
        require(type(a['method_id']) is str and a['method_id'] in methods, where + ': unknown method')
        rid, sid = a['run_id'], a['startpoint_id']
        require(rid is None or (type(rid) is str and rid in runs), where + ': unknown run')
        require(sid is None or (type(sid) is str and sid in points), where + ': unknown startpoint')
        require(a['status'] == 'planned' or rid is not None, where + ': actual attempt requires run_id')
        require(a['status'] != 'planned' or rid is None, where + ': planned attempt must not claim an actual run')
        if rid is not None:
            require(rid not in used_runs, where + ': run already belongs to another attempt'); used_runs.add(rid)
            if sid is not None:
                p, r = points[sid], runs[rid]
                require(r['parent_run_id'] == p['source_run_id'], where + ': startpoint source is not immediate parent')
                require(r['replay_prefix_steps'] == p['boundary'], where + ': intended replay does not match chosen boundary')
        result = a['result']
        fields(result, ('raw_points', 'success', 'review', 'videos'), where + '.result')
        score(result['raw_points'], where + '.result.raw_points'); boolean(result['success'], where + '.result.success', True)
        string(result['review'], where + '.result.review', True); strings(result['videos'], where + '.result.videos')
        require(a['status'] != 'planned' or (result['raw_points'] is None and result['success'] is None and result['review'] is None and not result['videos']), where + ': planned attempt cannot claim observed results/review/video')
    for m in methods.values():
        linked = [a for a in attempts.values() if a['method_id'] == m['id']]
        require(m['status'] != 'tested' or any(a['status'] in ('completed', 'failed') for a in linked), 'method ' + m['id'] + ': tested requires a closed actual attempt')
        require(m['status'] != 'proposed' or not any(a['status'] != 'planned' for a in linked), 'method ' + m['id'] + ': proposed method has an actual attempt')
    return data


def load_catalog(source):
    raw = Path(source).read_bytes()
    try:
        value = json.loads(raw, object_pairs_hook=no_duplicate_keys, parse_constant=reject_constant)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise CatalogError('invalid catalog JSON: ' + str(exc)) from exc
    return validate_catalog(value), hashlib.sha256(raw).hexdigest()


DDL = '''
PRAGMA foreign_keys=ON;
CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE runs(id TEXT PRIMARY KEY, kind TEXT NOT NULL, source_group TEXT NOT NULL,
 source_commit TEXT, source_working_tree_modified INTEGER, parent_run_id TEXT REFERENCES runs(id) DEFERRABLE INITIALLY DEFERRED,
 replay_prefix_steps INTEGER NOT NULL CHECK(replay_prefix_steps>=0), replay_completed_steps INTEGER,
 recorded_transitions INTEGER, qc_status TEXT NOT NULL, backup_status TEXT NOT NULL, payload TEXT NOT NULL);
CREATE TABLE startpoints(id TEXT PRIMARY KEY, source_run_id TEXT NOT NULL REFERENCES runs(id),
 boundary INTEGER NOT NULL CHECK(boundary>=0), support_status TEXT NOT NULL,
 raw_points REAL CHECK(raw_points BETWEEN 0 AND 50), payload TEXT NOT NULL);
CREATE TABLE methods(id TEXT PRIMARY KEY, status TEXT NOT NULL, payload TEXT NOT NULL);
CREATE TABLE attempts(id TEXT PRIMARY KEY, status TEXT NOT NULL, run_id TEXT UNIQUE REFERENCES runs(id),
 startpoint_id TEXT REFERENCES startpoints(id), method_id TEXT NOT NULL REFERENCES methods(id),
 raw_points REAL CHECK(raw_points BETWEEN 0 AND 50), success INTEGER CHECK(success IN (0,1)), payload TEXT NOT NULL);
CREATE INDEX run_group_idx ON runs(source_group,kind,qc_status);
CREATE INDEX point_support_idx ON startpoints(support_status,raw_points);
CREATE INDEX method_status_idx ON methods(status);
CREATE INDEX attempt_combination_idx ON attempts(startpoint_id,method_id,status);
'''


def encoded(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True)


def build_catalog(source, database):
    source, database = Path(source), Path(database)
    require(source.resolve() != database.resolve(), 'database cannot overwrite canonical JSON')
    data, source_sha = load_catalog(source)  # Validate before creating/replacing any index.
    database.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.catalog-', suffix='.sqlite3', dir=database.parent); os.close(fd)
    try:
        with closing(sqlite3.connect(tmp)) as db, db:
            db.executescript(DDL)
            meta = {'schema_version': '1', 'catalog_id': data['catalog_id'], 'source_sha256': source_sha,
                'source_path': str(source.resolve()), 'built_at_utc': datetime.now(timezone.utc).isoformat(),
                'usage': 'trusted_offline_research_only', 'canonical_source': 'versioned_json'}
            db.executemany('INSERT INTO metadata VALUES(?,?)', meta.items())
            for r in data['runs']:
                db.execute('INSERT INTO runs VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                    (r['id'],r['kind'],r['source_group'],r['source_commit'],r['source_working_tree_modified'],
                     r['parent_run_id'],r['replay_prefix_steps'],r['replay_completed_steps'],r['recorded_transitions'],
                     r['qc_status'],r['backup']['status'],encoded(r)))
            for p in data['startpoints']:
                db.execute('INSERT INTO startpoints VALUES(?,?,?,?,?,?)',
                    (p['id'],p['source_run_id'],p['boundary'],p['support']['status'],p['score_at_boundary']['raw_points'],encoded(p)))
            for m in data['methods']:
                db.execute('INSERT INTO methods VALUES(?,?,?)', (m['id'],m['status'],encoded(m)))
            for a in data['attempts']:
                db.execute('INSERT INTO attempts VALUES(?,?,?,?,?,?,?,?)',
                    (a['id'],a['status'],a['run_id'],a['startpoint_id'],a['method_id'],a['result']['raw_points'],a['result']['success'],encoded(a)))
            require(not db.execute('PRAGMA foreign_key_check').fetchall(), 'SQLite foreign key check failed')
        os.replace(tmp, database)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
    return {'database': str(database), 'source_sha256': source_sha, 'counts': {k:len(data[k]) for k in ('runs','startpoints','methods','attempts')}}


def open_database(path):
    path = Path(path)
    require(path.is_file(), f'index not found: {path}; run build first')
    db = sqlite3.connect('file:' + quote(str(path.resolve())) + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    try:
        meta = dict(db.execute('SELECT key,value FROM metadata'))
        require(meta.get('schema_version') == '1', 'unsupported index schema; rebuild from JSON')
    except Exception:
        db.close()
        raise
    return db, meta


def fetch(db, table, ident):
    require(table in ('runs','startpoints','methods','attempts'), 'unknown entity')
    row = db.execute(f'SELECT payload FROM {table} WHERE id=?', (ident,)).fetchone()
    require(row is not None, f'{table}: unknown id {ident}')
    return json.loads(row['payload'])


def point_status(db, point):
    run = fetch(db, 'runs', point['source_run_id'])
    length = run['recorded_transitions']
    valid = None if length is None else point['boundary'] <= length
    return {'source_group': run['source_group'], 'source_kind': run['kind'],
        'source_commit': run['source_commit'], 'source_working_tree_modified': run['source_working_tree_modified'],
        'boundary_valid': valid, 'review_ready': valid is True and run['qc_status']=='passed' and run['backup']['status']=='verified'}


def summarize(db, table, ident):
    record = fetch(db, table, ident)
    if table == 'startpoints':
        record.update(point_status(db, record))
    elif table == 'attempts':
        run = fetch(db, 'runs', record['run_id']) if record['run_id'] else None
        point = fetch(db, 'startpoints', record['startpoint_id']) if record['startpoint_id'] else None
        record['source_group'] = run['source_group'] if run else (point_status(db, point)['source_group'] if point else None)
        completed = run['replay_completed_steps'] if run else None
        record['startpoint_reached'] = None if point is None or completed is None else completed >= point['boundary']
        record['method_status'] = fetch(db, 'methods', record['method_id'])['status']
    return record


def select_records(db, entity, filters):
    require(entity in ('runs','startpoints','methods','attempts'), 'unknown entity')
    aliases = {'runs':'r','startpoints':'s','methods':'m','attempts':'a'}
    joins = {
        'runs':'runs r',
        'startpoints':'startpoints s JOIN runs sr ON sr.id=s.source_run_id LEFT JOIN attempts a ON a.startpoint_id=s.id LEFT JOIN methods m ON m.id=a.method_id',
        'methods':'methods m LEFT JOIN attempts a ON a.method_id=m.id LEFT JOIN startpoints s ON s.id=a.startpoint_id LEFT JOIN runs sr ON sr.id=s.source_run_id LEFT JOIN runs r ON r.id=a.run_id',
        'attempts':'attempts a JOIN methods m ON m.id=a.method_id LEFT JOIN startpoints s ON s.id=a.startpoint_id LEFT JOIN runs sr ON sr.id=s.source_run_id LEFT JOIN runs r ON r.id=a.run_id',
    }
    expressions = {'source_group': 'r.source_group' if entity=='runs' else ('sr.source_group' if entity=='startpoints' else 'COALESCE(r.source_group,sr.source_group)'),
        'run_kind': 'r.kind' if entity=='runs' else ('sr.kind' if entity=='startpoints' else 'COALESCE(r.kind,sr.kind)'),
        'qc_status': 'sr.qc_status' if entity=='startpoints' else 'r.qc_status',
        'support_status':'s.support_status','boundary_score':'s.raw_points','result_score':'a.raw_points',
        'method_status':'m.status','method_id':'m.id','attempt_status':'a.status'}
    where, values = [], []
    if entity=='runs':
        unsupported = set(filters)-{'source_group','run_kind','qc_status'}
        require(not unsupported, 'runs filters only support source_group/run_kind/qc_status')
    for key, value in filters.items():
        if key == 'review_ready':
            where.append(('' if value else 'NOT ') + 'COALESCE(' + READY + ',0)')
        elif key in ('boundary_score_unknown','result_score_unknown'):
            where.append(expressions[key.removesuffix('_unknown')] + ' IS NULL')
        else:
            require(key in expressions, 'unknown filter: '+key)
            where.append(expressions[key] + '=?'); values.append(value)
    sql = 'SELECT DISTINCT ' + aliases[entity]+'.id AS id FROM '+joins[entity]
    if where: sql += ' WHERE ' + ' AND '.join(where)
    sql += ' ORDER BY ' + aliases[entity]+'.id'
    return [summarize(db, entity, row['id']) for row in db.execute(sql, values)]


def matrix(db, filters):
    """Only registered combinations; never invent a Cartesian experiment grid."""
    groups = {}
    for attempt in select_records(db, 'attempts', filters):
        key = (attempt['source_group'], attempt['startpoint_id'], attempt['method_id'])
        if key not in groups:
            method = fetch(db, 'methods', attempt['method_id'])
            groups[key] = {'source_group':key[0], 'startpoint_id':key[1], 'method_id':key[2],
                'method_status':method['status'], 'axes':method['axes'],
                'status_counts':dict.fromkeys(ATTEMPT_STATUS,0),
                'actual_startpoint_counts':dict.fromkeys(('reached','unreached','unknown','not_applicable'),0),
                'attempts':[]}
        row = groups[key]; row['status_counts'][attempt['status']] += 1
        if attempt['status'] != 'planned':
            reached = attempt['startpoint_reached']
            reach_key = ('not_applicable' if attempt['startpoint_id'] is None else
                         'unknown' if reached is None else 'reached' if reached else 'unreached')
            row['actual_startpoint_counts'][reach_key] += 1
        row['attempts'].append(attempt)
    return list(groups.values())


def show_record(db, entity, ident):
    result = summarize(db, entity, ident)
    if entity == 'runs':
        result['startpoint_ids'] = [r[0] for r in db.execute('SELECT id FROM startpoints WHERE source_run_id=? ORDER BY id',(ident,))]
        result['attempt_ids'] = [r[0] for r in db.execute('SELECT id FROM attempts WHERE run_id=? ORDER BY id',(ident,))]
    elif entity in ('startpoints','methods'):
        key = 'startpoint_id' if entity=='startpoints' else 'method_id'
        result['attempts'] = [summarize(db,'attempts',r[0]) for r in db.execute(f'SELECT id FROM attempts WHERE {key}=? ORDER BY id',(ident,))]
    return result


def add_filters(parser):
    parser.add_argument('--source-group'); parser.add_argument('--run-kind', choices=RUN_KIND)
    parser.add_argument('--qc-status', choices=QC_STATUS); parser.add_argument('--support-status', choices=SUPPORT)
    parser.add_argument('--method-status', choices=METHOD_STATUS); parser.add_argument('--method-id')
    parser.add_argument('--attempt-status', choices=ATTEMPT_STATUS)
    for label in ('boundary','result'):
        group = parser.add_mutually_exclusive_group()
        group.add_argument('--'+label+'-score', type=float)
        group.add_argument('--'+label+'-score-unknown', action='store_true')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--ready', action='store_true'); group.add_argument('--not-ready', action='store_true')
    parser.add_argument('--limit', type=int, default=100)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    build = sub.add_parser('build'); build.add_argument('--source',type=Path,default=DEFAULT_SOURCE); build.add_argument('--db',type=Path,default=DEFAULT_DB)
    validate = sub.add_parser('validate'); validate.add_argument('--source',type=Path,default=DEFAULT_SOURCE); validate.add_argument('--db',type=Path)
    listing = sub.add_parser('list',aliases=['query']); listing.add_argument('entity',nargs='?',default='startpoints',choices=['runs','startpoints','methods','attempts']); listing.add_argument('--db',type=Path,default=DEFAULT_DB); add_filters(listing)
    grid = sub.add_parser('matrix'); grid.add_argument('--db',type=Path,default=DEFAULT_DB); add_filters(grid)
    show = sub.add_parser('show'); show.add_argument('entity',choices=['runs','startpoints','methods','attempts']); show.add_argument('id'); show.add_argument('--db',type=Path,default=DEFAULT_DB)
    args = parser.parse_args(argv)
    try:
        if args.command == 'build':
            result = build_catalog(args.source,args.db)
        elif args.command == 'validate':
            data, digest_value = load_catalog(args.source)
            result = {'valid':True,'source_sha256':digest_value,'counts':{k:len(data[k]) for k in ('runs','startpoints','methods','attempts')},'validation_scope':'curated schema/relations only; linked evidence was not opened'}
            if args.db:
                db, meta = open_database(args.db)
                try:
                    require(meta['source_sha256']==digest_value,'index is stale: canonical JSON hash differs; rebuild')
                    require(not db.execute('PRAGMA foreign_key_check').fetchall(),'index foreign key check failed')
                finally: db.close()
                result['index_matches_source'] = True
        else:
            db, meta = open_database(args.db)
            try:
                if args.command == 'show': result = show_record(db,args.entity,args.id)
                else:
                    require(1<=args.limit<=10000,'limit must be 1..10000')
                    filters = {key:getattr(args,key) for key in ('source_group','run_kind','qc_status','support_status','method_status','method_id','attempt_status','boundary_score','result_score') if getattr(args,key) is not None}
                    for label in ('boundary','result'):
                        if getattr(args,label+'_score_unknown'):filters[label+'_score_unknown']=True
                        if label+'_score' in filters:score(filters[label+'_score'],label+'_score')
                    if args.ready or args.not_ready:filters['review_ready']=bool(args.ready)
                    rows = matrix(db,filters) if args.command=='matrix' else select_records(db,args.entity,filters)
                    result = {'total':len(rows),'items':rows[:args.limit],'index_source_sha256':meta['source_sha256']}
            finally: db.close()
        print(json.dumps({'usage':'trusted_offline_research_only','result':result},ensure_ascii=False,indent=2,allow_nan=False))
        return 0
    except (CatalogError,OSError,sqlite3.Error) as exc:
        parser.exit(2, 'catalog error: '+str(exc)+'\n')


if __name__ == '__main__':
    raise SystemExit(main())
