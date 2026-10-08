# SPDX-License-Identifier: MIT
"""Exclusive storage ownership and inspectable clip transactions.

Directory fsync is used on POSIX. Windows flushes files but cannot provide the
same directory-durability guarantee through this stdlib implementation.
"""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from copy import deepcopy
from functools import wraps
import hashlib
import json
import math
import os
import re
import shutil
import stat
import uuid

from .models import DroppedFrames, FilePayload, Frame


class StorageError(RuntimeError):
    pass


def poisons_transaction(method):
    """Any rejected write poisons this take, even if a caller catches the error."""
    @wraps(method)
    def guarded(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except Exception as error:
            if self._failure is None:
                self._failure = f'{method.__name__}: {type(error).__name__}: {error}'
            raise
    return guarded


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def sync_directory(path: Path):
    if os.name == 'posix':
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def atomic_json(path: Path, data: dict):
    tmp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with tmp.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(data, stream, indent=2, allow_nan=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
        sync_directory(path.parent)
    finally:
        if tmp.exists():
            tmp.unlink()


def incomplete_clips(root):
    """Read-only snapshot; safe while a recorder holds the ownership lock.

    Concurrent recording/commit can appear incomplete until the next snapshot.
    A contract-2 complete manifest needs a matching post-commit receipt.
    """
    result = []
    for folder in sorted(Path(root).iterdir()):
        if not folder.is_dir() or folder.is_symlink():
            continue
        try:
            raw = (folder / 'manifest.json').read_bytes()
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise ValueError('manifest must be an object')
            status = value.get('status', 'unknown')
            if status in ('complete', 'cancelled') and value.get('writer_contract_version') == 2:
                try:
                    receipt = json.loads((folder / 'commit.json').read_bytes())
                    if receipt.get('manifest_sha256') != hashlib.sha256(raw).hexdigest():
                        status = 'uncertain_commit'
                except (OSError, ValueError, AttributeError):
                    status = 'uncertain_commit'
            if status not in ('complete', 'cancelled'):
                result.append({'clip_id': folder.name, 'status': status})
        except (OSError, ValueError):
            result.append({'clip_id': folder.name, 'status': 'missing_or_invalid_manifest'})
    return result


class ClipStore:
    """The OS releases the advisory lock even if the process crashes.

    The lock file is retained, avoiding unlink/recreate races. Storage must be a
    trusted, dedicated local filesystem; symlink-race hardening and network FS
    semantics are not part of this implementation.
    """
    def __init__(self, root: Path, reserve_bytes: int = 256 * 1024 * 1024):
        if type(reserve_bytes) is not int or reserve_bytes < 0:
            raise ValueError('reserve_bytes must be a nonnegative integer')
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.reserve_bytes = reserve_bytes
        self._lock = (self.root / '.gs8-owner.lock').open('a+b')
        try:
            if os.name == 'nt':
                import msvcrt
                self._lock.seek(0)
                msvcrt.locking(self._lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self._lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            self._lock.close()
            raise StorageError('storage is already owned by another recorder') from error
        self.closed = False
        self.active: ClipTransaction | None = None

    def free_bytes(self):
        return shutil.disk_usage(self.root).free

    def require_space(self, additional=0):
        if self.closed:
            raise StorageError('storage is closed')
        if self.free_bytes() < self.reserve_bytes + additional:
            raise StorageError('storage reserve reached; no new capture data accepted')

    def begin(self, settings: dict, simulated: bool, sensor: dict | None = None):
        if self.active is not None:
            raise StorageError('previous clip has not closed')
        if not isinstance(settings, dict) or settings.get('capture_format') not in ('raw', 'encoded'):
            raise StorageError('capture_format must be raw or encoded')
        if type(simulated) is not bool:
            raise StorageError('simulated must be explicitly boolean')
        if settings['capture_format'] == 'encoded' and not simulated:
            raise StorageError('a commissioned encoded writer is not installed')
        self.require_space()
        clip_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex[:12]
        path = self.root / clip_id
        path.mkdir()
        sync_directory(self.root)
        transaction = ClipTransaction(self, path, clip_id, settings, simulated, sensor)
        self.active = transaction
        return transaction

    def incomplete_clips(self):
        return incomplete_clips(self.root)

    def close(self):
        if not self.closed:
            if self.active is not None:
                raise StorageError('cannot close storage with an open clip')
            self._lock.close()
            self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        try:
            if self.active is not None:
                writer = getattr(self.active, '_writer', None)
                if writer is not None:
                    # Exceptional teardown may wait; the sampling step never
                    # does. Do not close handles while a worker is using them.
                    writer.close(wait=True)
                if self.active is not None:
                    self.active.abandon()
        except Exception:
            if exc_type is None:
                raise
        finally:
            self._lock.close()
            self.closed = True


class ClipTransaction:
    def __init__(self, store, path, clip_id, settings, simulated, sensor=None):
        self.store, self.path = store, path
        self.closed = False
        self._failure = None
        self._journal = None
        self.manifest = {
            'schema_version': 1, 'writer_contract_version': 2, 'clip_id': clip_id, 'status': 'recording',
            'created_utc': utc_now(), 'closed_utc': None, 'simulated': bool(simulated),
            'sensor': deepcopy(sensor) if sensor is not None else {'model': 'unspecified'},
            'settings': deepcopy(settings), 'frames': [], 'artifacts': [], 'failure': None,
            'dropped_frames': [], 'capture_summary': None,
            'durability': 'file_and_directory_fsync_requested' if os.name == 'posix' else 'file_fsync_requested_directory_flush_unavailable',
        }
        self._encoded = None
        self._encoded_hash = hashlib.sha256()
        self._encoded_size = 0
        self._encoded_finalized = False
        self._source_next = 0
        try:
            atomic_json(path / 'manifest.json', self.manifest)
            self._journal = (path / 'frames.jsonl').open('x', encoding='utf-8', newline='\n')
            self._journal.flush()
            os.fsync(self._journal.fileno())
            if settings['capture_format'] == 'encoded':
                self._encoded = (path / 'take.simclip.jsonl').open('xb')
                self._encoded.flush()
                os.fsync(self._encoded.fileno())
            sync_directory(path)
        except Exception:
            self.abandon()
            raise

    @poisons_transaction
    def add_frame(self, index: int, timestamp_ns: int, payload, *, source_sequence=None, applied_metadata=None):
        if self.closed:
            raise StorageError('clip already closed')
        if self._failure:
            raise StorageError('clip has failed; further writes are inhibited')
        frames = self.manifest['frames']
        if type(index) is not int or index != len(frames):
            raise StorageError('frame sequence discontinuity')
        if type(timestamp_ns) is not int or timestamp_ns < 0 or (frames and timestamp_ns <= frames[-1]['sensor_timestamp_ns']):
            raise StorageError('sensor timestamps must increase strictly')
        if applied_metadata is not None:
            if not isinstance(applied_metadata, dict):
                raise StorageError('applied metadata must be an object')
            applied_metadata = json.loads(json.dumps(applied_metadata, allow_nan=False))
        source_sequence = index if source_sequence is None else source_sequence
        if type(source_sequence) is not int or source_sequence != self._source_next:
            raise StorageError('invalid source sequence')
        if self._encoded is None:
            extension = '.simframe' if self.manifest['simulated'] else '.dng'
            filename = f'{index:08d}' + extension
            size, digest = self._write_payload(filename, payload)
            entry = {'index': index, 'filename': filename, 'sensor_timestamp_ns': timestamp_ns,
                     'size_bytes': size, 'sha256': digest}
        else:
            if not isinstance(payload, (bytes, bytearray, memoryview)) or not payload:
                raise StorageError('encoded descriptors require nonempty bytes-like payload')
            payload_size = payload.nbytes if isinstance(payload, memoryview) else len(payload)
            self.store.require_space(payload_size)
            offset = self._encoded_size
            self._encoded.write(payload)
            self._encoded.flush()
            os.fsync(self._encoded.fileno())
            self._encoded_hash.update(payload)
            self._encoded_size += payload_size
            entry = {'index': index, 'filename': 'take.simclip.jsonl', 'sensor_timestamp_ns': timestamp_ns,
                     'byte_offset': offset, 'size_bytes': payload_size,
                     'sha256': hashlib.sha256(payload).hexdigest(), 'evidence_scope': 'container_byte_range'}
        entry['source_sequence'] = source_sequence
        if applied_metadata is not None:
            entry['applied_metadata'] = applied_metadata
        self._journal.write(json.dumps(entry, allow_nan=False) + '\n')
        self._journal.flush()
        os.fsync(self._journal.fileno())
        frames.append(entry)
        self._source_next = entry['source_sequence'] + 1

    def _write_payload(self, filename, payload):
        source = None
        if isinstance(payload, FilePayload):
            source_path = Path(payload.path)
            if source_path.is_symlink() or not stat.S_ISREG(source_path.stat().st_mode):
                raise StorageError('handoff must be a closed regular file')
            size = source_path.stat().st_size
            source = source_path.open('rb')
        elif isinstance(payload, (bytes, bytearray, memoryview)):
            size = payload.nbytes if isinstance(payload, memoryview) else len(payload)
        else:
            raise StorageError('empty or invalid frame payload')
        try:
            if size <= 0:
                raise StorageError('empty or invalid frame payload')
            self.store.require_space(size)
            digest = hashlib.sha256()
            written = 0
            with (self.path / filename).open('xb') as stream:
                if source is None:
                    stream.write(payload)
                    digest.update(payload)
                    written = size
                else:
                    while chunk := source.read(1024 * 1024):
                        stream.write(chunk)
                        digest.update(chunk)
                        written += len(chunk)
                    if written != size:
                        raise StorageError('handoff file changed during transfer')
                stream.flush()
                os.fsync(stream.fileno())
            sync_directory(self.path)
            return written, digest.hexdigest()
        finally:
            if source is not None:
                source.close()

    @poisons_transaction
    def accept_message(self, message):
        """Convert source sequence evidence into contiguous storage indices."""
        if isinstance(message, DroppedFrames):
            if (self.closed or self._failure or type(message.first_sequence) is not int
                    or message.first_sequence != self._source_next or type(message.count) is not int
                    or message.count <= 0 or not isinstance(message.reason, str) or not message.reason):
                raise StorageError('invalid or out-of-order dropped-frame report')
            entry = {'first_sequence': message.first_sequence, 'count': message.count, 'reason': message.reason}
            self.manifest['dropped_frames'].append(entry)
            self._source_next += message.count
            self._journal.write(json.dumps({'dropped_frames': entry}) + '\n')
            self._journal.flush()
            os.fsync(self._journal.fileno())
            return
        if not isinstance(message, Frame) or type(message.index) is not int or message.index < self._source_next:
            raise StorageError('source frame sequence repeated or regressed')
        if message.index > self._source_next:
            self.accept_message(DroppedFrames(self._source_next, message.index - self._source_next,
                                              'unreported_source_sequence_gap'))
        if not self.manifest['simulated']:
            metadata = message.applied_metadata
            if (not isinstance(metadata, dict)
                    or not all(key in metadata for key in ('exposure_us', 'analogue_gain', 'colour_gains'))):
                raise StorageError('real frames require applied exposure/gain/colour-gain metadata')
            gains = metadata['colour_gains']
            values = [metadata['exposure_us'], metadata['analogue_gain']]
            if not isinstance(gains, (list, tuple)) or len(gains) != 2:
                raise StorageError('applied colour gains must contain red and blue gains')
            if any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in values + list(gains)):
                raise StorageError('applied metadata values must be positive finite numbers')
        self.add_frame(len(self.manifest['frames']), message.sensor_timestamp_ns, message.payload,
                       source_sequence=message.index, applied_metadata=message.applied_metadata)

    @poisons_transaction
    def add_artifact(self, filename, payload, kind):
        if (self.closed or self._failure or not isinstance(filename, str)
                or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', filename)
                or filename.endswith('.')
                or filename.lower() in ('manifest.json', 'frames.jsonl', 'take.simclip.jsonl', 'commit.json')
                or re.fullmatch(r'\d+\.(dng|simframe)', filename, re.IGNORECASE)
                or filename.casefold() in {item['filename'].casefold() for item in self.manifest['artifacts']}
                or filename.split('.')[0].upper() in ('CON', 'PRN', 'AUX', 'NUL',
                    *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10)))):
            raise StorageError('invalid artifact filename or closed clip')
        if not isinstance(kind, str) or not kind:
            raise StorageError('artifact must have nonempty bytes and kind')
        size, digest = self._write_payload(filename, payload)
        entry = {'filename': filename, 'kind': kind,
                 'size_bytes': size, 'sha256': digest}
        self.manifest['artifacts'].append(entry)
        return dict(entry)

    @poisons_transaction
    def finish(self, failure: str | None = None, *, summary=None, cancelled=False):
        if self.closed:
            raise StorageError('clip already closed')
        if failure is not None and (not isinstance(failure, str) or not failure):
            raise StorageError('failure must be a nonempty string or None')
        failure = self._failure or failure
        if self._encoded is not None and not self._encoded_finalized:
            self._encoded.flush()
            os.fsync(self._encoded.fileno())
            self._encoded.close()
            self.manifest['artifacts'].append({'filename': 'take.simclip.jsonl', 'kind': 'simulated_encoded',
                'size_bytes': self._encoded_size, 'sha256': self._encoded_hash.hexdigest()})
            self._encoded_finalized = True
        self._journal.close()
        if summary is None:
            summary = {'expected_frame_count': len(self.manifest['frames']),
                       'source_frame_count': self._source_next, 'stop_requested_ns': None,
                       'evidence': 'writer_observed_only'}
        if (not isinstance(summary, dict)
                or type(summary.get('expected_frame_count')) is not int
                or type(summary.get('source_frame_count')) is not int
                or summary['expected_frame_count'] != len(self.manifest['frames'])
                or summary['source_frame_count'] != self._source_next):
            failure = failure or 'capture final counters disagree with accepted frames/drop reports'
        elif summary.get('evidence') == 'backend_counters' and (
                type(summary.get('stop_requested_ns')) is not int or summary['stop_requested_ns'] < 0):
            failure = failure or 'capture stop timestamp is invalid'
        self.manifest['capture_summary'] = deepcopy(summary)
        cancelled = cancelled and self._source_next == 0
        if not self.manifest['frames'] and failure is None and not cancelled:
            failure = 'no frames accepted'
        cancelled = cancelled and not self.manifest['frames'] and failure is None
        committed = {**self.manifest, 'status': 'failed' if failure else 'cancelled' if cancelled else 'complete',
                     'failure': failure, 'closed_utc': utc_now()}
        # Completion is published only after all frame/container bytes are flushed.
        atomic_json(self.path / 'manifest.json', committed)
        receipt = self.path / 'commit.json'
        try:
            atomic_json(receipt, {'manifest_sha256': hashlib.sha256((self.path / 'manifest.json').read_bytes()).hexdigest()})
        except Exception:
            # Do not leave apparently verified completion after receipt failure.
            receipt.unlink(missing_ok=True)
            raise
        self.manifest = committed
        self.closed = True
        self.store.active = None
        return self.path

    def abandon(self):
        """Release local handles after an I/O failure; leave on-disk state incomplete."""
        errors = []
        for stream in (self._encoded, self._journal):
            if stream is not None and not stream.closed:
                try:
                    stream.close()
                except OSError as error:
                    errors.append(error)
        self.closed = True
        if self.store.active is self:
            self.store.active = None
        if errors:
            raise StorageError('error closing abandoned clip handles') from errors[0]
