# GS8 EVF fork capture and writer contract

EVF extension, 2026-09-20: the copied host contract below remains the storage
boundary. `PicameraEvfBackend` additionally implements `check_health()` for idle
live preview and `release_take()` after successful durable commit. The fork
controller uses `release_take()` only without a fault or shutdown request;
`close()` remains mandatory on fault/shutdown. A retained idle preview does not
grant permission to power off. Changing settings requires a new backend session.

Hardware commissioning exception to the inherited prompt-return boundary:
`preflight()` opens/configures Picamera2 and starts DRM synchronously, and final
`close()` calls the camera/preview stop APIs and joins workers (ten-second join
timeout per worker). These run outside recording's callback/poll path. Their
wall-clock duration is not qualified on a Pi; a production GPIO service should
move initialisation/final teardown off its input-sampling thread. All ongoing
capture callbacks, polling, stop gating and normal take release avoid storage
waits. A timed-out or failed final close keeps ownership and cannot enable poweroff.

In this adapter `Frame.index` and contract-2 `source_frame_count` refer to selected
**recording samples**. `applied_metadata.sensor_frame_sequence` is the actual raw
libcamera buffer sequence; `sensor_source_index` counts every preview exposure
within that take. Summary `sensor_frames_observed` and
`sensor_frames_intentionally_not_recorded` preserve intentional sampling evidence.
Sensor gaps, regression, queue overflow or unachieved requested cadence fail the
take. Nominal `record_pts_ns` never replaces actual sensor timestamps.

The following inherited text describes the original host boundary; its claim
that no IMX296 adapter exists applies only to the original package. This fork's
hardware adapter exists but is not physically commissioned. See README.md.

Contract version 2 extends schema-1 manifests. This is an implemented host
boundary with simulation and fault injection, not an IMX296 hardware adapter.

## Ownership and lifecycle

One controller thread calls backend methods serially. Each method must return
promptly: sensor callbacks, encoding and audio acquisition belong to backend
workers with synchronized message queues. `poll()` returns a finite list and
never waits for capture or disk. `preflight(settings)` returns negotiated
sensor metadata and must unwind resources itself if it raises. After successful
preflight, any subsequent failure, including storage creation, triggers
`request_stop()`, continued polling, an explicit `drained()` acknowledgement,
and `close()`. Stop and close are idempotent.

`preflight` reports `model`, `mode`, positive `width`, `height`, `bit_depth`,
`crop: [x, y, width, height]` in source pixels, and a named `timestamp_clock`.
Do not fill this from requested settings if the device negotiated a different
mode. Simulation explicitly names its descriptor mode and simulated clock.

`Frame.index` is the sensor's take-relative sequence, starting at zero, and
`sensor_timestamp_ns` uses the declared sensor clock. A frame carries immutable
`bytes`, a mutable bytes-like buffer (snapshotted on queue submission), or
`FilePayload(Path(...))`. Handoff files must be closed regular files, immutable
and available until backend `close()`; the disk worker copies and hashes them
in 1 MiB chunks. The backend owns eventual staging cleanup. This supports a DNG
writer that already produces files without loading the whole file in Python.
Same-size concurrent source-file modification is outside that ownership contract.

Real frames require `applied_metadata` with positive finite `exposure_us`,
`analogue_gain` and `colour_gains: [red, blue]`. These are the actual per-frame
values returned by the device, not a claim that requested controls were applied.
Additional JSON metadata can carry mode-specific measurements.

`DroppedFrames(first_sequence, count, reason)` records loss in source order,
including tail loss after the last image. A jump in `Frame.index` automatically
records `unreported_source_sequence_gap`. Duplicate/regressing sequences or
timestamps fail the transaction. Storage uses its own contiguous `index` and
preserves the source identity as `source_sequence`; source loss is never hidden
by renumbering. Consumers must decide explicitly whether dropped footage is usable.

`request_stop(now_ns)` records a stop request, not completion. `drained(now_ns)`
returns `True` only after producers have stopped and all frame/drop messages
have been delivered. `artifacts()` then returns closed audio or other files
(`Artifact` supports bytes or `FilePayload`); enabled audio needs exactly one
audio artifact with `AudioInfo` in the same timestamp clock.

