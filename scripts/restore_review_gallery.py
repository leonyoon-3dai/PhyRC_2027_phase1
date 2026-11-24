"""Restore a closed series' SQLite journal and reviewed MP4s to a new gallery directory."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import tarfile
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,119}')


def checked_file(directory, item):
    path = (directory / item['path']).resolve()
    path.relative_to(directory.resolve())
    with path.open('rb') as source:
        if path.stat().st_size != item['bytes'] or hashlib.file_digest(source, 'sha256').hexdigest() != item['sha256']:
            raise ValueError(f'Backup checksum mismatch: {path.name}')
    return path


def restore(manifest, directory, destination):
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f'Choose a new gallery directory: {destination}')
    journal = checked_file(directory, manifest['journal'])
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as tmp:
        staged = Path(tmp) / 'gallery'
        staged.mkdir(mode=0o700)
        db_path = staged / 'journal.sqlite3'
        shutil.copyfile(journal, db_path)
        with sqlite3.connect(db_path.resolve().as_uri() + '?mode=ro', uri=True) as db:
            if (db.execute('PRAGMA integrity_check').fetchone() != ('ok',)
                    or db.execute('PRAGMA foreign_key_check').fetchone() is not None):
                raise ValueError('Invalid review database')
            digest_rows = list(db.execute('SELECT run,segment,digest FROM segments ORDER BY rowid'))
        runs = {row['run_id']: row for row in manifest['runs']}
        if set(runs) != {run for run, _, _ in digest_rows}:
            raise ValueError('Journal runs differ from the backup receipt')
        for run, metadata in runs.items():
            if not ID.fullmatch(run):
                raise ValueError('Unexpected run ID')
            media = staged / 'media' / run
            media.mkdir(parents=True)
            with zipfile.ZipFile(checked_file(directory, metadata['review_zip'])) as archive:
                for stored_run, hold, digest in digest_rows:
                    if stored_run != run:
                        continue
                    if not ID.fullmatch(hold):
                        raise ValueError('Unexpected segment ID')
                    mp4 = media / (hold + '.mp4')
                    with archive.open(mp4.relative_to(staged).as_posix()) as source, mp4.open('xb') as output:
                        shutil.copyfileobj(source, output)
                    with mp4.open('rb') as f:
                        if hashlib.file_digest(f, 'sha256').hexdigest() != digest:
                            raise ValueError(f'Clip differs from the reviewed observation: {run}/{hold}')
        staged.rename(destination)
    return len(digest_rows)


def restore_frames(manifest, directory, destination):
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f'Choose a new frames directory: {destination}')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as tmp:
        staged = Path(tmp) / 'frames'
        staged.mkdir(mode=0o700)
        for item in manifest['runs']:
            run, count = item['run_id'], item['review_frame_count']
            if not ID.fullmatch(run) or type(count) is not int or count < 1:
                raise ValueError('Unexpected review frame metadata')
            folder = staged / run / 'segment-frames'
            folder.mkdir(parents=True)
            expected = {f'{step:06d}.jpg' for step in range(count)}
            path = checked_file(directory, item['review_frames'])
            with tarfile.open(path, 'r|gz') as archive:
                for member in archive:
                    if not member.isfile() or member.name not in expected:
                        raise ValueError(f'Unexpected frame in {run}: {member.name}')
                    expected.remove(member.name)
                    with archive.extractfile(member) as source, (folder / member.name).open('xb') as output:
                        shutil.copyfileobj(source, output)
            if expected:
                raise ValueError(f'Incomplete review frame sequence: {run}')
        staged.rename(destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt', type=Path, default=ROOT / 'docs/active/20261124-private-backup.json')
    parser.add_argument('--download-root', type=Path, help='Existing snapshot with the relative paths in the receipt')
    parser.add_argument('--destination', type=Path, default=ROOT / 'output/segment-review')
    parser.add_argument('--frames-destination', type=Path, help='Also restore source JPEGs for cumulative GIFs')
    args = parser.parse_args()
    receipt = json.loads(args.receipt.read_text())
    dest = args.destination.absolute()
    frames_dest = args.frames_destination.absolute() if args.frames_destination else None
    for path in (dest, frames_dest):
        if path is not None and (path.exists() or path.is_symlink()):
            parser.error(f'The destination already exists: {path}')
    if frames_dest:
        gallery_path, frames_path = dest.resolve(), frames_dest.resolve()
        if gallery_path.is_relative_to(frames_path) or frames_path.is_relative_to(gallery_path):
            parser.error('Gallery and frame destinations must be separate directories')
    os.umask(0o077)

    with tempfile.TemporaryDirectory() as tmp:
        download = args.download_root or Path(tmp)
        if not args.download_root:
            items = [receipt['journal'], *(r['review_zip'] for r in receipt['runs'])]
            if frames_dest:
                items.extend(r['review_frames'] for r in receipt['runs'])
            subprocess.run(['hf', 'download', receipt['repo_id'], *(item['path'] for item in items),
                            '--repo-type', receipt['repo_type'], '--revision', receipt['revision'],
                            '--local-dir', tmp], check=True)
        if frames_dest:
            dest.parent.mkdir(parents=True, exist_ok=True)
            frames_dest.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(dir=dest.parent) as gallery_tmp, \
                    tempfile.TemporaryDirectory(dir=frames_dest.parent) as frames_tmp:
                staged_gallery = Path(gallery_tmp) / 'gallery'
                staged_frames = Path(frames_tmp) / 'frames'
                count = restore(receipt, download, staged_gallery)
                restore_frames(receipt, download, staged_frames)
                if any(path.exists() or path.is_symlink() for path in (dest, frames_dest)):
                    raise FileExistsError('A restore destination appeared while validating the backup')
                staged_frames.rename(frames_dest)
                staged_gallery.rename(dest)
        else:
            count = restore(receipt, download, dest)
    print(f'Restored {count} verified clips and the journal to {dest}')


if __name__ == '__main__':
    main()
