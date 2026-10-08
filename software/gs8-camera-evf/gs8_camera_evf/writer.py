# SPDX-License-Identifier: MIT
"""Bounded single-owner disk worker. Submission never waits for disk or queue space."""
from concurrent.futures import Future, ThreadPoolExecutor, wait
from copy import deepcopy
from dataclasses import replace
from threading import BoundedSemaphore

from .models import Frame
from .storage import StorageError


def finalize(transaction, artifacts, summary, failure, cancelled):
    """Runs after every accepted message, including any failed write."""
    try:
        if failure is None and transaction._failure is None and not cancelled:
            try:
                for artifact in artifacts:
                    entry = transaction.add_artifact(artifact.filename, artifact.payload, artifact.kind)
                    if artifact.kind in ('audio', 'simulated_audio'):
                        transaction.manifest['audio'] = {
                            **artifact.audio_info.to_dict(),
                            **{key: value for key, value in entry.items() if key != 'kind'},
                        }
            except Exception as error:
                failure = f'{type(error).__name__}: {error}'
        return transaction.finish(failure=failure, summary=summary, cancelled=cancelled)
    except Exception:
        transaction.abandon()
        raise


class InlineClipWriter:
    """Deterministic test adapter; production Controller uses AsyncClipWriter."""
    def __init__(self, transaction):
        self.transaction = transaction
        transaction._writer = self
        self.pending = []

    def _submit(self, function, *args):
        future = Future()
        try:
            future.set_result(function(*args))
        except Exception as error:
            future.set_exception(error)
        return future

    def submit(self, message):
        future = self._submit(self.transaction.accept_message, message)
        self.pending.append(future)

    def poll_error(self):
        completed = [future for future in self.pending if future.done()]
        self.pending = [future for future in self.pending if not future.done()]
        return next((future.exception() for future in completed if future.exception() is not None), None)

    def finish(self, artifacts, summary, failure, cancelled):
        return self._submit(finalize, self.transaction, artifacts, summary, failure, cancelled)

    def wait_idle(self, timeout=10):
        if self.pending:
            _, incomplete = wait(self.pending, timeout=timeout)
            if incomplete:
                raise TimeoutError('writer did not become idle')

    def close(self, wait=False):
        pass


class AsyncClipWriter(InlineClipWriter):
    """At most capacity in-flight messages; overload fails the take explicitly.

    Mutable byte buffers/metadata are copied at submission. Large frames should
    use FilePayload, whose producer promises immutability through close().
    Only this worker accesses its ClipTransaction after construction.
    """
    def __init__(self, transaction, capacity=32):
        if type(capacity) is not int or capacity <= 0:
            raise ValueError('writer capacity must be positive')
        super().__init__(transaction)
        self._slots = BoundedSemaphore(capacity)
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='gs8-storage')

    def _submit(self, function, *args):
        return self._executor.submit(function, *args)

    def submit(self, message):
        if not self._slots.acquire(blocking=False):
            raise StorageError('bounded writer queue is full; capture cannot continue losslessly')
        try:
            if isinstance(message, Frame):
                payload = bytes(message.payload) if isinstance(message.payload, (bytearray, memoryview)) else message.payload
                message = replace(message, payload=payload, applied_metadata=deepcopy(message.applied_metadata))
            future = self._submit(self.transaction.accept_message, message)
            future.add_done_callback(lambda _: self._slots.release())
            self.pending.append(future)
        except Exception:
            self._slots.release()
            raise

    def close(self, wait=False):
        self._executor.shutdown(wait=wait)
