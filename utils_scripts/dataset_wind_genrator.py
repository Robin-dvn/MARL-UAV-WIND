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
import re # Added import
import itertools # Added import

# If on Windows, display an error and exit.
if platform.system() == "Windows":
    print("ERROR: This script is designed to be run in a Linux-like environment (e.g., WSL).")
    print("Please run it from WSL or a Linux environment.")
    sys.exit(1)

def update_inlet_velocity(case_dir_path: Path, velocity_x: float):
    """
    Updates the inlet velocity in the OpenFOAM U file by modifying the Uinlet variable.

    Args:
        case_dir_path: Path to the case directory.
        velocity_x: The x-component of the velocity for the inlet.
    """
    u_file_path = case_dir_path / "0.orig" / "U"
    if not u_file_path.exists():
        print(f"❌ Error: U file not found at {u_file_path}")
        return

    try:
        content = u_file_path.read_text()
        
        # Regex to find the Uinlet definition line, e.g., "Uinlet (10 0 0);"
        # It captures three groups:
        # 1. The part before the velocity values: "Uinlet          ("
        # 2. The velocity values themselves: "10 0 0"
        # 3. The part after the velocity values: ");"
        pattern = re.compile(
            r"^(Uinlet\s+\()([^)]+)(\);)",  # Matches "Uinlet (values);"
            re.MULTILINE  # ^ matches the beginning of a line
        )
        
        def replace_uinlet_velocity(match):
            # Reconstruct the line with the new velocity_x, keeping Y and Z as 0
            # match.group(1) is "Uinlet          ("
            # match.group(3) is ");"
            return f"{match.group(1)}{velocity_x} 0 0{match.group(3)}"

        new_content, num_replacements = pattern.subn(replace_uinlet_velocity, content)

        if num_replacements > 0:
            u_file_path.write_text(new_content)
            if "--suppress-output" not in sys.argv:
                print(f"💨 Uinlet variable updated to ({velocity_x} 0 0) in {u_file_path}")
        else:
            print(f"⚠️ Warning: Uinlet definition line not found or not updated in {u_file_path}.")
            print(f"   Searched for a line like 'Uinlet (...);'. Please check the U file format at {u_file_path}")
            print(f"   If the format is different, the script may not work as expected.")


    except Exception as e:
        print(f"❌ Failed to update Uinlet in {u_file_path}: {e}")
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
    angles = [0,45,135,180] # Example with more angles
    velocities = [5, 10, 15] # Example velocities in m/s
    base_geometry = Path("/mnt/c/Users/r.davenne/Documents/geometry/base_buildings.stl")
    base_case = Path("/home/rdavenne/OpenFOAM_cases/windAroundBuildings")
    output_dir = Path("/home/rdavenne/OpenFOAM_cases/test_dataset")
    # freecad_script = Path("rotate_stl.py") # Assuming this is in the same dir or PATH - This variable is not used
    slice_script = Path("utils_scripts/slice_and_export.py") # Assuming this path is correct relative to execution

    output_dir.mkdir(exist_ok=True)

    script_timings = {} # To store timings
    total_script_start_time = time.time() # Start general timer

    # Use tqdm for the loop, disable if output is suppressed to avoid tqdm printing
    for angle, velocity in tqdm(list(itertools.product(angles, velocities)), desc="Processing angle/velocity combinations", disable=suppress_subprocess_output):
        case_dir = output_dir / f"case_angle_{angle}_vel_{velocity}"
        case_geometry = case_dir / "constant/triSurface/buildings.stl"

        # Copy the base case
        if case_dir.exists():
            shutil.rmtree(case_dir)
        shutil.copytree(base_case, case_dir)

        # Update inlet velocity in the U file
        update_inlet_velocity(case_dir, velocity)

        rotate_path = Path("utils_scripts/rotate_stl.py").resolve()
        snappy_dict_path = case_dir / "system/snappyHexMeshDict"
        freecad_start_time = time.time() # Timer for FreeCAD
        geometry_center = None # Initialize variable to store center
        try:
            process_result = subprocess.run([
                "freecadcmd", str(rotate_path),
                str(base_geometry),
                str(case_geometry),
                str(angle),
                str(snappy_dict_path)
            ], check=True,
            capture_output=True, text=True # Capture output
            # stdout=None if not suppress_subprocess_output else subprocess.DEVNULL, # Will be replaced by capture_output
            # stderr=None if not suppress_subprocess_output else subprocess.DEVNULL # Will be replaced by capture_output
            )
            
            # Process stdout to find the geometry center
            if process_result.stdout:
                if not suppress_subprocess_output:
                    print(process_result.stdout) # Print FreeCAD output if not suppressed
                for line in process_result.stdout.splitlines():
                    if line.startswith("GEOMETRY_CENTER:"):
                        try:
                            coords_str = line.split(":")[1]
                            x, y, z = map(float, coords_str.split(','))
                            geometry_center = {"x": x, "y": y, "z": z}
                            if not suppress_subprocess_output:
                                print(f"Extracted geometry center: {geometry_center}")
                            break 
                        except Exception as e:
                            if not suppress_subprocess_output:
                                print(f"⚠️ Could not parse geometry center from line: {line} - Error: {e}")
            if process_result.stderr and not suppress_subprocess_output:
                print(process_result.stderr, file=sys.stderr)


        except subprocess.CalledProcessError as e:
            print(f"\\n❌ FreeCAD rotation failed for angle {angle}")
            print(f"Command: {e.cmd}")
            print(f"Exit code: {e.returncode}")
            if e.stdout: # Changed from e.output to e.stdout
                print("Stdout:\\n", e.stdout)
            if e.stderr: # Added stderr printing
                print("Stderr:\\n", e.stderr)
            sys.exit(1)

        freecad_end_time = time.time()
        script_timings[f"freecad_rotation_angle_{angle}_vel_{velocity}"] = freecad_end_time - freecad_start_time
        if geometry_center:
            script_timings[f"geometry_center_angle_{angle}_vel_{velocity}"] = geometry_center


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
        script_timings[f"openfoam_simulation_angle_{angle}_vel_{velocity}"] = openfoam_end_time - openfoam_start_time

        # Export slice with ParaView
        paraview_start_time = time.time() # Timer for ParaView
        subprocess.run([
            "pvpython", str(slice_script),
            str(case_dir / "case.foam"),
            str(case_dir / "slice.csv")
        ], check=True, stdout=subprocess.DEVNULL if suppress_subprocess_output else None, stderr=subprocess.DEVNULL if suppress_subprocess_output else None)
        paraview_end_time = time.time() # End timer for ParaView
        script_timings[f"paraview_slice_export_angle_{angle}_vel_{velocity}"] = paraview_end_time - paraview_start_time # Store ParaView timing

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
