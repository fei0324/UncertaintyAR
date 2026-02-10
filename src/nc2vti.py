import netCDF4 as nc
import numpy as np
from pyevtk.hl import imageToVTK
import os

def nc2vti(inputdir, outdir):
    """
    Convert MERRA2 IVT .nc files into .vti files
    :param inputdir: .nc file
    :param outdir: output directory
    :return: .vti files of IVT data
    """

    year = inputdir.split("/")[1].split("_")[1][:4]
    print(year)
    ivt_data = nc.Dataset(inputdir, "r+")
    lat = ivt_data['lat'][:]
    lon = ivt_data['lon'][:]
    time = ivt_data['time'][:]

    ivtx = ivt_data['ivtx'][:]
    ivty = ivt_data['ivty'][:]

    nx, ny, nz = len(lon), len(lat), 1

    for i in range(len(time)):

        os.makedirs(outdir, exist_ok=True)
        day = i // 4
        hour = i % 4
        print(day, hour)

        x_i = ivtx[0, i, 0, :, :].T.reshape((nx, ny, nz))
        y_i = ivty[0, i, 0, :, :].T.reshape((nx, ny, nz))
        ivt_mag_i = np.sqrt(np.power(x_i, 2) + np.power(y_i, 2))

        outfile = outdir + "ivt_" + year + "_" + str(day) + "_" + str(hour)

        imageToVTK(outfile, pointData={"ivt_x": x_i, "ivt_y": y_i, "ivt_magnitude": ivt_mag_i})


if __name__ == "__main__":
    nc2vti("MERRA2IVT/ivt_2014.nc", "MERRA2IVT/ivt_2014/")
    # ivt_1996 = nc.Dataset("MERRA2IVT/ivt_1996.nc", "r+")