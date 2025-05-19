import sys
from paraview.simple import *

"""
This script uses ParaView (pvpython) to create a slice from an OpenFOAM simulation case
and export it as a CSV file.

It takes two command-line arguments:
1.  `case_path`: The path to the OpenFOAM case file (e.g., case.foam).
2.  `csv_path`: The path where the resulting CSV data will be saved.

The script reads the specified mesh regions and cell arrays (specifically 'U' for velocity),
creates a horizontal slice at Z=20.0, and then saves the data from this slice.
"""

case_path = sys.argv[1]
csv_path = sys.argv[2]

case = OpenFOAMReader(FileName=case_path)
case.MeshRegions = ['internalMesh']
case.CellArrays = ['U']

slice1 = Slice(Input=case)
slice1.SliceType = 'Plane'
slice1.SliceType.Origin = [0.0, 0.0, 20.0]
slice1.SliceType.Normal = [0.0, 0.0, 1.0]

SaveData(csv_path, proxy=slice1, WriteTimeSteps=0)
