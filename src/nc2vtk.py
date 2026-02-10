import netCDF4 as nc
import numpy as np
import vtk
import os


def createVF(xcnt, ycnt, ivtx_i, ivty_i):
    """Create the vector field for time step i of the ivt data"""

    ivtx = [ivtx_i.reshape(xcnt * ycnt, )]
    ivty = [ivty_i.reshape(xcnt * ycnt, )]

    vf = np.concatenate((ivtx, ivty), axis=0).T

    return vf


def createVtkPlane(vf, xcnt, ycnt, xmin, xmax, ymin, ymax):

    plane = vtk.vtkPlaneSource()
    plane.SetResolution(xcnt - 1, ycnt - 1)
    plane.SetOrigin([xmin, ymin, 0])
    # x axis (Point1)
    plane.SetPoint1([xmax, ymin, 0])
    # y axis (Point2)
    plane.SetPoint2([xmin, ymax, 0])
    plane.Update()

    vel = vtk.vtkFloatArray()
    vel.SetName("VTI")
    vel.SetNumberOfComponents(3)
    vel.SetNumberOfTuples(len(vf))

    mag = vtk.vtkFloatArray()
    mag.SetName("VTI_Magnitude")
    mag.SetNumberOfValues(len(vf))

    for i in range(len(vf)):
        vel.SetTuple3(i, vf[i][0], vf[i][1], 0)
        mag_val = np.sqrt(np.power(vf[i][0], 2) + np.power(vf[i][1], 2))
        mag.SetValue(i, mag_val)

    return plane, vel, mag


if __name__ == "__main__":
    ivt_1992 = nc.Dataset("MERRA2IVT/ivt_1992.nc", "r+")

    lat = ivt_1992['lat'][:]
    ycnt = len(lat)
    ymin = np.min(lat)
    ymax = np.max(lat)
    lon = ivt_1992['lon'][:]
    xcnt = len(lon)
    xmin = np.min(lon)
    xmax = np.max(lon)
    time = ivt_1992['time'][:]

    ivtx = ivt_1992['ivtx'][:]
    ivty = ivt_1992['ivty'][:]
    # print(ivtx)

    for i in range(len(time)):

        outdir = "MERRA2IVT/ivt1992/"
        os.makedirs(outdir, exist_ok=True)
        day = i // 4
        hour = i % 4
        print(day, hour)

        x_i = ivtx[0, i, 0, :, :]
        y_i = ivty[0, i, 0, :, :]

        vf = createVF(xcnt, ycnt, x_i, y_i)
        plane, vel, mag = createVtkPlane(vf, xcnt, ycnt, xmin, xmax, ymin, ymax)

        pointData = plane.GetOutput().GetPointData()
        pointData.SetVectors(vel)
        pointData.SetScalars(mag)
        # plane.GetOutput().GetPointData().SetVectors(vel)
        # plane.GetOutput
        # pointData = plane.GetOutput().GetPointData()

        writer = vtk.vtkXMLDataWriter()
        # writer = vtk.vtkXMLImageDataWriter()
        # outfile = outdir + "ivt1992_" + str(day) + "_" + str(hour) + ".vtp"
        outfile = "test.vtp"
        writer.SetFileName(outfile)
        writer.SetInputConnection(plane.GetOutputPort())
        writer.Write()
        break