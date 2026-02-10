import vtk
import vtk.util.numpy_support as VN
import numpy as np
import alphashape
import json
import copy
import sys
from shapely.geometry import Point
from scipy.spatial.distance import pdist, squareform

import matplotlib.pyplot as plt


def getFurthestIPs(intersection_points, ip_furthest_path):
    """
    Get the furthest two points (intersection points) on the MSC in an AR
    :param intersection_points: a list of intersection points from getMSCInterior()
    :return: save [[point1], [point2]] as .npy file
    """
    pairwise_distance = squareform(pdist(np.array(intersection_points), 'euclidean'))
    furthest_ids = np.unravel_index(np.argmax(pairwise_distance), pairwise_distance.shape)
    furthest_coords = [intersection_points[furthest_ids[0]], intersection_points[furthest_ids[1]]]
    np.save(ip_furthest_path, furthest_coords, allow_pickle=True)


def getMSCInterior(AR_i_points, MSC_subset_i, alpha_shape_path, json_path, r=0, alpha=1):
    """
    Get the MSC subset inside of an AR and return the intersection points
    :param AR_i_points: the points of one AR
    :param MSC_subset_i: the MSC subset around the AR
    :param json_path: the path to save MSC_shurnk
    :param r: radius of tolerance (prevent the deletion of the MSC line segments that are slightly outside of the alpha shape)
    :param alpha: parameter for alphashape, default is 1 because of the points are distance 1 apart in the AR catalog
    :return: the intersection points in a list
    """
    alpha_shape = alphashape.alphashape(AR_i_points, alpha)

    # if alpha_shape is one connected component
    if alpha_shape.geom_type == 'Polygon':
        alpha_shape_coords = alpha_shape.exterior.coords[:]

    # if alpha_shape is a multipolygon
    else:
        alpha_shape_coords = None
        for AR_subset in alpha_shape.geoms:
            if alpha_shape_coords is None:
                alpha_shape_coords = AR_subset.exterior.coords[:]
            else:
                alpha_shape_coords = alpha_shape_coords + AR_subset.exterior.coords[:]
    np.save(alpha_shape_path, alpha_shape_coords)

    msc_shrunk = copy.deepcopy(MSC_subset_i)
    intersection_points = []
    for i, edge in MSC_subset_i.items():
        for cell in edge['cells']:
            point0 = cell[0]
            point1 = cell[1]
            if alpha_shape.contains(Point(point0[0], point0[1])) and not alpha_shape.contains(Point(point1[0], point1[1])):
                intersection_points.append(point0[:2])
                intersection_points.append(point1[:2])
            elif not alpha_shape.contains(Point(point0[0], point0[1])) and alpha_shape.contains(
                Point(point1[0], point1[1])):
                intersection_points.append(point0[:2])
                intersection_points.append(point1[:2])
            elif not (alpha_shape.contains(Point(point0[0], point0[1])) and alpha_shape.contains(
                Point(point1[0], point1[1]))):
                if alpha_shape.distance(Point(point0[0], point0[1])) >= r and alpha_shape.distance(
                Point(point1[0], point1[1])) >= r:
                    msc_shrunk[i]['cells'].remove(cell)

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(msc_shrunk, f, ensure_ascii=False, indent=4)
    f.close()

    return intersection_points


def shrinkMSCWrapper():

    inputAR = sys.argv[1]
    AR_id = sys.argv[2]
    msc_subset_outdir = sys.argv[3]
    cpInAR_outdir = sys.argv[4]
    alpha_shape_outdir = sys.argv[5]

    msc_subset_AR_i = msc_subset_outdir + "MSCSubset_" + AR_id + ".json"
    msc_shrunk_outpath = msc_subset_outdir + "MSCShrunk_" + AR_id + ".json"
    ip_furthest_i = cpInAR_outdir + "IP_furthest_" + AR_id + ".npy"
    alpha_shape_outpath = alpha_shape_outdir + "AlphaShape_" + AR_id + ".npy"

    readerAR = vtk.vtkXMLUnstructuredGridReader()
    readerAR.SetFileName(inputAR)
    readerAR.Update()
    AR = readerAR.GetOutput()
    AR_points = VN.vtk_to_numpy(AR.GetPoints().GetData())
    AR_ids = VN.vtk_to_numpy(AR.GetPointData().GetArray("AR_shape"))
    AR_i = np.where(AR_ids == int(AR_id))[0]
    AR_i_points = AR_points[AR_i][:, :2]

    with open(msc_subset_AR_i, "r") as f:
        msc_subset_i = json.load(f)
        intersection_points = getMSCInterior(AR_i_points, msc_subset_i, alpha_shape_outpath, msc_shrunk_outpath, alpha=1)
        getFurthestIPs(intersection_points, ip_furthest_i)


