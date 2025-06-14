import sys
import FreeCAD
import Mesh
from FreeCAD import Base
import math
from pathlib import Path
import re

def update_refinement_box(stl_path: Path, snappy_path: Path, margin=0.1, zmin=0.0, zmax=85):
    mesh = Mesh.Mesh(str(stl_path))
    bbox = mesh.BoundBox

    dx = bbox.XMax - bbox.XMin
    dy = bbox.YMax - bbox.YMin
    diag = math.sqrt(dx**2 + dy**2) * (1 + margin)

    cx = bbox.Center.x
    cy = bbox.Center.y

    xmin = int(cx - diag / 2)
    xmax = int(cx + diag / 2)
    ymin = int(cy - diag / 2)
    ymax = int(cy + diag / 2)

    box_string = f"""
    refinementBox
    {{
        type box;
        min ({xmin:.3f} {ymin:.3f} {zmin:.3f});
        max ({xmax:.3f} {ymax:.3f} {zmax:.3f});
    }}"""

    text = Path(snappy_path).read_text()
    # 1. Extraire bloc geometry { ... }
    pattern = r'refinementBox\s*\{[^}]*?(type\s+[^\n]*;)[^}]*?(min\s+[^\n]*;)[^}]*?(max\s+[^\n]*;)[^}]*?\}'
    updated_text = re.sub(pattern, box_string, text, count=1, flags=re.DOTALL)
    Path(snappy_path).write_text(updated_text)

    print(f"✅ refinementBox mise à jour avec une marge de {int(margin*100)}%.")


# === Lecture des arguments ===


input_path = Path(sys.argv[2])
output_path = Path(sys.argv[3])
angle = float(sys.argv[4])
snappy_path = Path(sys.argv[5])

print(f"🔁 Rotation de {angle}° appliquée à {input_path}")
print(f"📦 STL sauvegardé dans {output_path}")

# Créer le dossier de sortie si nécessaire
output_path.parent.mkdir(parents=True, exist_ok=True)
print("arguments : ", input_path, output_path, angle, snappy_path)
# Charger le mesh
mesh = Mesh.Mesh(str(input_path))
print("✅ STL chargé.")
# Calcul du centre du mesh (bounding box)
bbox = mesh.BoundBox
center_2d_for_rotation = Base.Vector(
    (bbox.XMin + bbox.XMax) / 2,
    (bbox.YMin + bbox.YMax) / 2,
    0    
)
# Calculer et imprimer le centre 3D réel de la bounding box
actual_center_3d = bbox.Center
print(f"GEOMETRY_CENTER:{actual_center_3d.x},{actual_center_3d.y},{actual_center_3d.z}")

pos = Base.Vector(
    0, 0, 0
)
print("📍 Centre du mesh (pour rotation Z) :", center_2d_for_rotation)

# Définir la rotation autour de Z
rotation = Base.Rotation(Base.Vector(0, 0, 1), angle)

# Appliquer la rotation autour du centre (rotation sur place)
placement = Base.Placement(pos,rotation,center_2d_for_rotation) # Utilise le centre 2D pour la rotation Z
mesh.Placement = placement

print("✅ Rotation sur place appliquée.")

print("✅ Rotation appliquée.")
# Sauvegarder
mesh.write(str(output_path))
print("✅ STL sauvegardé.")
# Mettre à jour la refinementBox
update_refinement_box(output_path, snappy_path)

