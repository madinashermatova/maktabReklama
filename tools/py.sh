#!/bin/sh
# Run Blender's bundled Python with the project-local deps (Pillow, SciPy, fontTools).
# Setup once:  "<Blender>/5.3/python/bin/python.exe" -m pip install --target tools/pydeps pillow scipy fonttools
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHONIOENCODING=utf-8 PYTHONPATH="$ROOT/tools/pydeps" exec "/c/Program Files/Blender Foundation/Blender 5.3/5.3/python/bin/python.exe" "$@"
