"""FR1 before/after counts, computed from the fork layout (no CAD). One fresh subprocess per D2_FR value.

Run from the repo root:  .venv-cad/Scripts/python.exe -B cad/gs8-d2-v1/candidate-fr1/fr1_counts.py
Writes candidate-fr1/out/fr1-counts.json and candidate-fr1/out/fr1-counts.md. Counts come from layout.PARTS / SCREWS /
COTS / X1203_KIT / STEPS / REMOVALS / RELEASE_ACCESS for each toggle state; nothing is hand-typed except the tool
keyword table and the fixed service preamble (ASSEMBLY s7 P1-P4: shutdown and pack disconnection come first)."""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
STATES = ['none', 'panel', 'keeper', 'hood=yslide', 'hood=screw1', 'all', 'panel,keeper,hood=screw1']
TOOL_WORDS = [('PH1 screwdriver', r'PH1|screwdriver|kit driver'), ('soldering iron', r'soldering'),
              ('multimeter', r'multimeter'), ('socket / spanner', r'socket|spanner'), ('tweezers', r'tweezers'),
              ('paint pen', r'paint pen'), ('release pins (2 x dia 1.5)', r'pins?\b.*1\.5|1\.5.*pin'),
              ('ESD strap', r'ESD'), ('junior hacksaw + file', r'hacksaw|\bfile\b'),
              # r4 (audit 2026-10-05-r3): the full ASSEMBLY s1.1 toolset, not a subset presented as the full count
              ('wire stripper + flush cutter', r'stripper|cutter'), ('heat gun', r'heat.?gun|heat-shrink|heat shrink'),
              ('flat bar / steel rule', r'flat bar|steel rule')]   # fix-candidate VC-L6: was missing
PREAMBLE = ['shut down (Pi halt is NOT isolation)', 'cap off (tool-free)', 'pack out', 'XT30 unplugged '
            '(physical battery disconnection before any internal electronic service: ASSEMBLY s7 P1-P4)']
POWER = ('cap', 'pack', 'xt30_pair')


def one():
    sys.path.insert(0, HERE)
    import layout as L
    screws = [s['id'] for s in L.SCREWS]
    kit = L.X1203_KIT
    n_kit_scr = int(re.match(r'\s*(\d+)', kit['screws']).group(1))
    n_kit_so = int(re.match(r'\s*(\d+)', kit['standoff']).group(1))
    tool_txt = [s['tool'] for s in L.STEPS] + [r.get('tool', '') for r in L.REMOVALS] + \
               [r.get('tool', '') for r in L.RELEASE_ACCESS]
    cats = sorted({name for name, rx in TOOL_WORDS for t in tool_txt if t and re.search(rx, t, re.I)})
    rem = {r['id']: r for r in L.REMOVALS}
    scr_tool = {s['id']: s.get('step') for s in L.SCREWS}
    joins = {s['id']: list(s['joins']) + [s['head_part'], str(s.get('into', '')).split(' ')[0]] for s in L.SCREWS}

    def seq(rid):
        r = rem[rid]
        out, seen = list(PREAMBLE), set(POWER)
        todo = [i for i in r['off'] + r['unscrew'] if i not in POWER]
        scr = [i for i in todo if i in scr_tool]
        for i in todo:              # a screw is listed just before the first part it holds (layout SCREWS joins)
            if i in seen or i in scr_tool:
                continue
            for sid in scr:
                if sid not in seen and i in joins[sid]:
                    seen.add(sid)
                    out.append('unscrew %s (straight PH1)' % sid)
            seen.add(i)
            out.append('remove %s' % i)
        for sid in scr:
            if sid not in seen:
                seen.add(sid)
                out.append('unscrew %s (straight PH1)' % sid)
        if r['release']:
            out.append('release %s (%s)' % ('/'.join(r['release']), r.get('tool', '')))
        out.append('take out %s [%s]' % (' + '.join(r['moving']), r.get('tool', '')))
        return out
    pins = [r['id'] for r in L.RELEASE_ACCESS]
    svc = {i for r in L.REMOVALS for i in r['off'] + r['unscrew']}
    j4_lock = [s['id'] for s in L.SCREWS if set(s['joins']) == {'base_grip', 'tub'} and s['id'] not in svc]
    return dict(
        state=L.FR_STATE, d2_fr=os.environ.get('D2_FR'), printed_parts=len(L.PARTS), printed_ids=list(L.PARTS),
        pt_body_screws=len(screws), pt_screw_ids=screws, pt_cots_line=L.COTS['pt_screws']['name'],
        ups_kit_m25_screws=n_kit_scr, ups_kit_standoffs=n_kit_so,
        purchased_lines=len(L.COTS), purchased_ids=sorted(L.COTS),
        release_access=pins, release_pins=(2 if pins else 0), loose_release_tools=(1 if pins else 0),
        tool_categories=cats, j4_independent_lock=j4_lock, assembly_steps=len(L.STEPS),
        steps=['%s %s [%s]' % (s['step'], s['name'], s['tool']) for s in L.STEPS],
        screw_steps={s['id']: s.get('step') for s in L.SCREWS},
        service=dict(panel=seq('panel_off'), pi=seq('pi_out'), hood=seq('hood_off')))


