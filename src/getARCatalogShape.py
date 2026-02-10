import netCDF4 as nc
import numpy as np
import matplotlib.pyplot as plt
from scipy import ndimage
from pyevtk.hl import imageToVTK, pointsToVTK
import os


def getARCatalogShape(nc_path, algo_name, year):
    """
    Convert the nc datafiles into individual shape files for each time step
    :param algo_name: algorithm folder name (excluding guan_waliser_v3)
    :param nc_path: path for the nc data (3 hourly data)
    :param year: 1980 - 2020
    :return: Saved into Algorithms/[algo_name]/ARCatalog/ARCatalog_[year]/shape/ARCatalog_[year]_shape_[day]_[time].vtu
    """
    nc_data = nc.Dataset(nc_path)
    time = nc_data['time'][:]
    outdata_dir = "Algorithms/" + algo_name + "/ARCatalog/ARCatalog_" + str(year) + "/shape/"
    os.makedirs(outdata_dir, exist_ok=True)

    for i, t in enumerate(time):
        print(t)
        if i % 2 == 0:
            day = i // 8
            print(day)
            hour = i % 8 // 2
            print(hour)
            AR_tag_t = nc_data['ar_binary_tag'][i, :, :]
            AR_tag_t = np.concatenate((AR_tag_t[:, 288:], AR_tag_t[:, :288]), axis=1)
            assert AR_tag_t.shape == (361, 576)
            # label ARs based on connected component
            labels, nb = ndimage.label(AR_tag_t.T)
            # plt.imshow(labels)
            # print(nb)
            # plt.imshow(AR_tag_t, interpolation='none')
            # plt.show()

            x = []
            y = []
            AR_id = []

            for i in range(AR_tag_t.T.shape[0]):
                for j in range(AR_tag_t.T.shape[1]):
                    if labels[i, j] > 0:
                        x.append(i)
                        y.append(j)
                        AR_id.append(labels[i, j])

            z = np.zeros(len(x), dtype=float)
            x = np.array(x, dtype=float)
            y = np.array(y, dtype=float)
            AR_id = np.array(AR_id, dtype=float)

            pointsToVTK(outdata_dir + "/ARCatalog_" + str(year) + "_shape_" + str(day) + "_" + str(hour),
                        x, y, z, data={"AR_shape": AR_id})


# teca_bard = nc.Dataset("Algorithms/teca_bard_v1.0.1/MERRA2.ar_tag.teca_bard_v1.0.1.3hourly.1996.nc4")
# ar_connect = nc.Dataset("Algorithms/ar_connect/MERRA2.ar_tag.ARCONNECT.3hourly.19960101-19961231.nc4")
# mundhenk = nc.Dataset("Algorithms/mundhenk_v3/MERRA2.ar_tag.Mundhenk_v3.3hourly.19960101-19961231.nc4")

# lat = teca_bard['lat'][:]
# lat = ar_connect['lat'][:]
# lat = mundhenk['lat'][:]
# print(lat)
# print(len(lat))
# print(np.min(lat))
# print(np.max(lat))
# lon = teca_bard['lon'][:]
# lon = ar_connect['lon'][:]
# lon = mundhenk['lon'][:]
# print(len(lon))
# print(lon[0])
# print(lon[575])
# print(lon[288])
# print(lon[287])
# print(lon[289])
# time = teca_bard['time'][:]
# time = ar_connect['time'][:]
# time = mundhenk['time'][:]
# print(len(time))
# print(time[:100])
# print(mundhenk['ar_binary_tag'][0].shape)
# t0 = mundhenk['ar_binary_tag'][0, :, :]
# t0_flipped = np.concatenate((t0[:, 288:], t0[:, :288]), axis=1)
# print(t0_flipped.shape)
# year = '1996'
# outdata_dir = "Algorithms/teca_bard_v1.0.1/ARCatalog/ARCatalog_" + year + "/shape/"
# outdata_dir = "Algorithms/ar_connect/ARCatalog/ARCatalog_" + year + "/shape/"
# outdata_dir = "Algorithms/mundhenk_v3/ARCatalog/ARCatalog_" + year + "/shape/"
# os.makedirs(outdata_dir, exist_ok=True)
# print(mundhenk['ar_binary_tag'][3240, :, :])

