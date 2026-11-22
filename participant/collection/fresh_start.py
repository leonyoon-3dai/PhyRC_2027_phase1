"""Trusted practice reset for the single nearest garment table, using the official sampler."""
import numpy as np

from Env_Config.Garment.RandomSpawn import sample_garment_spawn
from Env_Config.Randomization import spawn_randomization_enabled


TABLE_INDEX = 2  # Positive-X central table in the four-table challenge scene.
FIRST_SEED = 43


def select_practice_reset(centers, size, bases, seed=None):
    """Condition an official seed without stepping, moving any object or resetting twice."""
    if not spawn_randomization_enabled():
        raise ValueError('nearest-table collection requires the official randomized reset')
    centers = np.asarray(centers, dtype=float)
    bases = np.asarray(bases, dtype=float)
    if (centers.shape != (4, 3) or bases.shape != (2, 3)
            or not np.isfinite(centers).all() or not np.isfinite(bases).all()):
        raise ValueError('expected four table centers and two finite robot base positions')
    distances = np.linalg.norm(centers[:, None, :2] - bases[None, :, :2], axis=2).mean(axis=1)
    if not np.isclose(distances[TABLE_INDEX], distances.min(), atol=1e-6, rtol=0):
        raise ValueError('table 2 is not a nearest table in this scene')
    first = FIRST_SEED if seed is None else seed
    if type(first) is not int or not 0 <= first < 2**63:
        raise ValueError('practice seed must be in 0..2**63-1')
    for offset in range(4096):
        value = (first + offset) % (2**63)
        placement = sample_garment_spawn(centers, size, seed=value)
        if placement['table_index'] == TABLE_INDEX:
            return {'profile': 'fresh-nearest-table-cp2', 'start_step': 0,
                    'requested_seed': first, 'episode_seed': value, 'table_index': TABLE_INDEX,
                    'table_prim_path': placement['table_prim_path'],
                    'mean_base_distance_xy_m': distances.tolist()}
    raise RuntimeError('official sampler did not return the fixed nearest table')


def verify_reset(info, profile, stage):
    """Verify the actual trusted reset and authored material before accepting a first action."""
    expected = profile['table_index']
    garment = info.get('garment_spawn', {})
    if (info.get('episode_seed') != profile['episode_seed'] or info.get('step_id') != 0
            or garment.get('table_index') != expected
            or garment.get('table_prim_path') != profile['table_prim_path']):
        raise RuntimeError('actual reset differs from the fresh nearest-table profile')
    material = stage.GetPrimAtPath('/World/HumanClothContactMaterial')
    if not material:
        raise RuntimeError('official shirt/manikin material missing; run prepare')
    for name in ('physics:staticFriction', 'physics:dynamicFriction'):
        attr = material.GetAttribute(name)
        value = attr.Get() if attr else None
        if value is None or not np.isclose(value, 0.35, rtol=0, atol=1e-6):
            raise RuntimeError('checkpoint 2 requires shirt/manikin friction 0.35')
    return {**profile, 'table_center_world_m': garment['table_center_world_m'],
            'shirt_manikin_friction': 0.35, 'verified_after_reset': True}
