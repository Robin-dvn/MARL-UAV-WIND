import subprocess
from pathlib import Path
import shutil
import time # Added import
import json # Added import

import platform
import sys

def run_in_wsl(script_name):
    win_path = Path(script_name).resolve()
    # Conversion chemin Windows → WSL
    wsl_path = f"/mnt/{win_path.drive[0].lower()}/{win_path.as_posix()[3:]}"
    print(f"Script WSL : {wsl_path}")
    # Utiliser bash interactif pour charger ~/.bashrc et donc le PATH de uv
    subprocess.run(["wsl", "bash", "-ic", f"uv run '{wsl_path}'"], check=True)

# Si tu es sous Windows, relancer le script dans WSL
if platform.system() == "Windows":
    print("🔁 Passage automatique dans WSL...")
    print(sys.argv[0])
    run_in_wsl(sys.argv[0])
    sys.exit()

# (sinon, continue l'exécution normale sous Linux / WSL)

# === Paramètres ===
angles = [90]
base_geometry = Path("/mnt/c/Users/r.davenne/Documents/geometry/base_buildings.stl")
base_case = Path("/home/rdavenne/OpenFOAM_cases/windAroundBuildings")
output_dir = Path("/home/rdavenne/OpenFOAM_cases/test_dataset")
freecad_script = Path("rotate_stl.py")
slice_script = Path("slice_and_export.py")

output_dir.mkdir(exist_ok=True)

script_timings = {} # To store timings

for angle in angles:
    case_dir = output_dir / f"case_{angle}"
    case_geometry = case_dir / "constant/triSurface/buildings.stl"

    # Copier le cas de base
    if case_dir.exists():
        shutil.rmtree(case_dir)
    shutil.copytree(base_case, case_dir)

    rotate_path = Path("utils_scripts/rotate_stl.py").resolve()

    # Timer for FreeCAD script
    freecad_start_time = time.time()
    subprocess.run([
        "freecadcmd", str(rotate_path),
        str(base_geometry),
        str(case_geometry),
        str(angle)
    ], check=True)
    freecad_end_time = time.time()
    script_timings[f"freecad_rotation_angle_{angle}"] = freecad_end_time - freecad_start_time


    # Lancer les commandes OpenFOAM
    # Timer for OpenFOAM commands
    openfoam_start_time = time.time()
    bash_cmd = f'''
    source /usr/lib/openfoam/openfoam2412/etc/bashrc
    cd {case_dir}
    mkdir 0
    cp -r 0.org/* 0
    blockMesh
    surfaceFeatureExtract
    snappyHexMesh -overwrite
    simpleFoam
    touch case.foam
    exit
    '''
    subprocess.run(["bash", "-c", bash_cmd], check=True)
    openfoam_end_time = time.time()
    script_timings[f"openfoam_simulation_angle_{angle}"] = openfoam_end_time - openfoam_start_time

    # Export slice avec ParaView
    # subprocess.run([
    #     "pvpython", str(slice_script),
    #     str(case_dir / "case.foam"),
    #     str(case_dir / "slice.csv")
    # ], check=True)

# Save timings to a JSON file
timings_file_path = output_dir / "script_timings.json"
with open(timings_file_path, 'w') as f:
    json.dump(script_timings, f, indent=4)

print(f"Timings saved to {timings_file_path}")
