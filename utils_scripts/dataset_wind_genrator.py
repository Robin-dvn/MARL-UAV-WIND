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
import random # Added import for random number generation

from visualize_wind_map import load_and_interpolate, extract_rotated_crop, export_simulated_data_arrays, export_incident_data_arrays , plot_ux_uy # plot_ux_uy commented out

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
    # angles = [45,0,5,7,90,98,178,270] # Example with more angles - Replaced by random generation
    # velocities = [15] # Example velocities in m/s - Replaced by random generation
    nb_couples = 10  # Number of angle-velocity pairs to generate
    velocity_min_mps = 5.0  # Minimum velocity in m/s
    velocity_max_mps = 25.0 # Maximum velocity in m/s
    angle_min_deg = 0.0     # Minimum angle in degrees
    angle_max_deg = 360.0   # Maximum angle in degrees (exclusive for random.uniform, but 360 is fine for full circle)

    base_geometry = Path("/mnt/c/Users/r.davenne/Documents/geometry/base_buildings.stl")
    base_case = Path("/home/rdavenne/OpenFOAM_cases/windAroundBuildings")
    output_dir = Path("/home/rdavenne/OpenFOAM_cases/test_dataset")
    # freecad_script = Path("rotate_stl.py") # Assuming this is in the same dir or PATH - This variable is not used
    slice_script = Path("utils_scripts/slice_and_export.py") # Assuming this path is correct relative to execution
    # visualization_output_dir = output_dir / "visualizations" # Directory for saving plots - Replaced by dataset_processed_dir
    dataset_processed_dir = output_dir / "dataset_processed" # New directory for structured dataset
    crop_size_visualization = (230.0, 230.0)  # Taille du domaine autour de la ville pour la visualisation
    output_resolution_visualization = (2000, 2000) # Résolution de l'image de visualisation

    output_dir.mkdir(exist_ok=True)
    # visualization_output_dir.mkdir(exist_ok=True) # Create visualization directory - Replaced
    dataset_processed_dir.mkdir(exist_ok=True) # Create processed dataset directory

    script_timings = {} # To store timings
    total_script_start_time = time.time() # Start general timer

    # Generate angle-velocity pairs
    angle_velocity_pairs = []
    for _ in range(nb_couples):
        angle = random.uniform(angle_min_deg, angle_max_deg)
        velocity = random.uniform(velocity_min_mps, velocity_max_mps)
        angle_velocity_pairs.append((angle, velocity))

    # Use tqdm for the loop, disable if output is suppressed to avoid tqdm printing
    # for angle, velocity in tqdm(list(itertools.product(angles, velocities)), desc="Processing angle/velocity combinations", disable=suppress_subprocess_output):
    for angle, velocity in tqdm(angle_velocity_pairs, desc="Processing angle/velocity combinations", disable=suppress_subprocess_output):
        # Round angle and velocity for directory naming to avoid overly long/precise float names
        # You can adjust the precision as needed
        angle_for_naming = round(angle, 2)
        velocity_for_naming = round(velocity, 2)

        case_dir = output_dir / f"case_angle_{angle_for_naming}_vel_{velocity_for_naming}"
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
        csv_slice_path = case_dir / "slice.csv"
        subprocess.run([
            "pvpython", str(slice_script),
            str(case_dir / "case.foam"),
            str(csv_slice_path) # Use variable for csv path
        ], check=True, stdout=subprocess.DEVNULL if suppress_subprocess_output else None, stderr=subprocess.DEVNULL if suppress_subprocess_output else None)
        paraview_end_time = time.time() # End timer for ParaView
        script_timings[f"paraview_slice_export_angle_{angle}_vel_{velocity}"] = paraview_end_time - paraview_start_time # Store ParaView timing

        # Generate and save wind map visualization
        if geometry_center and csv_slice_path.exists():
            if not suppress_subprocess_output:
                print(f"🔄 Generating visualization for angle {angle}, velocity {velocity}...")
            try:
                x_vec, y_vec, ux_grid, uy_grid = load_and_interpolate(csv_slice_path)
                # Utiliser les coordonnées x, y du centre extraites (ignorer z pour la 2D)
                center_2d_visualization = (geometry_center['x'], geometry_center['y'])
                
                ux_crop, uy_crop = extract_rotated_crop(
                    x_vec, y_vec, 
                    ux_grid, uy_grid, 
                    center_2d_visualization, 
                    crop_size_visualization, 
                    angle, # Utiliser l\'angle de rotation actuel de la géométrie
                    output_res=output_resolution_visualization
                )
                
                # Define the case-specific directory and ensure it exists
                case_specific_dir = dataset_processed_dir / f"case_angle_{angle_for_naming}_vel_{velocity_for_naming}"
                case_specific_dir.mkdir(parents=True, exist_ok=True)

                # Define the prefix for the output files within the case-specific directory
                save_prefix_path = case_specific_dir / "wind_data"
                
                plot_ux_uy(
                    ux_crop, uy_crop, angle,
                    save_path=str(save_prefix_path)+"_visu.png" # Save the plot as a PNG
                ) # Commented out as per discussion, focus on .npy and .json for dataset

                # Export simulated wind data arrays (Ux_sim, Uy_sim)
                export_simulated_data_arrays(
                    ux_crop=ux_crop,
                    uy_crop=uy_crop,
                    save_prefix_path=save_prefix_path 
                )

                # Export incident wind data arrays (Ux_incident, Uy_incident)
                export_incident_data_arrays(
                    base_velocity=float(velocity), 
                    angle_deg=float(angle),
                    output_resolution=output_resolution_visualization,
                    save_prefix_path=save_prefix_path
                )

                # Save metadata (angle and velocity) to a JSON file
                # Use the original, non-rounded angle and velocity for metadata accuracy
                metadata = {"angle_deg": float(angle), "velocity_mps": float(velocity)}
                metadata_save_path = Path(f"{str(save_prefix_path)}_metadata.json") # Path will be case_specific_dir / "wind_data_metadata.json"
                with open(metadata_save_path, 'w') as f_meta:
                    json.dump(metadata, f_meta, indent=4)

                if not suppress_subprocess_output:
                    print(f"✅ Successfully saved 4 data arrays and 1 metadata JSON for angle {angle}, velocity {velocity} to {case_specific_dir}")
            except Exception as e:
                if not suppress_subprocess_output:
                    print(f"❌ Failed to save one or more data arrays for angle {angle}, velocity {velocity}: {e}")
        elif not geometry_center and not suppress_subprocess_output:
            print(f"⚠️ Skipping visualization for angle {angle}, velocity {velocity} due to missing geometry center.")
        elif not csv_slice_path.exists() and not suppress_subprocess_output:
            print(f"⚠️ Skipping visualization for angle {angle}, velocity {velocity} due to missing CSV slice file: {csv_slice_path}")

                # Clean up the case directory to save space
        if case_dir.exists():
            if not suppress_subprocess_output:
                print(f"🧹 Cleaning up case directory: {case_dir}")
            try:
                shutil.rmtree(case_dir)
                if not suppress_subprocess_output:
                    print(f"✅ Successfully removed {case_dir}")
            except Exception as e:
                if not suppress_subprocess_output:
                    print(f"❌ Failed to remove {case_dir}: {e}")
        elif not suppress_subprocess_output:
            print(f"ℹ️ Case directory {case_dir} not found for cleanup (already removed or never created).")
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
