import subprocess
from pathlib import Path
import shutil

# === Paramètres ===
angles = [0, 15, 30]
base_geometry = Path("base_geometry/buildings_original.stl")
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

    # Lancer FreeCAD pour appliquer la rotation
    subprocess.run([
        "freecadcmd", "rotate_stl.py",
        str(base_geometry),
        str(case_geometry),
        str(angle)
    ], check=True)

    # Lancer les commandes OpenFOAM
    # bash_cmd = f'''
    # openfoam2412
    # cd {case_dir}
    # blockMesh
    # surfaceFeatureExtract
    # snappyHexMesh -overwrite
    # simpleFoam
    # touch case.foam
    # '''
    # subprocess.run(["bash", "-c", bash_cmd], check=True)

    # Export slice avec ParaView
    # subprocess.run([
    #     "pvpython", str(slice_script),
    #     str(case_dir / "case.foam"),
    #     str(case_dir / "slice.csv")
    # ], check=True)
