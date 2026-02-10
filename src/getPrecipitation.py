import netCDF4 as nc
import numpy as np
from pyevtk.hl import imageToVTK
import os


def getPrecipitationSum2006(inputpath_1, inputpath_2, start_day_num, variable, outdir, lon_dim=576, lat_dim=361):
    """
    Get 24 hour sum precipitation data in 2006.
    :param inputdir: input path of the precipitation file
    :param variable: 'PRECTOT' or 'PRECTOTCORR'
    :return:
    """
    precip_data_1 = nc.Dataset(inputpath_1, "r+")
    precip_data_2 = nc.Dataset(inputpath_2, "r+")
    rain_data_1 = precip_data_1[variable]
    rain_data_2 = precip_data_2[variable]
    rain_all = np.concatenate((rain_data_1, rain_data_2))
    rain_start = rain_all[::6]
    print(rain_start.shape)

    nx, ny, nz = lon_dim, lat_dim, 1

    for i in range(len(rain_start) - 4):
        os.makedirs(outdir, exist_ok=True)
        rain_sum = np.zeros(rain_start[i].shape)
        for j in range(i * 6, i * 6 + 24):
            rain_sum = np.add(rain_sum, rain_all[j])
        # print(rain_sum)
        print(rain_sum.shape)
        rain_i = rain_sum.T.reshape((nx, ny, nz))
        print(rain_i.shape)
        # regrid from 0 - 360 to -180 - 180
        rain_i_left = rain_i[:lon_dim // 2, :, :]
        rain_i_right = rain_i[lon_dim // 2:, :, :]
        rain_i_translate = np.concatenate((rain_i_right, rain_i_left))
        print(rain_i_translate.shape)

        day = start_day_num + i//4
        hour = i % 4
        print(day, hour)

        outfile = outdir + "precipitation_2006" + "_" + str(day) + "_" + str(hour)
        imageToVTK(outfile, pointData={"precipitation": rain_i_translate})


def getPrecipitationSum(inputdir, num_hours, lat_dim, lon_dim, outdir):
    """
    Convert MERRA2 precipitation .nc files into .vti files, get the sum of precipitation 24 hours after the initial time
    :param inputdir: .nc file
    :param outdir: output directory
    :return: .vti files of precipitation data
    """

    # year = inputdir.split("/")[1].split("_")[1][:4]
    # print(year)
    precip_data = nc.Dataset(inputdir, "r+")
    # get every 6th hour
    rain_start = precip_data['rain_hr'][::6]
    # print(len(rain_start))

    # 12/01/1996 is day 335
    # 12/31/1996 is day 365
    nx, ny, nz = lon_dim, lat_dim, 1
    for i in range(len(rain_start) - 4):
        os.makedirs(outdir, exist_ok=True)
        rain_sum = np.zeros(rain_start[i].shape)
        for j in range(i*6, i*6+num_hours):
            rain_sum = np.add(rain_sum, precip_data['rain_hr'][j])
        # print(rain_sum)
        rain_i = rain_sum.T.reshape((nx, ny, nz))
        print(rain_i.shape)
        # regrid from 0 - 360 to -180 - 180
        rain_i_left = rain_i[:lon_dim//2, :, :]
        rain_i_right = rain_i[lon_dim//2:, :, :]
        rain_i_translate = np.concatenate((rain_i_right, rain_i_left))

        hour = i % 4
        if i < 124:
            year = 1996
            day = 335 + i//4
        else:
            year = 1997
            day = i//4 - 124//4

        print(year, day, hour)

        outfile = outdir + "precipitation_" + str(year) + "_" + str(day) + "_" + str(hour)
        imageToVTK(outfile, pointData={"precipitation": rain_i_translate})


def getPrecipitation(inputdir, lat_dim, lon_dim, outdir):
    """
    Convert MERRA2 precipitation .nc files into .vti files, get every 6th hour since the data is hourly
    :param inputdir: .nc file
    :param outdir: output directory
    :return: .vti files of precipitation data
    """

    # year = inputdir.split("/")[1].split("_")[1][:4]
    # print(year)
    precip_data = nc.Dataset(inputdir, "r+")
    # get every 6th hour
    rain = precip_data['rain_hr'][::6]
    print(len(rain))
    print(rain.shape)

    # 12/01/1996 is day 335
    # 12/31/1996 is day 365
    nx, ny, nz = lon_dim, lat_dim, 1
    for i in range(len(rain)):
        os.makedirs(outdir, exist_ok=True)
        rain_i = rain[i, :, :].T.reshape((nx, ny, nz))
        print(rain_i.shape)
        # regrid from 0 - 360 to -180 - 180
        rain_i_left = rain_i[:lon_dim//2, :, :]
        rain_i_right = rain_i[lon_dim//2:, :, :]
        rain_i_translate = np.concatenate((rain_i_right, rain_i_left))

        hour = i % 4
        if i < 124:
            year = 1996
            day = 335 + i//4
        else:
            year = 1997
            day = i//4 - 124//4

        print(year, day, hour)

        outfile = outdir + "precipitation_" + str(year) + "_" + str(day) + "_" + str(hour)
        # imageToVTK(outfile, pointData={"precipitation": rain_i_translate})

    # lat = ivt_data['lat'][:]
    # lon = ivt_data['lon'][:]
    # time = ivt_data['time'][:]

    # ivtx = ivt_data['ivtx'][:]
    # ivty = ivt_data['ivty'][:]
    #
    # nx, ny, nz = len(lon), len(lat), 1
    #
    # for i in range(len(time)):
    #
    #     os.makedirs(outdir, exist_ok=True)
    #     day = i // 4
    #     hour = i % 4
    #     print(day, hour)
    #
    #     x_i = ivtx[0, i, 0, :, :].T.reshape((nx, ny, nz))
    #     y_i = ivty[0, i, 0, :, :].T.reshape(nx, ny, nz)
    #     ivt_mag_i = np.sqrt(np.power(x_i, 2) + np.power(y_i, 2))
    #
    #     outfile = outdir + "ivt_" + year + "_" + str(day) + "_" + str(hour)
    #
    #     imageToVTK(outfile, pointData={"ivt_x": x_i, "ivt_y": y_i, "ivt_magnitude": ivt_mag_i})


if __name__ == "__main__":
    # getPrecipitation("MERRA2Precipitation/MERRA2_Tot_rain_hrly_96_97.nc", 361, 576, "MERRA2Precipitation/Precipitation1996Dec1997Jan/")
    # getPrecipitationSum("MERRA2Precipitation/MERRA2_Tot_rain_hrly_96_97.nc", 24, 361, 576, "MERRA2Precipitation/Precipitation24hrAfterSum/")
    # ivt_1996 = nc.Dataset("MERRA2IVT/ivt_1996.nc", "r+")

    precip_1 = "MERRA2Precipitation/MERRA2_300.tavg1_2d_flx_Nx.20061103.SUB.nc"
    precip_2 = "MERRA2Precipitation/MERRA2_300.tavg1_2d_flx_Nx.20061104.SUB.nc"
    getPrecipitationSum2006(precip_1, precip_2, 308, 'PRECTOT', "MERRA2Precipitation/Precipitation24hrAfterSum2006/")