def main():
    py = sys.executable
    res = []
    for st in STATES:
        env = dict(os.environ, D2_FR=st)
        p = subprocess.run([py, '-B', os.path.abspath(__file__), '--one'], env=env, capture_output=True, text=True)
        if p.returncode:
            sys.exit('state %s failed:\n%s' % (st, p.stderr[-2000:]))
        res.append(json.loads(p.stdout.strip().splitlines()[-1]))
    os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
    with open(os.path.join(HERE, 'out', 'fr1-counts.json'), 'w', encoding='utf-8') as f:
        json.dump(dict(note='computed from candidate-fr1/layout.py per D2_FR value (fr1_counts.py); counts only, '
                       'nothing printed, bought or assembled', states=res), f, indent=1)
    base = res[0]
    cols = [('printed_parts', 'printed parts'), ('pt_body_screws', 'PT body screws'),
            ('ups_kit_m25_screws', 'UPS kit M2.5 screws'), ('ups_kit_standoffs', 'UPS kit standoffs'),
            ('purchased_lines', 'purchased lines (COTS)'), ('release_pins', 'loose release pins'),
            ('assembly_steps', 'assembly steps')]
    L = ['| D2_FR | ' + ' | '.join(c[1] for c in cols) + ' | PT screw ids | J4 independent lock | tool categories named in step/removal texts (a subset) |',
         '|---' * (len(cols) + 4) + '|']
    for r in res:
        cells = []
        for k, _ in cols:
            d = r[k] - base[k]
            cells.append('%d%s' % (r[k], (' (%+d)' % d) if d else ''))
        L.append('| %s | %s | %s | %s | %s |' % (r['d2_fr'], ' | '.join(cells), ', '.join(r['pt_screw_ids']),
                                                 ', '.join(r['j4_independent_lock']) or 'NONE',
                                                 ', '.join(r['tool_categories'])))
    L += ['', '**Tool count (r4, audit 2026-10-05-r3):** the last column is a keyword scan of the layout step and '
          'removal tool texts, a subset. The authoritative full toolset is ASSEMBLY.md s1.1: **12 tools** with the hood '
          'release pins (`none`, `panel`, `keeper`), **11** for every hood variant without pins (`hood=yslide`, '
          '`hood=screw1`, `all`). The release pins are the only tool any FR1 joint removes; the camera is not a '
          'one-screwdriver build (stripper/cutter, heat gun, flat bar, soldering iron and the rest remain).']
    L += ['', 'Service sequences (derived from layout.REMOVALS off/unscrew lists; each screw is placed before the first part it joins; '
          'preamble = ASSEMBLY s7 P1-P4). The order of the other items follows the registry lists: an action list, not a '
          'replacement for ASSEMBLY.md:', '']
    for r in res:
        if r['d2_fr'] not in ('none', 'all', 'panel,keeper,hood=screw1'):
            continue
        L.append('### D2_FR=%s' % r['d2_fr'])
        for k in ('panel', 'hood', 'pi'):
            L.append('- **%s service** (%d actions): %s' % (k, len(r['service'][k]), ' -> '.join(r['service'][k])))
        L.append('')
    with open(os.path.join(HERE, 'out', 'fr1-counts.md'), 'w', encoding='utf-8') as f:
        f.write('# FR1 counts (generated by fr1_counts.py; do not edit)\n\n' + '\n'.join(L) + '\n')
    print('\n'.join(L[:len(res) + 2]))


if __name__ == '__main__':
    if '--one' in sys.argv:
        print(json.dumps(one()))
    else:
        main()
