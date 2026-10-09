# SPDX-License-Identifier: MIT
"""Independently audit hash links and serialized CAD outputs, never physical readiness.

Example, from project root (use the pinned CAD interpreter):
  python cad/gs8-d2-v1/audit_cloud_release.py --out cad/gs8-d2-v1/out --require-step --json audit.json
Read-only apart from the explicitly named JSON report; no geometry build or display.
"""
import argparse
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path, PurePosixPath
import platform
import struct
import sys

import manifold3d as m3
import numpy as np


EXPECTED_CATEGORIES = {
    'contract', 'cots_containment', 'interference', 'mate_overlap', 'clearance', 'keepouts',
    'cable_routes', 'bed_fit', 'stl_mesh', 'print_modifiers', 'print_overhang', 'thin_wall', 'critical_features',
    'evf_restraint', 'driver', 'engrave_groove', 'boss_geometry', 'inserts', 'j7_float',
    'lens_support', 'lens_clamp', 'sweeps', 'removals', 'service_driver', 'release_access',
    'stack_retention', 'layout_self_check', 'mass_com',
}
EXPECTED_CATEGORIES.add('mate_paths')   # r7 C1 (SPEC-C1 4.2); each r7 cluster adds its own line
EXPECTED_CATEGORIES.update(('mate_reach', 'cable_stow', 'header_housings'))   # r7 C2 (SPEC-C2 3.3)
EXPECTED_CATEGORIES.add('handling')     # r7 C5 (SPEC-C5 3.2)
EXPECTED_CATEGORIES.add('lead_access')  # r7 C3 (SPEC-C3 3.2)
EXPECTED_CATEGORIES.add('roll_catch')   # r7 C4 (SPEC-C4 4.1)
# r6 (audit 2026-10-06 L9): report-only categories; their summary status is 'info', never 'pass'.
INFO_CATEGORIES = {'mass_com'}

