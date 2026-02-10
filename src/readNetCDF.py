import netCDF4 as nc
import numpy as np
from tvtk.api import tvtk, write_data
from mayavi import mlab

data = np.random.random((10,10,10))
print(data.shape)

grid = tvtk.ImageData(spacing=(10, 5, -10), origin=(100, 350, 200),
                      dimensions=data.shape)
data = np.ravel(data, order="F")
print(data.shape)
grid.point_data.scalars = np.ravel(data, order='F')
# print(grid.point_data.scalars.shape)
grid.point_data.scalars.name = 'Test Data'


def view(dataset):
    """ Open up a mayavi scene and display the dataset in it.
    """
    fig = mlab.figure(bgcolor=(1, 1, 1), fgcolor=(0, 0, 0), figure=dataset.class_name[3:])
    surf = mlab.pipeline.surface(dataset, opacity=1)
    mlab.pipeline.surface(mlab.pipeline.extract_edges(surf), color=(0, 0, 0), )

@mlab.show
def main():
    view(grid)

if __name__ == "__main__":
    main()

# Writes legacy ".vtk" format if filename ends with "vtk", otherwise
# this will write data using the newer xml-based format.
# write_data(grid, 'test.vtk')

# ivt_1992_net = nc.Dataset("MERRA2IVT/ivt_1992.nc")
# lat = ivt_1992_net['lat'][:]
# lon = ivt_1992_net['lon'][:]
# ens = ivt_1992_net['ens'][:]
# lev = ivt_1992_net['lev'][:]


# precipiData = Dataset("AnomPrecip_1979-2020.1in4.nc", "r+")
# print(precipiData.data_model)
# print(precipiData.variables.keys())
#
# for dim in precipiData.dimensions.values():
#     print(dim)
#
# print(precipiData.variables)
#
# for name in precipiData.ncattrs():
#     print(name)
#     print(getattr(precipiData, name))
#
# print(precipiData['longitude'].shape)
# print(precipiData['latitude'].shape)
# # print(precipiData[][:10])
# print(precipiData['ATP'].units)

# ivt_1992 = Dataset("MERRA2IVT/ivt_1992.nc", "r+")
# ivt_1992_classic = Dataset("MERRA2IVT/ivt_1992.nc", "w", format="NETCDF4_CLASSIC")
# print(ivt_1992.data_model)
# print(ivt_1992_classic.data_model)
#
# print(ivt_1992.variables.keys())
# print(ivt_1992['lon'].shape)
# print(ivt_1992['lev'].shape)
# print(ivt_1992['time'].shape)
# print(ivt_1992['ivtx'].shape)
# print(ivt_1992['ivty'].shape)

# ivt_1992 = xr.open_dataset("MERRA2IVT/ivt_1992.nc")
# print(ivt_1992)