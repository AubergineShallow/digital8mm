import numpy as np, json
from d3_plate import run
out = {}
for name, kw in [
    ('rd30 pitch ss/ss', dict(rd=30)),
    ('rd30 pitch free-left ss-top', dict(rd=30, left='free')),
    ('rd30 pitch free/free', dict(rd=30, left='free', top='free')),
    ('rd30 yaw free/free', dict(rd=30, left='free', top='free', load='yaw')),
    ('rd20 yaw free/free', dict(rd=20, left='free', top='free', load='yaw')),
    ('rd30 pitch free/free E900 (creep 1000h 50C)', dict(rd=30, left='free', top='free', E=900.0)),
]:
    r = run(**kw); out[name] = r
    print('%-44s %.3e rad/Nm = %.3f deg/Nm' % (name, r, np.degrees(r)), flush=True)
json.dump(out, open('d3_plate2.json', 'w'), indent=1)
