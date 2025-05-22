import pandas as pd
import numpy as np
from scipy.interpolate import griddata, interpn
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys # Added import for sys

def load_and_interpolate(csv_path: Path, grid_shape=(2000, 2000)):
    df = pd.read_csv(csv_path)
    df = df.rename(columns={'Points:0': 'x', 'Points:1': 'y', 'U:0': 'ux'})
    if 'U:1' in df.columns:
        df = df.rename(columns={'U:1': 'uy'})
    else:
        df['uy'] = 0.0

    x_vec = np.linspace(df.x.min(), df.x.max(), grid_shape[0])
    y_vec = np.linspace(df.y.min(), df.y.max(), grid_shape[1])
    x_mesh, y_mesh = np.meshgrid(x_vec, y_vec, indexing='ij')

    ux_grid = griddata(df[['x', 'y']].values, df['ux'].values, (x_mesh, y_mesh), method='linear')
    uy_grid = griddata(df[['x', 'y']].values, df['uy'].values, (x_mesh, y_mesh), method='linear')

    return x_vec, y_vec, ux_grid, uy_grid

def extract_rotated_crop(x_vec, y_vec, ux, uy, center, crop_size, angle_deg, output_res=(2000, 2000)):
    cx, cy = center
    w, h = crop_size
    Nx, Ny = output_res

    # grille dans le repère tourné (ville fixe)
    x_rel = np.linspace(-w/2, w/2, Nx)
    y_rel = np.linspace(-h/2, h/2, Ny)
    x_grid, y_grid = np.meshgrid(x_rel, y_rel, indexing='ij')

    theta = np.deg2rad(angle_deg)
    cos_t, sin_t = np.cos(theta), np.sin(theta)

    # coordonnées dans le repère global
    x_rot = cos_t * x_grid - sin_t * y_grid + cx
    y_rot = sin_t * x_grid + cos_t * y_grid + cy

    pts_interp = np.stack([x_rot.ravel(), y_rot.ravel()], axis=-1)

    ux_crop = interpn((x_vec, y_vec), ux, pts_interp, method='linear', bounds_error=False, fill_value=np.nan)
    uy_crop = interpn((x_vec, y_vec), uy, pts_interp, method='linear', bounds_error=False, fill_value=np.nan)

    return ux_crop.reshape(Nx, Ny), uy_crop.reshape(Nx, Ny)

def plot_ux_uy(ux_crop, uy_crop, angle_deg, save_path=None): # Added save_path parameter
    fig = make_subplots(rows=1, cols=2, subplot_titles=[f"Ux (θ={angle_deg}°)", f"Uy (θ={angle_deg}°)"])

    fig.add_trace(go.Heatmap(z=ux_crop.T, colorscale="RdBu_r", colorbar=dict(title="Ux")), row=1, col=1)
    fig.add_trace(go.Heatmap(z=uy_crop.T, colorscale="RdBu_r", colorbar=dict(title="Uy")), row=1, col=2)

    fig.update_layout(title_text=f"Vent vu depuis la ville (référentiel fixe, angle={angle_deg}°)" ) # Updated title
    img_bytes = fig.to_image(format="png", width=800, height=600)

    # Écrire l’image sur disque manuellement
    with open(save_path, "wb") as f:
        f.write(img_bytes)

    print("✅ Image sauvegardée via to_image()")

def export_simulated_data_arrays(ux_crop: np.ndarray, uy_crop: np.ndarray, save_prefix_path: Path):
    """
    Saves the cropped simulated Ux and Uy data arrays as .npy files.
    No logging or extensive error handling.
    """
    np.save(f"{str(save_prefix_path)}_ux_sim.npy", ux_crop)
    np.save(f"{str(save_prefix_path)}_uy_sim.npy", uy_crop)

def export_incident_data_arrays(base_velocity: float, angle_deg: float, output_resolution: tuple[int, int], save_prefix_path: Path):
    """
    Calculates and saves uniform incident Ux and Uy data arrays (relative to geometry) as .npy files.
    No logging or extensive error handling.
    """
    theta_rad = np.deg2rad(angle_deg)
    
    # Incident wind vector in global frame is (base_velocity, 0)
    # Geometry's x-axis direction: (cos(theta), sin(theta))
    # Geometry's y-axis direction: (-sin(theta), cos(theta))
    # Ux_incident_local = V_global . geometry_x_axis
    # Uy_incident_local = V_global . geometry_y_axis
    
    ux_incident_component = base_velocity * np.cos(theta_rad)
    uy_incident_component = -base_velocity * np.sin(theta_rad) # Wind from X, so Uy relative to geometry is -V*sin(theta)

    incident_ux_array = np.full(output_resolution, ux_incident_component, dtype=np.float16)
    incident_uy_array = np.full(output_resolution, uy_incident_component, dtype=np.float16)

    np.save(f"{str(save_prefix_path)}_ux_incident.npy", incident_ux_array)
    np.save(f"{str(save_prefix_path)}_uy_incident.npy", incident_uy_array)

# --- Exemple d'utilisation ---
if __name__ == "__main__":
    csv_path = Path("assets/wind_map/ux.csv")
    x_vec, y_vec, ux, uy = load_and_interpolate(csv_path)

    center = (100.0, 0.0)        # centre de la ville
    crop_size = (230.0, 230.0)  # taille du domaine autour de la ville
    angle = 0.0               # rotation de la ville

    ux_crop, uy_crop = extract_rotated_crop(x_vec, y_vec, ux, uy, center, crop_size, angle)
    plot_ux_uy(ux_crop, uy_crop, angle,"./image.png")
