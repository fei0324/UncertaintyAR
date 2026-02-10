import netCDF4 as nc
import numpy as np
from pyevtk.hl import imageToVTK, pointsToVTK
import os


def getARVar(start_t, end_t, variable, AR_catalog, outdir):
    """
    Output AR variables in .vtu files
    :param start_t: start time computed from the year and day
    :param end_t: end time computed from the year and day
    :param variable: "shape", "axis", etc. Original arrays need to be numpy masked arrays.
    :param AR_catalog: AR catalog file
    :param outdir: output directory
    :return: .vtu files of the variable
    """

    year = outdir.split("/")[-2][-4:]
    # print(year)

    # 1992 time 17532 - 18995, from day 4383
    for t in range(start_t, end_t):
        # print(t)
        AR_shape_t = AR_catalog[variable][0, t, 0, :, :].T
        AR_mask_t = np.ma.getmask(AR_shape_t)
        # print(AR_mask_t.shape)

        x = []
        y = []
        AR_id = []

        for i in range(AR_shape_t.shape[0]):
            for j in range(AR_shape_t.shape[1]):
                if not AR_mask_t[i, j]:
                    x.append(i)
                    y.append(j)
                    AR_id.append(AR_shape_t[i, j])

        z = np.zeros(len(x), dtype=float)
        x = np.array(x, dtype=float)
        y = np.array(y, dtype=float)
        AR_id = np.array(AR_id, dtype=float)

        outfolder = outdir + variable + "/"
        os.makedirs(outfolder, exist_ok=True)
        day_0 = start_t / 4
        assert day_0.is_integer()
        day = int(t // 4 - day_0)
        hour = t % 4
        print(day, hour)

        outfile = outfolder + "ARCatalog_" + str(year) + "_" + variable + "_" + str(int(day)) + "_" + str(hour)
        # print(outfile)
        pointsToVTK(outfile, x, y, z, data={"AR_" + variable: AR_id})
        # break


if __name__ == "__main__":
    AR_catalog = nc.Dataset("ARCatalog/globalARcatalog_MERRA2_1980-2020_v3.0.nc")
    # getARShape(17532, 18996, AR_catalog, "ARCatalog/ARCatalog_1992/")

    # getARVar(23376, 24840, "shape", AR_catalog, "ARCatalog/ARCatalog_1996/")
    # getARVar(37988, 39448, "axis", AR_catalog, "Algorithms/guan_waliser_v3/ARCatalog/ARCatalog_2006/")
    # getARVar(54060, 55520, "shape", AR_catalog, "Algorithms/guan_waliser_v3/ARCatalog/ARCatalog_2017/")
    getARVar(49676, 51136, "shape", AR_catalog, "Algorithms/guan_waliser_v3/ARCatalog/ARCatalog_2014/")

    # print(AR_catalog['axis'][0, 0, 0, :].count())