# for i, t in enumerate(time):
#     print(t)
#     if i % 2 == 0:
#         day = i // 8
#         print(day)
#         hour = i % 8 // 2
#         print(hour)
#         # AR_tag_t = teca_bard['ar_binary_tag'][i, :, :]
#         AR_tag_t = ar_connect['ar_binary_tag'][i, :, :]
#         # AR_tag_t = mundhenk['ar_binary_tag'][i, :, :]
#         AR_tag_t = np.concatenate((AR_tag_t[:, 288:], AR_tag_t[:, :288]), axis=1)
#         assert AR_tag_t.shape == (361, 576)
#         # label ARs based on connected component
#         labels, nb = ndimage.label(AR_tag_t.T)
#         # plt.imshow(labels)
#         # print(nb)
#         # plt.imshow(AR_tag_t, interpolation='none')
#         # plt.show()
#
#         x = []
#         y = []
#         AR_id = []
#
#         for i in range(AR_tag_t.T.shape[0]):
#             for j in range(AR_tag_t.T.shape[1]):
#                 if labels[i, j] > 0:
#                     x.append(i)
#                     y.append(j)
#                     AR_id.append(labels[i, j])
#
#         z = np.zeros(len(x), dtype=float)
#         x = np.array(x, dtype=float)
#         y = np.array(y, dtype=float)
#         AR_id = np.array(AR_id, dtype=float)
#
#
#         pointsToVTK(outdata_dir + "/ARCatalog_" + year + "_shape_" + str(day) + "_" + str(hour),
#                     x, y, z, data={"AR_shape": AR_id})
        # break


if __name__ == "__main__":
    # getARCatalogShape("Algorithms/ar_connect/MERRA2.ar_tag.ARCONNECT.3hourly.20060101-20061231.nc4", "ar_connect", 2006)
    # getARCatalogShape("Algorithms/climatenet/MERRA2.ar_tag.ClimateNet_DL_model.3hr.20140101-20141231.nc4", "climatenet", 2014)
    # getARCatalogShape("Algorithms/lora_v2/MERRA2.ar_tag.Lora_v2.3hourly.2014.nc4", "lora_v2", 2014)
    # getARCatalogShape("Algorithms/mundhenk_v3/MERRA2.ar_tag.Mundhenk_v3.3hourly.20140101-20141231.nc4", "mundhenk_v3", 2014)
    # getARCatalogShape("Algorithms/panlu/MERRA2.ar_tag.PanLu.3hourly.20140101-20141231.nc4", "panlu", 2014)
    # getARCatalogShape("Algorithms/reid500/MERRA2.ar_tag.Reid500.3hourly.20140101-20141231.nc4", "reid500", 2014)
    # getARCatalogShape("Algorithms/rutz/MERRA2.ar_tag.Rutz.3hourly.20140101-20141231.nc4", "rutz", 2014)
    # getARCatalogShape("Algorithms/sail_v1/MERRA2.ar_tag.SAIL_v1.3hourly.20140101-20141231.nc", "sail_v1", 2014)
    # getARCatalogShape("Algorithms/teca_bard_v1.0.1/MERRA2.ar_tag.teca_bard_v1.0.1.3hourly.2014.nc4", "teca_bard_v1.0.1", 2014)
    # getARCatalogShape("Algorithms/tempest_250/MERRA2.ar_tag.Tempest_v1.3hourly.2014.nc", "tempest_250", 2014)
    # getARCatalogShape("Algorithms/tempest_500/MERRA2.ar_tag.Tempest_v1.3hourly.2014.nc", "tempest_500", 2014)
    getARCatalogShape("Algorithms/tempest_700/MERRA2.ar_tag.Tempest_v1.3hourly.2014.nc", "tempest_700", 2014)
