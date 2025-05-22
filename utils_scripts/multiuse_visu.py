import numpy as np
from pathlib import Path
from visualize_wind_map import plot_ux_uy

def show_saved_wind_data_heatmap(folder_path: str):
    """
    Charge les fichiers wind_data_ux_sim.npy et wind_data_uy_sim.npy dans le dossier donné,
    récupère l'angle depuis le JSON, puis affiche la heatmap avec plot_ux_uy (affichage interactif).
    """
    folder = Path(folder_path)
    ux_path = folder / "wind_data_ux_sim.npy"
    uy_path = folder / "wind_data_uy_sim.npy"
    json_path = folder / "wind_data_metadata.json"
    if not ux_path.exists() or not uy_path.exists():
        print(f"❌ Fichiers .npy non trouvés dans {folder_path}")
        return
    angle = 0.0
    if json_path.exists():
        try:
            import json
            with open(json_path, 'r') as f:
                meta = json.load(f)
                angle = float(meta.get("angle_deg", 0.0))
        except Exception as e:
            print(f"⚠️ Erreur lecture JSON: {e}")
    else:
        print(f"⚠️ Fichier {json_path} non trouvé, angle=0.0 utilisé.")
    ux = np.load(ux_path)
    uy = np.load(uy_path)
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    fig = make_subplots(rows=1, cols=2, subplot_titles=[f"Ux (θ={angle}°)", f"Uy (θ={angle}°)"])
    fig.add_trace(go.Heatmap(z=ux.T, colorscale="RdBu_r", colorbar=dict(title="Ux")), row=1, col=1)
    fig.add_trace(go.Heatmap(z=uy.T, colorscale="RdBu_r", colorbar=dict(title="Uy")), row=1, col=2)
    fig.update_layout(title_text=f"Vérification wind_data .npy (angle={angle}°)")
    fig.show()

if __name__ == "__main__":
    dossier = "/home/rdavenne/OpenFOAM_cases/test_dataset/dataset_processed/case_angle_10.85_vel_10.19" 
    show_saved_wind_data_heatmap(dossier)
