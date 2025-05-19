import pandas as pd
import numpy as np
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from scipy.interpolate import griddata
from pathlib import Path

# Fonction pour charger et interpoler un CSV
def load_and_interpolate(csv_path):
    df = pd.read_csv(Path(csv_path))
    df = df.rename(columns={'Points:0': 'x', 'Points:1': 'y', 'U:0': 'ux'})
    points = df[['x', 'y']].values
    ux = df['ux'].values
    grid_x, grid_y = np.mgrid[
        df['x'].min():df['x'].max():300j,
        df['y'].min():df['y'].max():300j
    ]
    grid_ux = griddata(points, ux, (grid_x, grid_y), method='linear')
    return grid_ux

# Charger et interpoler les deux CSV
ux1 = load_and_interpolate('assets/wind_map/ux.csv')
ux2 = load_and_interpolate(r'\\wsl.localhost\Ubuntu\home\rdavenne\OpenFOAM_cases\test_dataset\case_90\slice.csv')

# Créer la figure avec deux sous-graphes
fig = make_subplots(rows=1, cols=2, subplot_titles=["Ux - ux.csv", "Ux - ux2.csv"])

# Ajout de la première image
fig.add_trace(
    go.Heatmap(
        z=ux1.T,
        colorscale=px.colors.diverging.RdBu[::-1],
        colorbar=dict(title="Ux"),
        zsmooth="best"
    ),
    row=1, col=1
)

# Ajout de la deuxième image
fig.add_trace(
    go.Heatmap(
        z=ux2.T,
        colorscale=px.colors.diverging.RdBu[::-1],
        showscale=False,
        zsmooth="best"
    ),
    row=1, col=2
)

fig.update_layout(
    title="Champs interpolés de Ux (ux.csv à gauche, ux2.csv à droite)",
    xaxis_title="x", yaxis_title="y"
)
fig.show()
