"""
Build script to bundle d2ro Python packages into docs/python_bundle.js for Pyodide WebAssembly execution.
"""
import os
import json

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(ROOT_DIR, "docs")
TARGET_JS = os.path.join(DOCS_DIR, "python_bundle.js")

FILES_TO_BUNDLE = [
    "d2ro/__init__.py",
    "d2ro/core/__init__.py",
    "d2ro/core/units.py",
    "d2ro/core/graph.py",
    "d2ro/core/grid_map.py",
    "d2ro/core/dstar_lite.py",
    "d2ro/core/mesh_network.py",
    "d2ro/core/human.py",
    "d2ro/core/metrics.py",
    "d2ro/core/agent.py",
    "d2ro/environments/__init__.py",
    "d2ro/environments/supermarket.py",
    "d2ro/environments/airport.py",
    "d2ro/environments/hospital.py",
]

def main():
    bundle_data = {}
    for rel_path in FILES_TO_BUNDLE:
        full_path = os.path.join(ROOT_DIR, rel_path)
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            bundle_data[rel_path.replace("\\", "/")] = content
            print(f"Bundled {rel_path} ({len(content)} bytes)")
        else:
            print(f"WARNING: File missing {rel_path}")

    js_content = f"// Auto-generated D2RO Python Source Bundle for Pyodide WASM\nwindow.D2RO_PYTHON_FILES = {json.dumps(bundle_data, indent=2)};\n"

    with open(TARGET_JS, "w", encoding="utf-8") as f:
        f.write(js_content)
    print(f"Successfully generated {TARGET_JS} ({len(js_content)} bytes)")

if __name__ == "__main__":
    main()
