import subprocess
from pathlib import Path
import shutil

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
angles = [0, 15, 30]
base_geometry = Path("/mnt/c/Users/r.davenne/Documents/geometry/base_buildings.stl")
base_case = Path("/home/rdavenne/OpenFOAM_cases/windAroundBuildings")
output_dir = Path("/home/rdavenne/OpenFOAM_cases/test_dataset")
freecad_script = Path("rotate_stl.py")
slice_script = Path("slice_and_export.py")

output_dir.mkdir(exist_ok=True)

for angle in angles:
    case_dir = output_dir / f"case_{angle}"
    case_geometry = case_dir / "constant/triSurface/buildings.stl"

    # Copier le cas de base
    if case_dir.exists():
        shutil.rmtree(case_dir)
    shutil.copytree(base_case, case_dir)

    rotate_path = Path("utils_scripts/rotate_stl.py").resolve()


    subprocess.run([
        "freecadcmd", str(rotate_path),
        str(base_geometry),
        str(case_geometry),
        str(angle)
    ], check=True)


    # Lancer les commandes OpenFOAM
    bash_cmd = f'''
    source /usr/lib/openfoam/openfoam2412/etc/bashrc
    cd {case_dir}

    blockMesh
    exit
    '''
    # surfaceFeatureExtract
    # snappyHexMesh -overwrite
    # simpleFoam
    # touch case.foam

    # '''
    subprocess.run(["bash", "-c", bash_cmd], check=True)

    # Export slice avec ParaView
    # subprocess.run([
    #     "pvpython", str(slice_script),
    #     str(case_dir / "case.foam"),
    #     str(case_dir / "slice.csv")
    # ], check=True)
