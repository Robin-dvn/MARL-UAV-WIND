import sys
import FreeCAD
import Mesh
from FreeCAD import Base
from pathlib import Path

input_path = sys.argv[2]
output_path = Path(sys.argv[3])
angle = float(sys.argv[4])
print(f"Rotation de {angle}° appliquée à {input_path} et enregistrée dans {output_path}")
# Créer les dossiers parents si nécessaire
output_path.parent.mkdir(parents=True, exist_ok=True)

# Charger et appliquer la rotation
mesh = Mesh.Mesh(str(input_path))
rotation = Base.Rotation(Base.Vector(0, 0, 1), angle)
placement = Base.Placement()
placement.Rotation = rotation
mesh.Placement = placement
mesh.write(str(output_path))
