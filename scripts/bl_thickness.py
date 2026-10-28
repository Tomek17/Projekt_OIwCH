"""Estimate the suction-side boundary-layer extent from a SU2 flow.vtu: distance from the wall where the eddy
viscosity drops below 1 % of its maximum, along vertical lines at several x/c (upper surface).

Usage (in the image): python scripts/bl_thickness.py runs/<exp>/<case>/flow.vtu
Status: written for F4g diagnosis, run once on naca0012_gci5_a10 xxfine. Vertical lines approximate the wall
normal only on the aft part of the airfoil (small surface slope).
"""
import sys, numpy as np, vtk
from vtk.util.numpy_support import vtk_to_numpy as v2n
r = vtk.vtkXMLUnstructuredGridReader(); r.SetFileName(sys.argv[1]); r.Update()
g = r.GetOutput(); P = v2n(g.GetPoints().GetData())[:, :2]
pd = g.GetPointData()
names = [pd.GetArrayName(i) for i in range(pd.GetNumberOfArrays())]
mu_t = v2n(pd.GetArray("Eddy_Viscosity"))
for x0 in (0.5, 0.8, 0.9, 0.95, 0.99):
    m = (np.abs(P[:, 0] - x0) < 0.002) & (P[:, 1] > 0) & (P[:, 1] < 0.3)
    y = P[m, 1]; mt = mu_t[m]; o = np.argsort(y); y, mt = y[o], mt[o]
    ys = y[0]; i = np.argmax(mt); edge = y[i:][mt[i:] < 0.01 * mt[i]]
    d = (edge[0] - ys) if len(edge) else float("nan")
    print(f"x={x0}: wall y={ys:.4f}, max mu_t at dy={y[i]-ys:.4f}, mu_t<1% of max at dy={d:.4f}")
