"""
This script automates the generation of a wind simulation dataset using OpenFOAM and ParaView.
It performs the following main steps for a list of specified angles:
1.  Copies a base OpenFOAM case.
2.  Rotates a base geometry (STL file) using FreeCAD's command line.
3.  Runs a series of OpenFOAM commands (blockMesh, surfaceFeatureExtract, snappyHexMesh, simpleFoam)
    to simulate wind flow around the rotated geometry.
4.  Exports a slice of the simulation data to a CSV file using ParaView's pvpython.
5.  Measures and records the execution time for each major step (FreeCAD, OpenFOAM, ParaView)
    and the total script duration into a JSON file.

The script is designed to be run in a Linux-like environment (e.g., WSL on Windows).
It includes an option to suppress subprocess output for a cleaner tqdm progress bar.

Usage:
    python dataset_wind_genrator.py [--suppress-output]
"""
import subprocess
from pathlib import Path
import shutil
import time
import json
from tqdm import tqdm # Added import
import platform
import sys

# If on Windows, display an error and exit.
if platform.system() == "Windows":
    print("ERROR: This script is designed to be run in a Linux-like environment (e.g., WSL).")
    print("Please run it from WSL or a Linux environment.")
    sys.exit(1)

def main_script_logic():
    """
    Main logic for the dataset generation script.

    Handles argument parsing for output suppression, sets up parameters,
    iterates through specified angles to perform geometry rotation, OpenFOAM simulation,
    and ParaView data extraction. It also times each significant operation and
    saves these timings to a JSON file.
    """
    # === Script arguments for suppression ===
    # (This is a simple way to handle it, consider argparse for more complex CLI args)
    suppress_subprocess_output = "--suppress-output" in sys.argv

    # === Parameters ===
    angles = [90, 180, 270] # Example with more angles
    base_geometry = Path("/mnt/c/Users/r.davenne/Documents/geometry/base_buildings.stl")
    base_case = Path("/home/rdavenne/OpenFOAM_cases/windAroundBuildings")
    output_dir = Path("/home/rdavenne/OpenFOAM_cases/test_dataset_timed_final")
    # freecad_script = Path("rotate_stl.py") # Assuming this is in the same dir or PATH - This variable is not used
    slice_script = Path("utils_scripts/slice_and_export.py") # Assuming this path is correct relative to execution

    output_dir.mkdir(exist_ok=True)

    script_timings = {} # To store timings
    total_script_start_time = time.time() # Start general timer

    # Use tqdm for the loop, disable if output is suppressed to avoid tqdm printing
    for angle in tqdm(angles, desc="Processing angles", disable=suppress_subprocess_output):
        case_dir = output_dir / f"case_{angle}"
        case_geometry = case_dir / "constant/triSurface/buildings.stl"

        # Copy the base case
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
        ], check=True, stdout=subprocess.DEVNULL if suppress_subprocess_output else None, stderr=subprocess.DEVNULL if suppress_subprocess_output else None)
        freecad_end_time = time.time()
        script_timings[f"freecad_rotation_angle_{angle}"] = freecad_end_time - freecad_start_time

        # Run OpenFOAM commands
        openfoam_start_time = time.time()
        bash_cmd = f"""
        source /usr/lib/openfoam/openfoam2412/etc/bashrc
        cd {case_dir}
        mkdir -p 0 # Use -p to avoid error if exists, though 0.orig is copied next
        cp -r 0.orig/* 0
        blockMesh
        surfaceFeatureExtract
        snappyHexMesh -overwrite
        simpleFoam
        touch case.foam
        exit
        """
        subprocess.run(["bash", "-c", bash_cmd], check=True, stdout=subprocess.DEVNULL if suppress_subprocess_output else None, stderr=subprocess.DEVNULL if suppress_subprocess_output else None)
        openfoam_end_time = time.time()
        script_timings[f"openfoam_simulation_angle_{angle}"] = openfoam_end_time - openfoam_start_time

        # Export slice with ParaView
        paraview_start_time = time.time() # Timer for ParaView
        subprocess.run([
            "pvpython", str(slice_script),
            str(case_dir / "case.foam"),
            str(case_dir / "slice.csv")
        ], check=True, stdout=subprocess.DEVNULL if suppress_subprocess_output else None, stderr=subprocess.DEVNULL if suppress_subprocess_output else None)
        paraview_end_time = time.time() # End timer for ParaView
        script_timings[f"paraview_slice_export_angle_{angle}"] = paraview_end_time - paraview_start_time # Store ParaView timing

    total_script_end_time = time.time() # End general timer
    script_timings["total_script_duration"] = total_script_end_time - total_script_start_time # Store general timing

    # Save timings to a JSON file
    timings_file_path = output_dir / "script_timings.json"
    with open(timings_file_path, 'w') as f:
        json.dump(script_timings, f, indent=4)

    if not suppress_subprocess_output:
        print(f"Timings saved to {timings_file_path}")

if __name__ == "__main__":
    main_script_logic()