# Fixed independently from the verified r5 input, not inferred from a supplied receipt.
EXPECTED_SOURCES = set(['FASTENER-POLICY.md', 'SPEC.md', 'build_d2.py', 'checks.py', 'cots.py', 'coupons_r1.py', 'd2_common.py', 'layout.py', 'make_coupons.py', 'make_tables.py', 'printed_collar.py', 'printed_grip.py', 'printed_hood.py', 'printed_keeper.py', 'printed_panel.py', 'printed_small.py', 'printed_tub.py'])
FONT_SOURCES = set(['run_locked.py', 'fonts/DejaVuSans-Bold.ttf', 'fonts/LICENSE-DejaVu.txt'])
EXPECTED_GATE_DOCS = set(['cad/gs8-d2-v1/MEASURED-PARTS.md', 'cad/gs8-d2-v1/SPEC.md', 'electronics/gs8-d2-v1/WIRING.md', 'electronics/gs8-evf-v1/EVF-SELECTION.md'])
EXPECTED_GATE_IDS = set(['EVF-G1', 'EVF-G2', 'EVF-G3', 'EVF-G4', 'EVF-G4b', 'EVF-G5', 'EVF-G6', 'EVF-G7', 'EVF-G8', 'EVF-G9', 'G-CAM-1', 'G-CAM-2', 'G-CAP-1', 'G-COL-1', 'G-COMB-1', 'G-ENC-1', 'G-EVF-1', 'G-EVF-2', 'G-FPC-1', 'G-HDMI', 'G-J4-1', 'G-KEEP-1', 'G-KEEP-1/whole', 'G-KNOB-1', 'G-LENS', 'G-MP-ENC', 'G-MP-EVF', 'G-MP-FPC', 'G-MP-PACK', 'G-MP-STICK', 'G-MP-SW', 'G-MP-X1203', 'G-PANEL-1', 'G-PANEL-1/whole', 'G-PI-1', 'G-PLG-1', 'G-PT-1', 'G-RUN-1', 'G-SKIRT-1', 'G-SNAP-1', 'G-SNAP-2', 'G-SNAP-2/whole', 'G-W1', 'G-W10', 'G-W11', 'G-W12', 'G-W13', 'G-W2', 'G-W3', 'G-W4', 'G-W5', 'G-W6', 'G-W7', 'G-W8', 'G-W9'])
EXPECTED_GATE_IDS.update(('G-EVF-3', 'G-QT-1', 'G-HDR-1'))   # r7 new gates: C1 G-EVF-3 (SPEC-C1), C2 G-QT-1 / G-HDR-1 (SPEC-C2); open, no record
EXPECTED_PARTS = set(['base_grip', 'cap', 'eyecup', 'hood', 'knob_exp', 'knob_fps', 'lens_collar', 'panel', 'pi_keeper', 'plunger', 'stick_sleeve', 'tub'])
EXPECTED_BASE_OUTPUTS = set(['checks.json', 'parts-manifest.json', 'print-manifest.json', 'renders/section-base-edge-x91.png', 'renders/section-evf-board-x137.png', 'renders/section-evf-board-z78.png', 'renders/section-j7-y0.png', 'renders/section-j7-z90.png', 'renders/section-pi-keeper-x80.png', 'renders/section-pi-keeper-y-20.png', 'renders/section-pi-keeper-y12.png', 'stl/base_grip.stl', 'stl/cap.stl', 'stl/eyecup.stl', 'stl/hood.stl', 'stl/knob_exp.stl', 'stl/knob_fps.stl', 'stl/lens_collar.stl', 'stl/modifiers/base_grip__mod_s_b1.stl', 'stl/modifiers/base_grip__mod_s_b2.stl', 'stl/modifiers/base_grip__mod_s_j.stl', 'stl/modifiers/base_grip__mod_tripod_nut.stl', 'stl/modifiers/panel__mod_s_b1.stl', 'stl/modifiers/panel__mod_s_b2.stl', 'stl/modifiers/panel__mod_s_r1.stl', 'stl/modifiers/panel__mod_s_r2.stl', 'stl/modifiers/tub__mod_s_b1.stl', 'stl/modifiers/tub__mod_s_b2.stl', 'stl/modifiers/tub__mod_s_c1.stl', 'stl/modifiers/tub__mod_s_c2.stl', 'stl/modifiers/tub__mod_s_c3.stl', 'stl/modifiers/tub__mod_s_j.stl', 'stl/modifiers/tub__mod_s_k1.stl', 'stl/modifiers/tub__mod_s_k2.stl', 'stl/modifiers/tub__mod_s_r1.stl', 'stl/modifiers/tub__mod_s_r2.stl', 'stl/panel.stl', 'stl/pi_keeper.stl', 'stl/plunger.stl', 'stl/stick_sleeve.stl', 'stl/tub.stl',
                            'stl/tools/collar_gauge.stl'])      # r6 (X2): the collar centring gauge
