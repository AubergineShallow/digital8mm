# Camera audit response — 20 September 2026

> **Note, 25 September 2026:** this file is an unchanged copy of `software/gs8-camera/AUDIT-RESPONSE.md` made when the EVF fork was created. Its Validation paragraph describes the OVF package. The EVF suite is `software/gs8-camera-evf/tests` (131 tests pass on 25 September 2026; see [README.md](README.md#host-verification)).

The host foundation addresses S-1 through S-11. Real Pi capture/GPIO/audio,
Linux-specific flush/lock behavior, power-loss durability and recording
throughput remain unqualified. No sensor adapter or hardware result is claimed.

| Finding | Change and evidence |
|---|---|
| S-1 | Default bounded asynchronous disk worker; bytes-like and streaming closed-file handoff; negotiated backend sensor mode/crop/clock metadata; applied frame metadata; explicit/inferred source drops, producer final counts and close lifecycle. Blocked-writer, queue-overflow, file-handoff and tail-loss regressions. Independent review reproduced a missing-summary bypass; the controller now rejects missing/weakened producer-counter evidence, invalid counters and stop timestamps outside its stop/drain interval, including for zero-frame cancellations. Startup directory creation still runs on the controller thread; no real-time guarantee. |
| S-2 | Zero-frame operator cancellation commits `cancelled`; uncalibrated custom WB inhibits CHECK without FAULT. Both recover through ordinary release/dial actions. Actual recording faults retain explicit service recovery. |
| S-3 | Contract-2 completion requires matching post-manifest `commit.json`; failed directory flush after manifest replacement is inventoried as `uncertain_commit`. Manifest and receipt failure regressions. |
| S-4 | Standalone read-only inventory opens no lock and creates no files. CLI inspection during an exclusive recording owner leaves file bytes and lock metadata unchanged. |
| S-5 | Journal/container creation and each new RAW/artifact directory entry are flushed appropriately; encoded bytes flush before journal publication. Labels state fsync requested and the Windows directory limitation. No physical durability claim. |
| S-6 | Malformed selections inhibit the next take without starving current polling; constructor validates/copies WB gains. Active malformed-selection regression. |
| S-7 | A successful preflight engages cleanup before storage creation; begin/worker-construction failure still stops, drains and closes backend resources. |
| S-8 | Context teardown joins a live writer, abandons open transaction handles and always releases ownership while preserving the original exception. |
| S-9 | Numeric DNG/simframe names, commit metadata and case-aliased artifacts are reserved/rejected. |
| S-10 | Encoded entries contain offset/length/hash of the individual descriptor range; full-container evidence is in artifacts. README and integration assertion corrected. |
| S-11 | PEP 639 MIT expression/license files, Python >=3.10, standalone optional planner discovery via GS8_SEQUENCE_MODULE, portable commands, audio/reserve docs, concise CLI errors, SPDX headers and source-distribution manifest. |

Validation: `PYTHONPATH=software/gs8-camera py -3.14 -m unittest discover -s
software/gs8-camera/tests -q` passed **99 tests**; the same 99 passed on installed
Python 3.11 and 3.10. Split: 17 controls, 25 storage, 31 controller, 21 audit
regressions, 5 independent camera-to-planner integration tests. On Python 3.14
the two-rate integration case also reports its two subtests in verbose runners.
Tests use temporary storage and synthetic bytes/audio. A temporary standalone
package copy and an offline wheel build verify optional planner-test skipping,
`Requires-Python: >=3.10`, `License-Expression: MIT` and the wheel licence file.

See [BACKEND-CONTRACT.md](BACKEND-CONTRACT.md) for field shapes, queue ownership,
exceptional teardown and remaining filesystem/hardware limits.
