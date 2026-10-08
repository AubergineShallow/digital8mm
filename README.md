# digital8mm: GS8 D2

GS8 D2 is a pistol-grip digital "Super 8" cine camera in the spirit of the Nizo:
- a Raspberry Pi 5 with the Raspberry Pi Global Shutter camera (IMX296, C/CS mount);
- an integrated micro-OLED electronic viewfinder;
- a 3D-printed ASA body;
- a physical 18/24 fps switch, an exposure dial and a record button;
- recording RAW to a removable USB stick.

This repository holds **only the D2 fork** of the wider GS8 project, plus the few shared files its build needs.

**Status:** a computed CAD release candidate (r6, 2026-10-08), **not a qualified design**.
- Every result here is a computed check on built solids and purchased-part proxies, desk research, or a document.
- Nothing has been printed, sliced, bought, measured, assembled or powered.
- 53 physical bench gates are open.
- **Print order (r6).** It is settled and enforced: [`PRINT-GUIDE.md`](cad/gs8-d2-v1/PRINT-GUIDE.md) section 7 says
  which measurements each part waits for. Start with the calibration coupons and the bench measurements (camera and
  lens first).
- **Print orientation (r6).** It is settled and checked layer by layer (`print_overhang`).
- **Open design defect.** The lens collar's clamp has no spring (audit 2026-10-06 M1); fix it before the collar is
  printed.

## Start here

1. [`cad/gs8-d2-v1/HANDOFF.md`](cad/gs8-d2-v1/HANDOFF.md): current state, latest build receipt, open items.
2. [`CLOUD-START-HERE.md`](CLOUD-START-HERE.md): how to reproduce the CAD and run the software on a host.
3. Design and build documents:
   - [`SPEC.md`](cad/gs8-d2-v1/SPEC.md): the contract;
   - [`DESIGN.md`](cad/gs8-d2-v1/DESIGN.md);
   - [`ASSEMBLY.md`](cad/gs8-d2-v1/ASSEMBLY.md);
   - [`PRINT-GUIDE.md`](cad/gs8-d2-v1/PRINT-GUIDE.md);
   - [`FASTENER-POLICY.md`](cad/gs8-d2-v1/FASTENER-POLICY.md);
   - [`MEASURED-PARTS.md`](cad/gs8-d2-v1/MEASURED-PARTS.md): the bench gates.
4. Electronics: [`electronics/gs8-d2-v1/WIRING.md`](electronics/gs8-d2-v1/WIRING.md) and
   [`BOM.md`](electronics/gs8-d2-v1/BOM.md).

## Layout

| Path | Contents |
|---|---|
| `cad/gs8-d2-v1/` | CadQuery sources (`layout.py` is the single geometry source), checks, tests, docs, research notes |
| `cad/gs8-d2-v1/out/` | Current release outputs: production STLs, modifier and coupon meshes, the collar centring gauge (`stl/tools/`), STEP, manifests, `checks.json`, `build-receipt.json`; Fujinon variant in `out/_fujinon-cloud-polish-20261007/` |
| `electronics/gs8-d2-v1/` | Wiring, BOM generator and BOM, power and fuse research, second-hand sourcing notes |
| `software/gs8-camera-evf/` | Camera software package, including the D2 integration (`d2_*.py`, `D2-INTEGRATION.md`) |
| `audit/d2-readiness-*` | Independent readiness audits of D2 and their responses |
| `visual-review/`, `validation/` | Rendered review views and computed verification records |

**Shared files carried over from the parent project** because the D2 build reads them:
- `electronics/gs8-evf-v1/EVF-SELECTION.md`: an EVF gate document;
- `cad/gs8-pxl-v3/cad-requirements-lock.txt`: the pinned CAD environment;
- `tools/bootstrap_cad.py`: creates that environment;
- `outputs/bom-release-2026-09-25/prices.json`: BOM prices.

**Kept out of git** (see `.gitignore`):
- manufacturer drawings and datasheet images used in research;
- airflow-simulation checkpoints;
- historical build folders;
- baseline zip snapshots.

## Reproduce

Use the pinned environment (Python 3.12.14 plus 43 locked packages), then run from the repository root. On Windows
use `.venv-cad/Scripts/python.exe` as the interpreter:

```text
python tools/bootstrap_cad.py
python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/test_r3_regressions.py
python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/build_d2.py --skip-renders --sweep-step 1.0
```

The full release sequence (coupons, Fujinon variant, tables, BOM, audit) is in `CLOUD-START-HERE.md`. Heavy CAD
commands always go through `run_locked.py`.

## Licences

- `software/gs8-camera-evf/` and `tools/` carry their own licence files.
- The DejaVu font has its licence in `cad/gs8-d2-v1/fonts/`.
- No licence has been chosen yet for the rest of this repository.
