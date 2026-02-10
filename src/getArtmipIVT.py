import netCDF4 as nc
import numpy as np
from pyevtk.hl import imageToVTK
import os


def getArtmipIVT(inputdir, outdir):

    year = inputdir.split(".")[0].split("_")[-1]
    print(year)
    ivt_data = nc.Dataset(inputdir, "r+")
    lat = ivt_data['lat'][:]
    lon = ivt_data['lon'][:]  # -180 to 180, convert to 0 to 360

    ivtx = ivt_data['uIVT'][:]
    ivty = ivt_data['vIVT'][:]

    time_len = ivtx.shape[0]

    nx, ny, nz = len(lon), len(lat), 1
    os.makedirs(outdir, exist_ok=True)

    for t in range(time_len):
        if t % 2 == 0:
            print(t)
            day = t // 8
            hour = (t % 8) // 2
            print(day, hour)

            x_i = ivtx[t, :, :].T.reshape((nx, ny, nz))
            y_i = ivty[t, :, :].T.reshape((nx, ny, nz))
            ivt_mag_i = np.sqrt(np.power(x_i, 2) + np.power(y_i, 2))
            ivt_mag_i = np.concatenate((ivt_mag_i[288:, :, :], ivt_mag_i[:288, :, :]), axis=0)
            outfile = outdir + "ivt_" + year + "_" + str(day) + "_" + str(hour)

            imageToVTK(outfile, pointData={"ivt_x": x_i, "ivt_y": y_i, "ivt_magnitude": ivt_mag_i})


if __name__ == "__main__":
    getArtmipIVT("MERRA2IVT/ARTMIP_MERRA_2D_2017.nc", "MERRA2IVT/ivt_2017/")