import sys
from paraview.simple import *

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
