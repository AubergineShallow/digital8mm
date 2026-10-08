# SPDX-License-Identifier: MIT
"""D2 bench qualification is separate from live operating observations.

A hash-verified report is traceable evidence, not proof that a bench test was
truthful or performed correctly. The X1203 gauge cannot measure Pi input watts,
rail transients, connector temperature or storage throughput. Do not fake those
as runtime telemetry; qualify them once on the actual build at G-W10..G-W12.
"""
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import hashlib
import json
import math


@dataclass(frozen=True)
class D2Commissioning:
    evidence_id: str
    # Set only by load_commissioning after reviewing its report/measurement schema.
    artifacts_verified: bool
    limits_passed: bool
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class D2HealthSample:
    acquired_ns: int
    soc_temperature_c: float | None = None
    throttled_bits: int | None = None
    usb_resets: int | None = None
    media_writable: bool | None = None
    free_bytes: int | None = None


@dataclass(frozen=True)
class D2Readiness:
    ready: bool
    state: str
    reasons: tuple[str, ...]
    evidence_source: str | None


def _number(value):
    return type(value) in (int, float) and math.isfinite(value)


def bench_limit_failures(measurements):
    """Necessary numerical bounds from WIRING G-W10/G-W11/G-W12, unchanged.

    These are selected necessary limits, not the whole acceptance procedure.
    Each gate's report must also record the required workload/range/repetition,
    startup, frame-count and shutdown tests before its reviewed status is pass.
    """
    checks = (
        ('power_100ms_w', lambda v: _number(v) and 0 < v <= 22.9),
        ('header_min_mv', lambda v: type(v) is int and v >= 4850),
        ('header_mean_mv', lambda v: type(v) is int and v >= 4950),
        ('soc_temperature_c', lambda v: _number(v) and -40 <= v < 80),
        ('boost_temperature_c', lambda v: _number(v) and -40 <= v <= 70),
        ('xt30_temperature_c', lambda v: _number(v) and -40 <= v <= 60),
        ('pad_temperature_c', lambda v: _number(v) and -40 <= v <= 60),
        ('sustained_write_mb_s', lambda v: _number(v) and v >= 100),
    )
    if not isinstance(measurements, dict):
        return ('bench_measurements_missing',)
    failures = tuple(f'bench_{name}_missing_or_outside_limit' for name, check in checks
                     if not check(measurements.get(name)))
    low, mean = measurements.get('header_min_mv'), measurements.get('header_mean_mv')
    if type(low) is int and type(mean) is int and low > mean:
        failures += ('bench_header_min_exceeds_mean',)
    return failures


def load_commissioning(path):
    """Load an operator-reviewed manifest with content-hashed local gate reports.

    Required JSON fields: schema_version=1, evidence_type='measured_hardware',
    build_id, reviewed_by, recorded_at (timezone-qualified ISO 8601), gates with
    G-W10/G-W11/G-W12 entries {status:'pass', report:'relative-file', sha256},
    measurements (bench_limit_failures keys). Reports must remain beside/below
    the manifest, be regular non-symlink files and match their SHA-256 digests.
    Never substitute the host-test/demo output for measured-hardware reports.
    """
    path = Path(path).resolve(strict=True)
    if path.stat().st_size > 64 * 1024:
        raise ValueError('commissioning manifest is too large')
    value = json.loads(path.read_text(encoding='utf-8'))
    if (not isinstance(value, dict) or type(value.get('schema_version')) is not int
            or value['schema_version'] != 1 or value.get('evidence_type') != 'measured_hardware'
            or any(not isinstance(value.get(k), str) or not value[k].strip()
                   for k in ('build_id', 'reviewed_by', 'recorded_at'))):
        raise ValueError('commissioning manifest requires reviewed measured-hardware evidence')
    try:
        recorded = datetime.fromisoformat(value['recorded_at'].replace('Z', '+00:00'))
    except ValueError as error:
        raise ValueError('commissioning recorded_at must be ISO 8601') from error
    if recorded.tzinfo is None:
        raise ValueError('commissioning recorded_at must include timezone')
    gates = value.get('gates')
    if not isinstance(gates, dict):
        raise ValueError('commissioning gate reports are missing')
    for gate in ('G-W10', 'G-W11', 'G-W12'):
        entry = gates.get(gate)
        if (not isinstance(entry, dict) or entry.get('status') != 'pass'
                or not isinstance(entry.get('report'), str) or not entry['report']
                or not isinstance(entry.get('sha256'), str) or len(entry['sha256']) != 64):
            raise ValueError(f'{gate} requires a reviewed pass report and SHA-256')
        relative = Path(entry['report'])
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError(f'{gate} report must be relative to the commissioning manifest')
        report = path.parent / relative
        if report.is_symlink() or not report.resolve(strict=True).is_relative_to(path.parent) or not report.is_file():
            raise ValueError(f'{gate} report must be a local regular file')
        digest = hashlib.sha256()
        with report.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1 << 20), b''):
                digest.update(chunk)
        if digest.hexdigest() != entry['sha256'].lower():
            raise ValueError(f'{gate} report hash does not match')
    reasons = bench_limit_failures(value.get('measurements'))
    return D2Commissioning(value['build_id'], True, not reasons, reasons)


def evaluate_readiness(now_ns, sample, *, reserve_bytes, commissioning=None):
    """Require verified bench evidence plus fresh runtime-observable health.

    Runtime observations are SoC heat/throttle flags, detected USB resets and
    mounted writable media/free space. Missing live telemetry inhibits new
    takes; the runtime drains an active take and stays unready, not force-off.
    """
    if type(now_ns) is not int or now_ns < 0 or type(reserve_bytes) is not int or reserve_bytes < 0:
        raise ValueError('readiness requires a valid clock and storage reserve')
    reasons = ()
    source = commissioning.evidence_id if isinstance(commissioning, D2Commissioning) else None
    if not isinstance(commissioning, D2Commissioning) or commissioning.artifacts_verified is not True:
        reasons += ('commissioning_evidence_missing_or_unverified',)
    elif commissioning.limits_passed is not True:
        reasons += commissioning.reasons or ('commissioning_limits_failed',)
    if sample is None:
        reasons += ('runtime_health_missing',)
    elif (not isinstance(sample, D2HealthSample) or type(sample.acquired_ns) is not int
            or sample.acquired_ns < 0 or sample.acquired_ns > now_ns
            or now_ns - sample.acquired_ns > 1_000_000_000):
        reasons += ('runtime_health_invalid_or_stale',)
    else:
        checks = (
            ('soc_temperature_c', lambda v: _number(v) and -40 <= v < 80),
            ('throttled_bits', lambda v: type(v) is int and v == 0),
            ('usb_resets', lambda v: type(v) is int and v == 0),
            ('media_writable', lambda v: v is True),
            ('free_bytes', lambda v: type(v) is int and v > reserve_bytes),
        )
        reasons += tuple(f'{name}_missing' if getattr(sample, name) is None else f'{name}_outside_limit'
                         for name, check in checks if not check(getattr(sample, name)))
    return D2Readiness(not reasons, 'reported_limits_pass' if not reasons else
                      'degraded' if any('outside_limit' in r or 'failed' in r for r in reasons) else 'unready',
                      reasons, source)
