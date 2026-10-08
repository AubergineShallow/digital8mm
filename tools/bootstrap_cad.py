"""MIT. Recreate the CAD runtime without an application-owned interpreter/cache.

Run using an installed Python >=3.10. Downloads pinned uv, standalone CPython
and wheel dependencies into ignored project-local directories. No global PATH,
system Python, original temporary venv or boot configuration is changed.
"""
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
UV_VERSION = '0.12.17'
PYTHON_VERSION = '3.12.14'


def run(*command, env=None):
    print('RUN', ' '.join(str(x) for x in command), flush=True)
    subprocess.run([str(x) for x in command], check=True, cwd=ROOT, env=env)


def executable(environment, name='python'):
    return environment / ('Scripts' if os.name == 'nt' else 'bin') / (name + ('.exe' if os.name == 'nt' else ''))


def main():
    bootstrap = ROOT / '.venv-bootstrap'
    if not executable(bootstrap).exists():
        run(sys.executable, '-m', 'venv', bootstrap)
    run(executable(bootstrap), '-m', 'pip', 'install', '--disable-pip-version-check', f'uv=={UV_VERSION}')
    uv = executable(bootstrap, 'uv')
    env = dict(os.environ, UV_PYTHON_INSTALL_DIR=str(ROOT / '.tools' / 'python'),
               UV_PYTHON_BIN_DIR=str(ROOT / '.tools' / 'bin'), UV_CACHE_DIR=str(ROOT / '.tools' / 'uv-cache'))
    run(uv, 'python', 'install', PYTHON_VERSION, env=env)
    target = ROOT / '.venv-cad'
    if not executable(target).exists():
        run(uv, 'venv', '--managed-python', '--python', PYTHON_VERSION, target, env=env)
    run(uv, 'pip', 'sync', '--python', executable(target), ROOT / 'cad/gs8-pxl-v3/cad-requirements-lock.txt', env=env)
    run(uv, 'pip', 'check', '--python', executable(target), env=env)
    run(executable(target), '-c', 'import sys,cadquery,vtk,PIL; print(sys.version); print("CadQuery",cadquery.__version__,"VTK",vtk.vtkVersion.GetVTKVersion(),"Pillow",PIL.__version__)')


if __name__ == '__main__':
    main()
