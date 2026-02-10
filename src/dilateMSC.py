import matplotlib.pyplot as plt
from shapely.geometry import LineString, Point, asMultiPoint, Polygon
from shapely.prepared import prep
# from descartes import PolygonPatch
import numpy as np
import vtk
import vtk.util.numpy_support as VN
import alphashape
import sys


def getPrecipPercent(axis_i, buffer_param, alpha_shape_i, precip):
    """
    Compute a percentage that represents the amount of precipitation characterized by the AR axis
    :param axis_i: AR axis loaded from the .npy file
    :param buffer_param: thickening parameter for the AR axis
    :param precip: output read from the input precipitation file
    :param alpha_shape_i: the alpha shape of AR read from the .npy file
    :return:
    """
    axis_i_line = LineString(axis_i)
    dilated_axis = axis_i_line.buffer(buffer_param, cap_style=3)
    alpha_shape_polygon = Polygon(alpha_shape_i)
    precip_vals = VN.vtk_to_numpy(precip.GetPointData().GetArray("precipitation"))

    captured_precip = 0
    total_precip = 0

    num_points = precip.GetNumberOfPoints()

    for i in range(num_points):
        precip_point = precip.GetPoint(i)
        pt = Point(precip_point[0], precip_point[1])
        if alpha_shape_polygon.contains(pt):
            total_precip += precip_vals[i]
        if dilated_axis.contains(pt):
            captured_precip += precip_vals[i]

    return captured_precip/total_precip


def orderCatalogAxisPoints(catalog_axis_i):
    # TODO: need to find where the axis starts and ends
    plt.scatter(*zip(*catalog_axis_i))
    # print(catalog_axis_i)
    catalog_axis_i = list(map(tuple, catalog_axis_i))
    # print(catalog_axis_i)
    p_previous, previous, current = catalog_axis_i[0], catalog_axis_i[0], catalog_axis_i[0]
    current_x, current_y = current[0], current[1]
    top = (current_x, current_y + 1)
    bottom = (current_x, current_y - 1)
    left = (current_x - 1, current_y)
    right = (current_x + 1, current_y)
    top_right = (current_x + 1, current_y + 1)
    bottom_right = (current_x + 1, current_y - 1)
    top_left = (current_x - 1, current_y + 1)
    bottom_left = (current_x - 1, current_y - 1)

    potentials = [top, bottom, left, right, top_right, bottom_right, top_left, bottom_left]
    next_list = [node for node in potentials if node in catalog_axis_i]
    ordered_axis = [current]

    while len(next_list) > 0:
        plt.scatter(*zip(*potentials))
        plt.scatter(*zip(*ordered_axis))
        plt.scatter(*zip(*next_list))
        plt.show()
        assert len(next_list) <= 2
        if len(next_list) == 1:
            next = next_list[0]
        else:
            dist_argmin = np.argmin([np.linalg.norm(np.array(potential_next) - np.array(current)) for potential_next in next_list])
            # print("min distances index", dist_argmin)
            next = next_list[dist_argmin]
        ordered_axis.append(next)
        # print("ordered_axis", ordered_axis)
        p_previous = previous
        previous = current
        current = next

        current_x, current_y = current[0], current[1]
        top = (current_x, current_y + 1)
        bottom = (current_x, current_y - 1)
        left = (current_x - 1, current_y)
        right = (current_x + 1, current_y)
        top_right = (current_x + 1, current_y + 1)
        bottom_right = (current_x + 1, current_y - 1)
        top_left = (current_x - 1, current_y + 1)
        bottom_left = (current_x - 1, current_y - 1)

        potentials = [top, bottom, left, right, top_right, bottom_right, top_left, bottom_left]
        if previous in potentials:
            potentials.remove(previous)
        if p_previous in potentials:
            potentials.remove(p_previous)
        next_list = [node for node in potentials if node in catalog_axis_i]
    # plt.scatter(top[0], top[1])
    # plt.scatter(bottom[0], bottom[1])
    # plt.scatter(bottom_right[0], bottom_right[1])
    # plt.scatter(right[0], right[1])
    # plt.scatter(top_right[0], top_right[1])
    return ordered_axis


def getPrecipPercentCatalog(axis_catalog, buffer_param, precip):
    pass


def getPrecipPercentWrapper():

    alpha_shape_dir = sys.argv[1]
    input_axis_dir = sys.argv[2]
    input_precip_path = sys.argv[3]
    AR_id = sys.argv[4]
    buffer_param = sys.argv[5]

    axis_i_path = input_axis_dir + "axis_" + AR_id + ".npy"
    alpha_shape_path = alpha_shape_dir + "AlphaShape_" + AR_id + ".npy"

    axis_i = np.load(axis_i_path)
    alpha_shape_i = np.load(alpha_shape_path)

    readerPrecip = vtk.vtkXMLImageDataReader()
    readerPrecip.SetFileName(input_precip_path)
    readerPrecip.Update()
    precip = readerPrecip.GetOutput()

    buffer_param = float(buffer_param)

    captured_percent = getPrecipPercent(axis_i, buffer_param, alpha_shape_i, precip)
    print(captured_percent)


if __name__ == "__main__":

    # getPrecipPercentWrapper()

    # alpha_shape_dir = 'IntermediateFiles/AlphaShape_1996_364_0/'
    # input_axis_dir = 'IntermediateFiles/GraphAxis_1996_364_0/'
    input_precip_path = 'MERRA2Precipitation/Precipitation24hrAfterSum/precipitation_1996_364_0.vti'
    # AR_id = '9'
    #
    # axis_i_path = input_axis_dir + "axis_" + AR_id + ".npy"
    # alpha_shape_path = alpha_shape_dir + "AlphaShape_" + AR_id + ".npy"
    #
    # axis_i = np.load(axis_i_path)
    # alpha_shape_i = np.load(alpha_shape_path)
    #
    # readerPrecip = vtk.vtkXMLImageDataReader()
    # readerPrecip.SetFileName(input_precip_path)
    # readerPrecip.Update()
    # precip = readerPrecip.GetOutput()
    #
    # captured_percent_list = []
    # for i in range(1, 20):
    #     print("Buffer", i)
    #     buffer_param = i
    #     captured_percent = getPrecipPercent(axis_i, buffer_param, alpha_shape_i, precip)
    #     captured_percent_list.append(captured_percent)
    #
    # x = np.linspace(0.1, 2, len(captured_percent_list))
    # plt.scatter(x, captured_percent_list)
    # plt.plot(x, captured_percent_list)
    # plt.show()

    axis_catalog_path = "ARCatalog/ARCatalog_1996/axis/ARCatalog_1996_axis_364_0.vtu"
    readerAxis = vtk.vtkXMLUnstructuredGridReader()
    readerAxis.SetFileName(axis_catalog_path)
    readerAxis.Update()
    axis_catalog = readerAxis.GetOutput()
    axis_points = VN.vtk_to_numpy(axis_catalog.GetPoints().GetData())
    axis_id = VN.vtk_to_numpy(axis_catalog.GetPointData().GetArray("AR_axis"))
    axis_id = np.array(list(map(int, axis_id)))
    AR_id = 1
    axis_i_catalog = np.where(axis_id == AR_id)[0]
    print(axis_i_catalog)
    axis_i_points = axis_points[axis_i_catalog][:, :2]
    ordered_axis = orderCatalogAxisPoints(axis_i_points)
    print(ordered_axis)
    # plt.scatter(*zip(*axis_i_points))
    # plt.plot(*zip(*axis_i_points))
    plt.plot(*zip(*ordered_axis))
    plt.show()






