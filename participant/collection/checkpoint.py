"""Trusted, non-overwriting approximate slot capture at a held boundary.

NPZ content is simulator-private. Only the trusted supervisor receives its path;
this module is never part of the actor tool schema or observation payload.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
SOURCE_FILES = ('config/assets.lock.json', 'config/policy_interface.json',
                'src/PhyRC_Sim/Policy/environment.py', 'src/PhyRC_Sim/Policy/stages.py',
                'src/PhyRC_Sim/Env_StandAlone/Teleop_TShirt_Stretch4_Env.py',
                'scripts/collect_operator.py', 'participant/collection/checkpoint.py')


def sha256(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def verify_checkpoint(path, *, source_group):
    """Check the receipt before any scene mutation or GPU initialization."""
    path = Path(path)
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('checkpoint_symlink_rejected')
    receipt_path = path.parent / 'receipt.json'
    if receipt_path.is_symlink():
        raise ValueError('checkpoint_symlink_rejected')
    receipt = json.loads(receipt_path.read_text())
    if receipt.get('schema') != 'phyrc-held-checkpoint-v1':
        raise ValueError('checkpoint_receipt_schema')
    if path.name != 'slot_' + receipt['key'] + '.npz':
        raise ValueError('checkpoint_receipt_name')
    if receipt['source_group'] != source_group:
        raise ValueError('checkpoint_source_group_mismatch')
    if receipt['slot_bytes'] != path.stat().st_size or receipt['slot_sha256'] != sha256(path):
        raise ValueError('checkpoint_hash_mismatch')
    if set(receipt['source_files_sha256']) != set(SOURCE_FILES):
        raise ValueError('checkpoint_source_manifest_incomplete')
    for name, expected in receipt['source_files_sha256'].items():
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts or sha256(ROOT / relative) != expected:
            raise ValueError('checkpoint_source_mismatch')
    return receipt


def save_checkpoint(env, operator, directory, key, *, run_id, source_group):
    if not operator._active or operator._hold_id is None:
        raise ValueError('checkpoint_requires_live_hold')
    if not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', key):
        raise ValueError('invalid_checkpoint_key')
    directory = Path(directory)
    if any(p.is_symlink() for p in (directory, *directory.parents)):
        raise ValueError('checkpoint_symlink_rejected')
    directory.mkdir(parents=True, exist_ok=True)
    # Reserve an entire fresh directory; the legacy saver may overwrite files,
    # so it must never see a pre-existing slot or a shared teleop F1 directory.
    destination = directory / key
    destination.mkdir(exist_ok=False)
    path = destination / ('slot_' + key + '.npz')
    tick_before = operator._tick
    clock_before = float(env.world.current_time)
    previous_directory = env.M.STATE_DIR
    try:
        env.M.STATE_DIR = str(destination)
        if not env.M.save_state_slot(key, env.cloths, env.rigs):
            raise RuntimeError('checkpoint_save_failed')
    finally:
        env.M.STATE_DIR = previous_directory
    if operator._tick != tick_before or float(env.world.current_time) != clock_before:
        raise RuntimeError('checkpoint_save_advanced_physics')
    from Policy.stages import validate_slot
    validate_slot(path, env.M._STATE_GEOMETRY_REVISION)
    operator._writer.flush()
    receipt = {
        'schema': 'phyrc-held-checkpoint-v1', 'run_id': run_id,
        'source_group': source_group, 'hold_id': operator._hold_id,
        'key': key, 'slot_path': str(path), 'slot_sha256': sha256(path),
        'slot_bytes': path.stat().st_size,
        'captured_utc': datetime.now(timezone.utc).isoformat(),
        'observation_step': tick_before // 12, 'episode_tick': tick_before,
        'simulation_time_s': float(operator._obs['simulation_time_s']),
        'world_time_s': clock_before, 'exact_physics_checkpoint': False,
        'restore_validated': False, 'geometry_revision': env.M._STATE_GEOMETRY_REVISION,
        'source_commit': getattr(env, '_source_commit', None),
        'source_files_sha256': {name: sha256(ROOT / name) for name in SOURCE_FILES},
        'restore': {'settle_control_ticks': 90, 'settle_simulation_seconds': 1.5,
                    'evaluation_restarts': True,
                    'reset_fields': ['base/root velocity', 'command ramps', 'pending grasp',
                                     'contact cache', 'command history']}}
    (destination / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt
