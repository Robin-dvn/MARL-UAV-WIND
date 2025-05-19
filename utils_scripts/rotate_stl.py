import sys
import FreeCAD
import Mesh
from FreeCAD import Base
from pathlib import Path

"""
This script rotates an STL mesh around the Z-axis using FreeCAD's command-line interface.

It takes three command-line arguments:
1.  The path to the input STL file.
2.  The path where the rotated STL file will be saved.
3.  The rotation angle in degrees.

The script loads the mesh, applies the specified rotation, and saves the modified mesh
to the output path. It also ensures that the output directory exists before saving.
"""

input_path = sys.argv[2]
output_path = Path(sys.argv[3])
angle = float(sys.argv[4])
print(f"Rotation of {angle}° applied to {input_path} and saved to {output_path}")
# Create parent directories if necessary
output_path.parent.mkdir(parents=True, exist_ok=True)

# Load and apply rotation
mesh = Mesh.Mesh(str(input_path))
rotation = Base.Rotation(Base.Vector(0, 0, 1), angle)
placement = Base.Placement()
placement.Rotation = rotation
mesh.Placement = placement
mesh.write(str(output_path))