`final_summary()` returns independent producer counters:

```json
{"expected_frame_count": 48, "source_frame_count": 48,
 "stop_requested_ns": 2070000001, "evidence": "backend_counters"}
```

`expected_frame_count` counts image messages the backend intended to deliver;
`source_frame_count` counts images plus all reported/inferred source drops.
Both must agree with persisted image/drop evidence or the take fails. Do not
derive these producer counters from the storage journal: that would hide a
lost final queue entry. The controller rejects absent summaries, missing or
weaker evidence labels, negative/non-integer counters and stop timestamps outside
the controller's first-stop-request to final-drain interval
before submitting finalization. This requirement also applies to a zero-frame
operator cancellation: valid zero counts permit cancellation, missing evidence
fails the take. The lower-level `ClipTransaction.finish()` API can create
`writer_observed_only` evidence for standalone storage tests. That weaker label
does not establish that a sensor's final frame arrived.

After backend drain, artifact and manifest work enters the disk queue. The
controller stays STOPPING/FAULT, continues sampling inputs, and rejects a new
take until the writer completes. Only then is backend `close()` called. A close
failure prevents poweroff readiness and is retried on later ticks. An idle
shutdown also closes the backend. `safe_to_request_poweroff` permits the eventual
OS shutdown request only; it never permits asserting the kernel HALTED signal.

## Queue and persistence

`AsyncClipWriter` owns a transaction exclusively after startup and processes
messages in order on one disk worker. Its bounded semaphore rejects the 33rd
in-flight message by default without waiting. This faults/stops capture and
retains failed-take evidence. Buffers can consume up to the configured count
times their size; a hardware adapter must size its own queues, frame buffers,
storage reserve and backlog against measured throughput. The host does not
claim a latency or throughput bound. `InlineClipWriter` is an explicit test
adapter for deterministic lifecycle tests, never the controller default.

Each new RAW/artifact file is flushed, fsynced, then its directory is fsynced on
POSIX before its journal entry is accepted. The journal is flushed/fsynced after
each entry. Encoded simulation flushes descriptor bytes before journal entries;
entries contain the exact byte offset/length/hash, while the artifact records
the complete container hash. Real encoded capture remains unimplemented.

`frames.jsonl` contains the same frame entries as `frames[]`, interspersed with
`{"dropped_frames": {"first_sequence": 7, "count": 1, "reason": "..."}}`.
The complete manifest contains `dropped_frames[]` and `capture_summary`.

After final file flushes, an atomic `manifest.json` replacement is followed by
the POSIX directory flush. Then `commit.json` records
`{"manifest_sha256": "<SHA-256 of exact manifest.json bytes>"}` and is flushed.
A contract-2 complete/cancelled manifest without a matching receipt is uncertain
and included in read-only inventory. Receipt errors attempt to remove the
receipt. A filesystem that also rejects that cleanup can leave ambiguous
evidence; file contents never prove drive firmware obeyed a flush. Windows
directory durability and real power-loss recovery still need platform evidence.

An ordinary zero-frame release closes as `cancelled` if no source frames were
reported; it is not a recording fault. All-dropped captures still fail. Real
storage/capture failures remain latched until explicit service recovery with
released trigger, quiescent backend and verified commit. Closing a `ClipStore`
context abandons an open transaction and releases the lock without masking an
original exception. Exceptional context teardown joins any live writer before
closing its files; unlike a sampling tick, this cleanup can wait on disk I/O.
The CLI and controller-owned normal shutdown drain the writer first.

## Host regression evidence

Run `python -m unittest discover -s tests -v` from this directory with the package
on `PYTHONPATH`. `test_audit_regressions.py` blocks disk work behind an event,
checks trigger processing and withheld poweroff permission, injects bounded
queue overflow, final-frame loss, manifest/receipt directory flush failures,
and verifies closed-file handoff, metadata, readonly inspection, cancellation,
custom WB inhibition and exception cleanup. These checks do not exercise Linux
flock/directory-fsync system calls on Windows or qualify actual camera hardware.
