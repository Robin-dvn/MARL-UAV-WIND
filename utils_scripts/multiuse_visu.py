import plotly.graph_objects as go
import numpy as np
from pathlib import Path

f = Path.cwd().joinpath("images")
if not f.is_dir(): f.mkdir()
f = f.joinpath("fig1.png")

fig = go.Figure(go.Scatter(x=np.linspace(1,10,100), y=np.sin(np.linspace(-np.pi,np.pi, 100))))

fig.write_image(f,format='png',engine='orca')