EXPECTED_COUPON_OUTPUTS = set(['stl/coupons/base_edge_base.stl', 'stl/coupons/base_edge_panel.stl', 'stl/coupons/base_edge_tub.stl', 'stl/coupons/board_edge_plate.stl', 'stl/coupons/cap_retention_cap.stl', 'stl/coupons/cap_retention_grip.stl', 'stl/coupons/clearance_comb.stl', 'stl/coupons/collar_hood_plate.stl', 'stl/coupons/collar_part.stl', 'stl/coupons/collar_tub_front.stl', 'stl/coupons/coupon-pi-keeper-part.stl', 'stl/coupons/coupon-pi-keeper-pi.stl', 'stl/coupons/coupon-pi-keeper-tub.stl', 'stl/coupons/coupon-pi-keeper-x1203.stl', 'stl/coupons/encoder_cradle_hook.stl', 'stl/coupons/evf_stop_panel.stl', 'stl/coupons/evf_stop_tub.stl', 'stl/coupons/hood_hook.stl', 'stl/coupons/hood_hook_ret.stl', 'stl/coupons/hood_ledge.stl', 'stl/coupons/hood_ledge_ret.stl', 'stl/coupons/keyhole_slot.stl', 'stl/coupons/knob_bore_ladder_enc.stl', 'stl/coupons/knob_bore_ladder_sw.stl', 'stl/coupons/pt_boss_bottom.stl', 'stl/coupons/pt_boss_post.stl', 'stl/coupons/tongue.stl'])
EXPECTED_PINS = {'PyYAML': '6.0.3', 'aiohappyeyeballs': '2.7.1', 'aiohttp': '3.14.3', 'aiosignal': '1.4.0', 'attrs': '26.1.0', 'cadquery': '2.6.1', 'cadquery-ocp': '7.8.1.1.post1', 'casadi': '3.8.1', 'charset-normalizer': '3.5.1', 'contourpy': '1.4.0', 'cycler': '0.12.1', 'ezdxf': '1.4.4', 'fonttools': '4.65.0', 'frozenlist': '1.8.0', 'idna': '3.20', 'kiwisolver': '1.5.1', 'manifold3d': '3.5.4', 'matplotlib': '3.11.2', 'more-itertools': '11.1.0', 'msgpack': '1.2.2', 'multidict': '6.9.0', 'multimethod': '1.12', 'nlopt': '2.11.0', 'numpy': '2.5.3', 'packaging': '26.3', 'path': '17.1.1', 'pillow': '12.3.0', 'propcache': '0.5.4', 'pymupdf': '1.28.2', 'pyparsing': '3.3.2', 'python-dateutil': '2.9.0.post0', 'reportlab': '5.0.1', 'six': '1.17.0', 'trame': '4.0.0', 'trame-client': '4.1.0', 'trame-common': '1.2.7', 'trame-server': '4.0.0', 'trame-vtk': '2.8.13', 'typing_extensions': '4.16.0', 'typish': '1.9.3', 'vtk': '9.3.1', 'wslink': '2.5.7', 'yarl': '1.25.1'}
EXPECTED_COMMON_HELPERS = set(['box_solid', 'cyl_solid(tube)', 'pt_boss', 'counterbore', 'snap_hook(hood hk1)', 'snap_strain', 'keyhole_tongue', 'keyhole_slot', 'dovetail(rail)', 'dovetail(groove)', 'vent_slots(out_band)', 'vent_slots(inlet_roof)', 'engrave(all items)', 'teardrop', 'bed_chamfer', 'safe_fillet(bad r falls back)', 'safe_fillet(ok)', 'to_print_pose(-Y)'])
EXPECTED_STATES = dict(slicer_review=12, coupon_validation=10, measured_fit=17, assembly_operation=26)
EXPECTED_STATES['assembly_operation'] += 3   # r7: the new assembly gates G-EVF-3, G-QT-1, G-HDR-1 (evidence/assembly/)
RECEIPT_KEYS = {'revision', 'sources', 'files', 'hardware_gates', 'status_states', 'summary', 'stubs', 'cad_release_candidate', 'blocking', 'unclassified_thin_spots', 'argv', 'carried_files'}