if __name__ == "__main__":

    shrinkMSCWrapper()
    # inputAR = "ARCatalog/ARCatalog_1996/shape/ARCatalog_1996_shape_363_0.vtu"
    # inputAR = "ARCatalog/ARCatalog_1996/shape/ARCatalog_1996_shape_364_0.vtu"
    # readerAR = vtk.vtkXMLUnstructuredGridReader()
    # readerAR.SetFileName(inputAR)
    # readerAR.Update()
    # AR = readerAR.GetOutput()
    # AR_points = VN.vtk_to_numpy(AR.GetPoints().GetData())
    # AR_id = VN.vtk_to_numpy(AR.GetPointData().GetArray("AR_shape"))
    # AR_i = np.where(AR_id == 12)[0]
    # AR_i = np.where(AR_id == 3)[0]
    # AR_individual_points = AR_points[AR_i][:, :2]
    # print(type(AR_individual_points))
    # alpha_shape = alphashape.alphashape(AR_individual_points, 1)
    # print(alpha_shape.bounds)
    # print(len(alpha_shape.geoms))
    # AR_boundary = list(alpha_shape.exterior.coords)

    # for AR_subset in alpha_shape.geoms:
    #     AR_boundary = list(AR_subset.exterior.coords)
    #     plt.scatter(*zip(*AR_boundary))
    #
    # plt.show()

    # msc_subset_AR_i = "IntermediateFiles/MSCSubset_1996_365_0/MSCSubset_9.json"
    # msc_subset_AR_i = "IntermediateFiles/MSCSubset_1996_364_0/MSCSubset_3.json"
    # msc_shrunk_i = "IntermediateFiles/MSCSubset_1996_364_0/MSCShrunk_3.json"
    # ip_furthest_i = "IntermediateFiles/ARCP_1996_364_0/IP_furthest_3.npy"
    # ip = np.load(ip_furthest_i)
    # print(ip)

    # with open(msc_subset_AR_i, "r") as f:
    #     msc_subset_i = json.load(f)
    #     intersection_points = getMSCInterior(AR_3_points, msc_subset_i, msc_shrunk_i, alpha=1)
    #     getFurthestIPs(intersection_points, ip_furthest_i)
    # plt.scatter(*zip(*AR_boundary))
    # with open(msc_subset_AR_i, "r") as f:
    #     edges = json.load(f)
    #     # print(edges)
    #     x = []
    #     y = []
    #     x_intersection = []
    #     y_intersection = []
    #     for i, edge in edges.items():
    #         # print(edge.keys())
    #         for cell in edge['cells']:
    #             point_0_x = cell[0][0]
    #             point_0_y = cell[0][1]
    #             point_1_x = cell[1][0]
    #             point_1_y = cell[1][1]
    #             if alpha_shape.contains(Point(point_0_x, point_0_y)) and alpha_shape.contains(Point(point_1_x, point_1_y)):
    #                 x.append(cell[0][0])
    #                 y.append(cell[0][1])
    #                 x.append(cell[1][0])
    #                 y.append(cell[1][1])
    #             elif alpha_shape.contains(Point(point_0_x, point_0_y)) and not alpha_shape.contains(Point(point_1_x, point_1_y)):
    #                 x_intersection.append(cell[0][0])
    #                 y_intersection.append(cell[0][1])
    #                 x_intersection.append(cell[1][0])
    #                 y_intersection.append(cell[1][1])
    #             elif not alpha_shape.contains(Point(point_0_x, point_0_y)) and alpha_shape.contains(Point(point_1_x, point_1_y)):
    #                 x_intersection.append(cell[0][0])
    #                 y_intersection.append(cell[0][1])
    #                 x_intersection.append(cell[1][0])
    #                 y_intersection.append(cell[1][1])
    #     plt.scatter(x, y)
    #     plt.scatter(x_intersection, y_intersection)
    # f.close()
    # plt.show()


    # fig, ax = plt.subplots()
    # for i in range(1, len(boundary)):
    #     boundary_part = boundary[:i]
    #     print(boundary_part)
    #     plt.scatter(*zip(*boundary_part))
        # ax.scatter(*zip(*boundary))
        # plt.show()
    # ax.add_patch(PolygonPatch(alpha_shape, alpha=0.2))
    # plt.show()
    # oldBoundary = np.load("IntermediateFiles/ARBoundaries_1996_365_0/ARBoundary_9.npy")
    # print(oldBoundary[:, :2])
    # plt.scatter(*zip(*oldBoundary[:, :2]))
    # plt.show()

