"""integrate-fork helper: replace the section-8 table in CANDIDATE.md by the table in out/fr1-validation.md (no CAD)."""
import os
H = os.path.dirname(os.path.abspath(__file__))
t = [l for l in open(os.path.join(H, 'out', 'fr1-validation.md')).read().splitlines() if l.startswith('|')]
c = open(os.path.join(H, 'CANDIDATE.md')).read().splitlines()
i = next(k for k, l in enumerate(c) if l.startswith('## 8.'))
a = next(k for k in range(i, len(c)) if c[k].startswith('|'))
b = a
while b < len(c) and c[b].startswith('|'):
    b += 1
c[a:b] = t
open(os.path.join(H, 'CANDIDATE.md'), 'w').write('\n'.join(c) + '\n')
print('spliced', len(t), 'rows')
