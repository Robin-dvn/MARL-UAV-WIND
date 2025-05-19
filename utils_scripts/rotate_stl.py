import sys
import FreeCAD
import Mesh
from FreeCAD import Base

input_path = sys.argv[1]
output_path = sys.argv[2]
angle = float(sys.argv[3])

mesh = Mesh.Mesh(input_path)
rotation = Base.Rotation(Base.Vector(0, 0, 1), angle)
placement = Base.Placement()
placement.Rotation = rotation
mesh.Placement = placement
mesh.write(output_path)
