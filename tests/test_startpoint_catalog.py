"""Offline catalog integrity and query semantics, with synthetic curated claims only."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from scripts import startpoint_catalog as catalog


def fixture():
    def run(ident, *, parent=None, intended=0, completed=0, recorded=928,
            group='family', qc='passed', backup='verified', dirty=False):
        return dict(id=ident, kind='demonstration', source_group=group,
            source_commit='a'*40, source_working_tree_modified=dirty,
            parent_run_id=parent, replay_prefix_steps=intended,
            replay_completed_steps=completed, recorded_transitions=recorded,
            qc_status=qc, backup=dict(status=backup,
                receipt='nonexistent/receipt.json' if backup=='verified' else None,
                revision='c'*40 if backup=='verified' else None,
                sha256='b'*64 if backup=='verified' else None))

    def point(ident, source, boundary, support, score):
        return dict(id=ident, source_run_id=source, boundary=boundary,
            history=[boundary-2,boundary-1],
            support=dict(status=support, evidence=['public/observation.json: discrete review'],
                uncertainty=['Not a continuous review or independent support proof.'],
                window_start=boundary-2, window_end=boundary),
            score_at_boundary=dict(raw_points=score,
                evidence='trusted offline boundary review' if score is not None else None))

    def method(ident, status):
        return dict(id=ident, name=ident, status=status,
            axes=dict(zip(catalog.AXES, ['bilateral edge','body opening','overhead',
                                      'unspecified','multiview','named'])),
            description='Comparison configuration, not a demonstrated successful skill.')

    def attempt(ident, status, run_id, start, method_id, score=None):
        return dict(id=ident, status=status, run_id=run_id, startpoint_id=start,
            method_id=method_id, result=dict(raw_points=score,
                success=False if status=='completed' else None,
                review='reviews/closed.md' if status=='completed' else None,
                videos=['videos/closed.mp4'] if status=='completed' else []),
            notes='A failed attempt may not reach its intended starting boundary.')

    return dict(schema_version=1, catalog_id='synthetic-tests',
        runs=[run('source'),
              run('failed',parent='source',intended=700,completed=120,recorded=141,dirty=True),
              run('closed',parent='source',intended=470,completed=470,recorded=600),
              # Parent can describe lineage without replay; new source group is valid here.
              run('fresh',parent='source',recorded=30,group='fresh-family',backup='pending'),
              run('unknown',recorded=None,completed=None,qc='unknown',backup='unknown',dirty=None)],
        startpoints=[point('edge470','source',470,'observed_bilateral',5),
                     point('historical700','source',700,'uncertain',0),
                     point('pending20','fresh',20,'observed_bilateral',5),
                     point('unknown20','unknown',20,'unknown',None)],
        methods=[method('used','tested'),method('candidate','proposed'),method('unused','ready')],
        attempts=[attempt('closed-attempt','completed','closed','edge470','used',5),
                  attempt('failed-attempt','failed','failed','historical700','used'),
                  attempt('repeat-plan','planned',None,'edge470','used'),
                  attempt('new-plan','planned',None,'edge470','candidate')])


class StartpointCatalogTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.source = Path(self.tmp.name)/'catalog.v1.json'
        self.database = Path(self.tmp.name)/'indices/catalog.sqlite3'
        self.data = fixture()
        self.write()

    def write(self):
        self.source.write_text(json.dumps(self.data,ensure_ascii=False,allow_nan=False))

    def build(self):
        result = catalog.build_catalog(self.source,self.database)
        db, meta = catalog.open_database(self.database)
        self.addCleanup(db.close)
        return db, meta, result

    def cli(self, *args, ok=True):
        result = subprocess.run([sys.executable,str(Path(catalog.__file__)),*map(str,args)],
            text=True,capture_output=True)
        self.assertEqual(result.returncode,0 if ok else 2,result.stderr)
        return json.loads(result.stdout)['result'] if ok else result.stderr

    def test_roundtrip_defaults_provenance_and_claims_without_opening_linked_files(self):
        self.data['runs'].reverse()  # JSON order is not a parent-before-child contract.
        self.write()
        original = self.source.read_bytes()
        db, meta, result = self.build()
        self.assertEqual(self.source.read_bytes(),original)
        self.assertEqual(meta['source_sha256'],hashlib.sha256(original).hexdigest())
        self.assertEqual(result['counts'],dict(runs=5,startpoints=4,methods=3,attempts=4))
        for entity in ('runs','methods','attempts'):
            for record in self.data[entity]:
                self.assertEqual(catalog.fetch(db,entity,record['id']),record)
        point = catalog.fetch(db,'startpoints','edge470')
        self.assertIs(point['exact_checkpoint'],False)
        self.assertEqual(point['training_approval'],'unreviewed')
        self.assertNotIn('exact_checkpoint',self.data['startpoints'][0])
        self.assertIs(catalog.fetch(db,'runs','failed')['source_working_tree_modified'],True)
        self.assertIsNone(catalog.fetch(db,'runs','unknown')['source_working_tree_modified'])
        self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(),[])
        with self.assertRaises(sqlite3.OperationalError):
            db.execute("DELETE FROM runs")  # Queries open the generated index read-only.

    def test_ready_support_and_boundary_score_are_independent_filters(self):
        db, _, _ = self.build()
        def ids(filters):
            return [r['id'] for r in catalog.select_records(db,'startpoints',filters)]
        self.assertEqual(ids({'review_ready':True}),['edge470','historical700'])
        self.assertEqual(ids({'support_status':'observed_bilateral'}),['edge470','pending20'])
        self.assertEqual(ids({'boundary_score':5,'review_ready':True}),['edge470'])
        self.assertEqual(ids({'boundary_score':0}),['historical700'])
        self.assertEqual(ids({'boundary_score_unknown':True}),['unknown20'])
        self.assertEqual(ids({'review_ready':False}),['pending20','unknown20'])
        self.assertIsNone(catalog.show_record(db,'startpoints','unknown20')['boundary_valid'])
        self.assertIs(catalog.show_record(db,'startpoints','unknown20')['review_ready'],False)

    def test_failed_replay_does_not_claim_chosen_startpoint_was_reached(self):
        db, _, _ = self.build()
        failed = catalog.show_record(db,'attempts','failed-attempt')
        self.assertIs(failed['startpoint_reached'],False)
        self.assertEqual(failed['startpoint_id'],'historical700')
        run = catalog.show_record(db,'runs','failed')
        self.assertEqual((run['replay_prefix_steps'],run['replay_completed_steps'],run['recorded_transitions']),(700,120,141))
        self.assertIs(catalog.show_record(db,'attempts','closed-attempt')['startpoint_reached'],True)
        self.assertIsNone(catalog.show_record(db,'attempts','repeat-plan')['startpoint_reached'])
        # A collector can start before any intended replay has completed.
        self.data['runs'][1].update(replay_completed_steps=0,recorded_transitions=0)
        self.data['attempts'][1]['status']='in_progress'
        catalog.validate_catalog(self.data)

    def test_matrix_only_registered_combinations_preserves_attempt_statuses(self):
        db, _, _ = self.build()
        rows = catalog.matrix(db,{})
        self.assertEqual(len(rows),3)  # Not the 4 points x 3 methods Cartesian product.
        self.assertNotIn('unused',[r['method_id'] for r in rows])
        used = next(r for r in rows if r['startpoint_id']=='edge470' and r['method_id']=='used')
        self.assertEqual(used['status_counts'],dict(planned=1,in_progress=0,completed=1,failed=0))
        self.assertEqual(used['actual_startpoint_counts'],dict(reached=1,unreached=0,unknown=0,not_applicable=0))
        failed = next(r for r in rows if r['startpoint_id']=='historical700')
        self.assertEqual(failed['actual_startpoint_counts'],dict(reached=0,unreached=1,unknown=0,not_applicable=0))
        planned = catalog.matrix(db,{'method_status':'proposed','attempt_status':'planned'})
        self.assertEqual([r['method_id'] for r in planned],['candidate'])
        self.assertEqual(sum(planned[0]['actual_startpoint_counts'].values()),0)
        self.assertEqual(catalog.matrix(db,{'result_score':0}),[])
        self.assertEqual(len(catalog.matrix(db,{'result_score_unknown':True})),3)
        self.data['runs'][1]['replay_completed_steps']=None
        self.data['attempts'][0]['startpoint_id']=None
        self.write(); second, _, _=self.build()
        rows=catalog.matrix(second,{})
        failed=next(r for r in rows if r['startpoint_id']=='historical700')
        self.assertEqual(failed['actual_startpoint_counts']['unknown'],1)
        fresh=next(r for r in rows if r['startpoint_id'] is None)
        self.assertEqual(fresh['actual_startpoint_counts']['not_applicable'],1)

    def test_fresh_lineage_different_group_allowed_but_replay_group_and_parent_strict(self):
        catalog.validate_catalog(self.data)
        mutations = [
            ('replay family',lambda d:d['runs'][1].update(source_group='another')),
            ('chosen parent',lambda d:d['runs'][1].update(parent_run_id='closed')),
            ('chosen boundary',lambda d:d['runs'][1].update(replay_prefix_steps=701)),
            ('unknown parent',lambda d:d['runs'][1].update(parent_run_id='absent')),
            ('cycle',lambda d:d['runs'][0].update(parent_run_id='fresh')),
            ('parent range',lambda d:d['runs'][0].update(recorded_transitions=699)),
            ('completion over intent',lambda d:d['runs'][1].update(replay_completed_steps=701)),
            ('completion over recording',lambda d:d['runs'][1].update(recorded_transitions=119)),
        ]
        for name, mutate in mutations:
            with self.subTest(name=name):
                data=deepcopy(self.data);mutate(data)
                with self.assertRaises(catalog.CatalogError):catalog.validate_catalog(data)
        # Scalar parent errors must be reported cleanly even when child appears first.
        data=deepcopy(self.data);data['runs'].reverse()
        data['runs'][-1]['recorded_transitions']='invalid'
        with self.assertRaises(catalog.CatalogError):catalog.validate_catalog(data)

    def test_window_history_boundary_and_review_constraints(self):
        mutations = [
            ('window half null',lambda p:p['support'].update(window_start=None)),
            ('window reversed',lambda p:p['support'].update(window_start=470,window_end=469)),
            ('window beyond',lambda p:p['support'].update(window_end=471)),
            ('history same boundary',lambda p:p.update(history=[470])),
            ('history duplicate',lambda p:p.update(history=[460,460])),
            ('history reverse',lambda p:p.update(history=[469,468])),
            ('boundary beyond source',lambda p:p.update(boundary=929)),
            ('support no evidence',lambda p:p['support'].update(evidence=[])),
            ('score no evidence',lambda p:p['score_at_boundary'].update(evidence=None)),
            ('exact checkpoint',lambda p:p.update(exact_checkpoint=True)),
            ('training approval',lambda p:p.update(training_approval='approved')),
        ]
        for name, mutate in mutations:
            with self.subTest(name=name):
                data=deepcopy(self.data);mutate(data['startpoints'][0])
                with self.assertRaises(catalog.CatalogError):catalog.validate_catalog(data)

    def test_null_zero_bool_nonfinite_huge_ranges_and_duplicate_json(self):
        for value in (True,False,-1,51,float('nan'),float('inf'),10**1000):
            with self.subTest(score=repr(value)[:30]):
                data=deepcopy(self.data);data['startpoints'][0]['score_at_boundary']['raw_points']=value
                with self.assertRaises(catalog.CatalogError):catalog.validate_catalog(data)
        for value in (True,-1,2**63):
            data=deepcopy(self.data);data['runs'][0]['recorded_transitions']=value
            with self.assertRaises(catalog.CatalogError):catalog.validate_catalog(data)
        for text in ('{"schema_version":1,"schema_version":1}',
                     '{"nested":{"x":1,"x":2}}','{"score":NaN}','{"score":Infinity}'):
            self.source.write_text(text)
            with self.assertRaises(catalog.CatalogError):catalog.load_catalog(self.source)

    def test_duplicates_foreign_keys_proposed_status_and_false_results_rejected(self):
        mutations = [
            ('duplicate ID',lambda d:d['runs'].append(deepcopy(d['runs'][0]))),
            ('missing method',lambda d:d['attempts'][0].update(method_id='absent')),
            ('missing startpoint',lambda d:d['attempts'][0].update(startpoint_id='absent')),
            ('duplicate actual run',lambda d:d['attempts'][1].update(run_id='closed',startpoint_id='edge470')),
            ('proposed actual',lambda d:d['methods'][0].update(status='proposed')),
            ('untested tested',lambda d:d['methods'][2].update(status='tested')),
            ('planned actual run',lambda d:d['attempts'][2].update(run_id='closed')),
            ('planned observed score',lambda d:d['attempts'][2]['result'].update(raw_points=5)),
            ('planned observed success',lambda d:d['attempts'][2]['result'].update(success=False)),
            ('planned observed video',lambda d:d['attempts'][2]['result'].update(videos=['video.mp4'])),
            ('planned result review',lambda d:d['attempts'][2]['result'].update(review='review.md')),
            ('missing dirty provenance',lambda d:d['runs'][0].pop('source_working_tree_modified')),
            ('unknown field',lambda d:d['runs'][0].update(hidden_state={})),
            ('verified without receipt',lambda d:d['runs'][0]['backup'].update(receipt=None)),
            ('verified mutable revision',lambda d:d['runs'][0]['backup'].update(revision='main')),
        ]
        for name, mutate in mutations:
            with self.subTest(name=name):
                data=deepcopy(self.data);mutate(data)
                with self.assertRaises(catalog.CatalogError):catalog.validate_catalog(data)

    def test_sqlite_primary_and_foreign_keys_are_enforced_beyond_json_validation(self):
        self.build()
        with sqlite3.connect(self.database) as db:
            db.execute('PRAGMA foreign_keys=ON')
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute('INSERT INTO methods SELECT * FROM methods LIMIT 1')
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("INSERT INTO startpoints VALUES('bad','absent',0,'unknown',NULL,'{}')")
            self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(),[])

    def test_invalid_rebuild_keeps_previous_index_and_source_is_never_overwritten(self):
        self.build();old=self.database.read_bytes()
        self.data['attempts'][0]['method_id']='absent';self.write()
        with self.assertRaises(catalog.CatalogError):catalog.build_catalog(self.source,self.database)
        self.assertEqual(self.database.read_bytes(),old)
        before=self.source.read_bytes()
        with self.assertRaises(catalog.CatalogError):catalog.build_catalog(self.source,self.source)
        self.assertEqual(self.source.read_bytes(),before)
        self.assertEqual(list(self.database.parent.glob('.catalog-*')),[])

    def test_cli_build_validate_list_show_matrix_and_stale_detection(self):
        built=self.cli('build','--source',self.source,'--db',self.database)
        self.assertEqual(built['counts']['runs'],5)
        self.assertTrue(self.cli('validate','--source',self.source,'--db',self.database)['index_matches_source'])
        rows=self.cli('query','startpoints','--db',self.database,'--source-group','family',
                      '--support-status','observed_bilateral','--boundary-score','5','--ready')
        self.assertEqual([r['id'] for r in rows['items']],['edge470'])
        shown=self.cli('show','runs','source','--db',self.database)
        self.assertEqual(shown['startpoint_ids'],['edge470','historical700'])
        self.assertEqual(self.cli('matrix','--db',self.database,'--attempt-status','failed')['total'],1)
        self.data['catalog_id']='changed';self.write()
        self.assertIn('stale',self.cli('validate','--source',self.source,'--db',self.database,ok=False))
        self.assertIn('runs filters',self.cli('list','runs','--db',self.database,'--ready',ok=False))
        self.assertIn('score',self.cli('list','--db',self.database,'--boundary-score','nan',ok=False))
        self.assertIn('unknown id',self.cli('show','runs',"source' OR 1=1 --",'--db',self.database,ok=False))


if __name__=='__main__':
    unittest.main()