def load_json(path, required=()):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key: %s' % key)
            result[key] = value
        return result
    value = json.loads(path.read_text(), object_pairs_hook=unique,
                       parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite JSON: ' + value)))
    if not isinstance(value, dict) or not set(required) <= set(value):
        raise ValueError('%s is not an object with required keys %s' % (path.name, sorted(required)))
    return value


def exact_coverage(actual, expected, label, failures):
    if not isinstance(actual, (dict, set, frozenset)):
        failures.append(label + ' must be a mapping or set')
        return
    keys = set(actual)
    if keys != set(expected):
        failures.append('%s coverage missing=%r unexpected=%r' % (label, sorted(set(expected) - keys),
                                                                 sorted(keys - set(expected))))


def parse_pins(text):
    result = {}
    for line in text.splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        if line.count('==') != 1:
            raise ValueError('Every dependency must have one exact == pin')
        name, pinned = line.split('==')
        if name in result:
            raise ValueError('Duplicate dependency pin: ' + name)
        result[name] = pinned
    return result


def validated_pins(text, failures):
    declared = parse_pins(text)
    exact_coverage(declared, EXPECTED_PINS, 'dependency pin set', failures)
    if declared != EXPECTED_PINS:
        failures.append('Dependency versions differ from the independently recorded 43-pin runtime')
    return declared


def validate_print_parts(printed, failures):
    if not isinstance(printed, list) or len(printed) != 12:
        failures.append('Expected 12 production printed parts')
    ids = [row['id'] for row in printed]
    exact_coverage(set(ids), EXPECTED_PARTS, 'print-manifest part set', failures)
    if len(set(ids)) != len(ids):
        failures.append('Duplicate print-manifest part IDs')


def validate_producer(producer, expected_sources, script, failures):
    if not isinstance(producer, dict):
        failures.append(script + ' is missing producer-recorded metadata')
        return
    if producer.get('script') != script or producer.get('source_hashes') != expected_sources:
        failures.append(script + ' producer source hashes/script do not match the frozen release inputs')
    stamp = producer.get('generated_at')
    if isinstance(stamp, bool) or not isinstance(stamp, (int, float)) or not math.isfinite(stamp) or stamp <= 0:
        failures.append(script + ' has no valid producer timestamp')


def validate_common_result(result, revision, expected_sources, failures):
    if result.get('revision') != revision or result.get('all_ok') is not True:
        failures.append('Common-test revision or all_ok is invalid')
    rows = result.get('results')
    if not isinstance(rows, list):
        failures.append('Common-test results must be a list')
        rows = []
    names = [row.get('helper') for row in rows]
    if set(names) != EXPECTED_COMMON_HELPERS or len(names) != len(EXPECTED_COMMON_HELPERS):
        failures.append('Common-test helper coverage is missing, unexpected or duplicated')
    if not all(row.get('ok') is True and row.get('n', 0) > 0 and row.get('volume_mm3', 0) > 0 for row in rows):
        failures.append('Common-test result contains failed/empty helper geometry')
    validate_producer(result.get('producer'), expected_sources, 'test_common.py', failures)


def validate_coupon_manifest(manifest, revision, expected_sources, files, script, failures):
    if manifest.get('revision') != revision:
        failures.append(script + ' coupon revision does not match the release')
    validate_producer(manifest.get('producer'), expected_sources, script, failures)
    for row in manifest.get('coupons', []):
        if row.get('valid') is not True or row.get('volume_mm3', 0) <= 0:
            failures.append(script + ' contains an invalid/empty coupon')
        if not row.get('stl') or row.get('stl_sha256') != files.get(row.get('stl')):
            failures.append(script + ' coupon STL producer hash does not match the receipt')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def under(root, relative):
    rel = PurePosixPath(relative)
    if rel.is_absolute() or '..' in rel.parts or '\\' in relative:
        raise ValueError('Unsafe relative artifact path: %r' % relative)
    return root.joinpath(*rel.parts)


def read_stl(path):
    data = path.read_bytes()
    if len(data) < 84:
        raise ValueError('STL is shorter than its binary header')
    count = struct.unpack_from('<I', data, 80)[0]
    if len(data) != 84 + count * 50:
        raise ValueError('STL payload length does not match triangle count')
    dtype = np.dtype([('normal', '<f4', (3,)), ('v', '<f4', (3, 3)), ('attr', '<u2')])
    vertices = np.frombuffer(data, dtype=dtype, offset=84)['v'].reshape(-1, 3)
    if not np.isfinite(vertices).all():
        raise ValueError('STL contains nonfinite vertex coordinates')
    _, idx, inv = np.unique(np.round(vertices / 1e-5).astype(np.int64), axis=0,
                            return_index=True, return_inverse=True)
    mesh = m3.Mesh(vert_properties=np.ascontiguousarray(vertices[idx], np.float32),
                   tri_verts=np.ascontiguousarray(inv.reshape(-1, 3), np.uint32))
    solid = m3.Manifold(mesh)
    if solid.is_empty():
        raise ValueError('Serialized STL is not a nonempty manifold')
    return solid, count


def _audit(project, out, require_step=False, final_release=False, alternate_out=None):
    cad = project / 'cad/gs8-d2-v1'
    receipt = load_json(out / 'build-receipt.json', RECEIPT_KEYS)
    checks = load_json(out / 'checks.json', {'summary', 'results', 'revision', 'lens_default'})
    printed = load_json(out / 'print-manifest.json', {'parts'})['parts']
    failures, links, meshes = [], {}, []

    def require(condition, message):
        if not condition:
            failures.append(message)

    # r7: the release label names its parent; r6-20261008 descends from r5-cloud-polish-20261007 (same font sources)
    cloud = any(tag in receipt['revision'] for tag in ('r5-cloud-polish-20261007', 'r6-20261008'))
    exact_coverage(receipt['sources'], EXPECTED_SOURCES | (FONT_SOURCES if cloud else set()), 'source set', failures)
    exact_coverage(receipt['hardware_gates']['source_docs'], EXPECTED_GATE_DOCS, 'gate-document set', failures)
    exact_coverage(receipt['hardware_gates']['gates'], EXPECTED_GATE_IDS, 'physical-gate ID set', failures)
    exact_coverage(receipt['status_states'], set(EXPECTED_STATES) | {'cad_checks'}, 'evidence-state set', failures)
    required_outputs = set(EXPECTED_BASE_OUTPUTS)
    if require_step or final_release:
        required_outputs |= {'step/gs8-d2-assembly.step'} | {'step/parts/%s.step' % p for p in EXPECTED_PARTS}
    if final_release:
        require(cloud, 'Final release must declare its r5-cloud-polish-20261007 lineage')
        required_outputs |= EXPECTED_COUPON_OUTPUTS | {'coupons-manifest.json', 'coupons-r1-manifest.json',
                                                      'checks-fujinon-sweep1mm.json', 'test_common.json'}
    require(required_outputs <= set(receipt['files']),
            'Required output coverage missing: %r' % sorted(required_outputs - set(receipt['files'])))

    for label, base, entries in (
        ('sources', cad, receipt['sources']), ('outputs', out, receipt['files']),
        ('gate_docs', project, receipt['hardware_gates']['source_docs']),
    ):
        verified = 0
        for name, digest in entries.items():
            path = under(base, name)
            ok = path.is_file() and sha(path) == digest
            require(ok, '%s hash missing/mismatched: %s' % (label, name))
            verified += bool(ok)
        links[label] = dict(total=len(entries), verified=verified)

    require(sha(out / 'checks.json') == receipt['status_states']['cad_checks']['checks_json_sha256'],
            'CAD checks digest disagrees with receipt')
    require(checks['summary'] == receipt['summary'], 'Checks and receipt summaries disagree')
    categories = {row['check'] for row in receipt['summary']}
    require(categories == EXPECTED_CATEGORIES and len(receipt['summary']) == len(EXPECTED_CATEGORIES),
            'Required category set was changed, omitted, or duplicated')
    require(all(row['status'] == ('info' if row['check'] in INFO_CATEGORIES else 'pass') for row in receipt['summary']),
            'A CAD category is not passing (report-only categories must read info)')
    require(not receipt['stubs'] and receipt['cad_release_candidate'], 'CAD has stubs or is not a computed candidate')
    require(not receipt['blocking'], 'Receipt reports blocking checks')
    require(not receipt.get('unclassified_thin_spots'), 'Unclassified thin spots remain')
    validate_print_parts(printed, failures)

    for row in printed:
        path = under(out, row['stl'])
        require(row['stl'] in receipt['files'], 'Production STL is not hash-linked: %s' % row['id'])
        require(sha(path) == row['stl_sha256'], 'Print manifest STL hash mismatch: %s' % row['id'])
        try:
            solid, triangles = read_stl(path)
            volume = solid.volume()
            shells = len(solid.decompose())
            deviation = abs(volume - row['volume_mm3']) / max(row['volume_mm3'], 1e-9)
            ok = shells == 1 and volume > 0 and deviation <= 0.005
            require(ok, 'Serialized STL shell/volume check failed: %s' % row['id'])
            meshes.append(dict(part=row['id'], triangles=triangles, shells=shells, volume_mm3=volume,
                               manifest_volume_mm3=row['volume_mm3'], relative_deviation=deviation,
                               status='pass' if ok else 'fail'))
        except Exception as error:
            failures.append('Serialized STL inspection failed: %s: %s' % (row['id'], error))

    if require_step or final_release:
        required_step = ['step/gs8-d2-assembly.step'] + ['step/parts/%s.step' % row['id'] for row in printed]
        for name in required_step:
            require(name in receipt['files'] and under(out, name).is_file(), 'Fresh STEP missing: %s' % name)
        require('--fast' not in receipt['argv'], 'Final STEP build unexpectedly used --fast')
    if '--skip-renders' in receipt['argv'] or '--fast' in receipt['argv']:
        for name in receipt['files']:
            if name.startswith('renders/'):
                require(name in EXPECTED_BASE_OUTPUTS, 'Skipped VTK image was incorrectly adopted: %s' % name)

    gates = receipt['hardware_gates']['gates']
    gate_counts = dict(total=len(gates), open=sum(v.startswith('open') for v in gates.values()),
                       withdrawn=sum(v.startswith('withdrawn') for v in gates.values()))
    require(gate_counts == dict(total=55 + 3, open=53 + 3, withdrawn=2), 'Physical gate count/state unexpectedly changed')   # r7: + G-EVF-3, G-QT-1, G-HDR-1
    require({key for key, value in gates.items() if value.startswith('withdrawn')} == {'G-SKIRT-1', 'G-SNAP-1'},
            'Unexpected withdrawn physical gate')
    for name, state in receipt['status_states'].items():
        if name != 'cad_checks':
            require(state['items_required'] == EXPECTED_STATES.get(name) and state['items_complete'] == 0,
                    'Physical evidence required-count/completion changed: ' + name)
            require(state['status'] == 'not run' and state['items_pass'] == 0 and state['open'],
                    'Physical evidence was incorrectly advanced: %s' % name)

    lock = project / 'cad/gs8-pxl-v3/cad-requirements-lock.txt'
    packages = []
    declared = validated_pins(lock.read_text(), failures)
    for name, pinned in declared.items():
        try:
            actual = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            actual = None
        packages.append(dict(name=name, pinned=pinned, actual=actual))
        require(actual == pinned, 'Runtime pin mismatch: %s' % name)
    require(platform.python_version() == '3.12.14', 'Python interpreter does not match 3.12.14')
    if final_release:
        classification = [row for row in checks['results']['critical_features']
                          if row.get('id') == 'thin_spot_classification']
        require(len(classification) == 1 and classification[0].get('status') == 'pass'
                and classification[0].get('unclassified_count') == 0,
                'Final build lacks its explicit passing thin-spot classification gate')
        coupon_paths = []
        for filename in ('coupons-manifest.json', 'coupons-r1-manifest.json'):
            manifest = load_json(out / filename, {'coupons', 'producer', 'revision'})
            validate_coupon_manifest(manifest, receipt['revision'], receipt['sources'], receipt['files'],
                                     'make_coupons.py' if filename == 'coupons-manifest.json' else 'coupons_r1.py', failures)
            coupon_paths += [row['stl'] for row in manifest['coupons'] if row.get('stl')]
        exact_coverage(set(coupon_paths), EXPECTED_COUPON_OUTPUTS, 'coupon-manifest STL set', failures)
        require(len(coupon_paths) == len(set(coupon_paths)), 'Duplicate coupon STL entries')
        carried = receipt['carried_files'].get('test_common.json')
        require(isinstance(carried, dict), 'Common-test carried evidence is missing')
        if isinstance(carried, dict):
            common_sources = dict(receipt['sources'], **{'test_common.py': sha(cad / 'test_common.py')})
            exact_coverage(carried.get('inputs'), common_sources, 'common-test input set', failures)
            common_result = load_json(out / 'test_common.json', {'results', 'all_ok', 'revision', 'producer'})
            validate_common_result(common_result, receipt['revision'], common_sources, failures)
            require(carried.get('inputs') == common_result['producer'].get('source_hashes'),
                    'Carried common-test hashes are not the producer-recorded hashes')
            for name, digest in (carried.get('inputs') or {}).items():
                require(sha(under(cad, name)) == digest, 'Common-test input hash mismatch: ' + name)
        require(alternate_out is not None, 'Final release requires an explicit alternate-lens output directory')
        if alternate_out is not None:
            other = audit(project, alternate_out, require_step=True)
            require(other['status'] == 'pass', 'Alternate-lens artifact audit failed: ' + '; '.join(other['failures']))
            copied = out / 'checks-fujinon-sweep1mm.json'
            require(sha(copied) == sha(alternate_out / 'checks.json'), 'Copied Fujinon checks do not match alternate output')
            alternate_checks = load_json(alternate_out / 'checks.json', {'lens_default'})
            require(alternate_checks['lens_default'] == 'fujinon_hf6xa', 'Alternate output is not the Fujinon lens')
            carried_alt = (receipt.get('carried_checks') or {}).get('checks-fujinon-sweep1mm.json') or {}
            require(carried_alt.get('sources_match') is True and alternate_checks.get('sources') == receipt['sources'],
                    'Carried Fujinon checks were not built from the release sources (audit 2026-10-06 L11)')
            require(checks['lens_default'] == 'kowa_lm6hc', 'Final primary output is not the Kowa lens')

    return dict(status='pass' if not failures else 'fail', revision=receipt['revision'],
                receipt_sha256=sha(out / 'build-receipt.json'), checks_sha256=sha(out / 'checks.json'),
                hash_links=links, categories=len(categories), meshes=meshes, physical_gates=gate_counts,
                runtime=dict(python=platform.python_version(), system=platform.system(),
                             lock_sha256=sha(lock), packages=packages), failures=failures,
                note='Computational artifact integrity only; no slicer, measurement, fabrication or hardware qualification.')


def audit(project, out, require_step=False, final_release=False, alternate_out=None):
    try:
        return _audit(project, out, require_step, final_release, alternate_out)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, IndexError) as error:
        return dict(status='fail', failures=['Malformed, missing or unreadable release evidence: ' + str(error)],
                    hash_links={}, categories=None, physical_gates=None)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--require-step', action='store_true')
    parser.add_argument('--final-release', action='store_true')
    parser.add_argument('--alternate-out', type=Path)
    parser.add_argument('--json', type=Path)
    args = parser.parse_args()
    result = audit(args.project.resolve(), args.out.resolve(), args.require_step, args.final_release,
                   args.alternate_out.resolve() if args.alternate_out else None)
    payload = json.dumps(result, indent=2, allow_nan=False) + '\n'
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(payload)
    print(json.dumps({key: result[key] for key in ('status', 'hash_links', 'categories', 'physical_gates', 'failures')},
                     indent=2))
    return 0 if result['status'] == 'pass' else 1


if __name__ == '__main__':
    sys.exit(main())
