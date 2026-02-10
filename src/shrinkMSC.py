import numpy as np
import matplotlib.pyplot as plt
import json
import copy
import sys


def _onSegment(p, q, r):
    """Given three colinear points p, q, r, check if point q lies on line segment 'pr"""
    p_x, p_y = p[0], p[1]
    q_x, q_y = q[0], q[1]
    r_x, r_y = r[0], r[1]

    if (q_x <= max(p_x, r_x)) and (q_x >= min(p_x, r_x)) and (q_y <= max(p_y, r_y)) and (q_y >= min(p_y, r_y)):
        return True
    return False


def _orientation(p, q, r):
    """
    Given three points, find the orientation of an ordered triplet (p, q, r)
    :return: 0 - collinear points, 1 - clockwise points, 2 - counterclockwise
    """
    p_x, p_y = p[0], p[1]
    q_x, q_y = q[0], q[1]
    r_x, r_y = r[0], r[1]
    val = (float(q_y - p_y)*(r_x - q_x)) - (float(q_x - p_x)*(r_y - q_y))
    # account for errors, theoretically val = 0 is the threshold
    if val > 0.00005:
        return 1
    elif val < -0.00005:
        return 2
    else:
        return 0


def _doIntersect(p1, q1, p2, q2):
    """Find if line segments 'p1q1' and 'p2a2' intersect."""
    o1 = _orientation(p1, q1, p2)
    o2 = _orientation(p1, q1, q2)
    o3 = _orientation(p2, q2, p1)
    o4 = _orientation(p2, q2, q1)

    # p1, q1 and p2 are collinear and p2 lies on segment p1q1
    if (o1 == 0) and _onSegment(p1, p2, q1):
        return 2
    # p1, q1 and q2 are collinear and q2 lies on segment p1q1
    if (o2 == 0) and _onSegment(p1, q2, q1):
        return 3
    # p2, q2 and p1 are collinear and p1 lies on segment p2q2
    if (o3 == 0) and _onSegment(p2, p1, q2):
        return 4
    # p2, q2 and q1 are collinear and q1 lies on segment p2q2
    if (o4 == 0) and _onSegment(p2, q1, q2):
        return 5
    # general case (pretty much never happens)
    if (o1 != o2) and (o3 != o4):
        return 1
    return 0


def _getSlopeIntercept(p, q):
    p_x, p_y = p[0], p[1]
    q_x, q_y = q[0], q[1]
    m = (p_y - q_y)/(p_x - q_x)
    b = p_y - m*p_x
    return m, b


def _findIntersection(p1, q1, p2, q2):
    m1, b1 = _getSlopeIntercept(p1, q1)
    m2, b2 = _getSlopeIntercept(p2, q2)

    x = (b2 - b1)/(m1 - m2)
    y = m1*x + b1
    return x, y


def _addIntersectionPoint(intersection_dict, i, j, x, y):
    """
    Add intersection point to intersection dictionary
    :param intersection_dict: current intersection_dict
    :param i: segment i
    :param j: cell j
    :param x: intersection point x coordinate
    :param y: intersection point y coordinate
    :return: new intersection_dict
    """
    if i not in intersection_dict.keys():
        intersection_dict[i] = {j: [x, y]}
    else:
        intersection_dict[i][j] = [x, y]
    return intersection_dict


def findMSCBoundaryIntersection(mscSubset, AR_boundary):
    """
    Find the intersection points between AR boundary and the morse smale complex subset
    :param mscSubset: output of getMSCSubset() read in using json
    :param AR_boundary: the ordered AR boundary points
    :return: a dictionary recording all the intersection points
        {i segment: {j cell: [x, y], ...} ...}
    """
    intersection_dict = {}
    for i, segment in mscSubset.items():
        cells = segment['cells']
        for j, cell in enumerate(cells):
            p1 = cell[0][:2]
            q1 = cell[1][:2]

            for k in range(len(AR_boundary) - 1):
                p2 = AR_boundary[k][:2]
                q2 = AR_boundary[k+1][:2]
                if _doIntersect(p1, q1, p2, q2) == 1:
                    # print("intersection type: ", doIntersect(p1, q1, p2, q2))
                    # compute intersections by looking at two intersecting lines
                    x, y = _findIntersection(p1, q1, p2, q2)
                    intersection_dict = _addIntersectionPoint(intersection_dict, i, j, x, y)
                # the following cases are all collinear cases
                # p2 is the intersection
                elif _doIntersect(p1, q1, p2, q2) == 2:
                    # print("intersection type: ", _doIntersect(p1, q1, p2, q2))
                    x, y = p2[0], p2[1]
                    intersection_dict = _addIntersectionPoint(intersection_dict, i, j, x, y)
                # q2 is the intersection
                elif _doIntersect(p1, q1, p2, q2) == 3:
                    # print("intersection type: ", _doIntersect(p1, q1, p2, q2))
                    x, y = q2[0], q2[1]
                    intersection_dict = _addIntersectionPoint(intersection_dict, i, j, x, y)
                # p1 is the intersection
                elif _doIntersect(p1, q1, p2, q2) == 4:
                    # print("intersection type: ", _doIntersect(p1, q1, p2, q2))
                    x, y = p1[0], p1[1]
                    intersection_dict = _addIntersectionPoint(intersection_dict, i, j, x, y)
                # q1 is the intersection
                elif _doIntersect(p1, q1, p2, q2) == 5:
                    # print("intersection type: ", _doIntersect(p1, q1, p2, q2))
                    x, y = q1[0], q1[1]
                    intersection_dict = _addIntersectionPoint(intersection_dict, i, j, x, y)
    return intersection_dict


def getFurthestIPs(intersection_dict, outfile):
    """
    Find the two intersection points with the furthest longitude distance
    :param intersection_dict: output from findMSCBoundaryIntersection()
    :return:
    """
    intersection_points = []
    for _, intersections in intersection_dict.items():
        intersection_points += list(intersections.values())

    intersection_points = np.array(intersection_points)
    # min and max longitude
    west_IP_index = np.argmin(intersection_points, axis=0)[0]
    east_IP_index = np.argmax(intersection_points, axis=0)[0]

    west_IP = intersection_points[west_IP_index]
    east_IP = intersection_points[east_IP_index]

    np.save(outfile, [west_IP, east_IP], allow_pickle=True)


def shrinkMSCSubset(mscSubset, intersection_dict, cpInAR, jsonDir):
    """
    Shrink the MSC subset to the AR boundary, discarding the rest
    :param mscSubset: json file from getMSCSubset.py
    :param intersections_dict: intersection points from findMSCBoundaryIntersection()
    :return:
    """
    msc_shrunk = copy.deepcopy(mscSubset)

    for segment_i, intersections in intersection_dict.items():
        segment_source = mscSubset[segment_i]['source']
        segment_target = mscSubset[segment_i]['target']
        segment_cells = msc_shrunk[segment_i]['cells']
        # works for numeric keys, not string keys
        if segment_source in cpInAR:
            # remove the cells from the last intersection to the last point
            max_key = max(intersections.keys())
            last_intersection = intersections[max_key]
            last_intersection.append(0.)
            # move the ending point of the line segment to the intersection point
            if segment_cells[int(max_key)][0] == last_intersection:
                segment_cells = segment_cells[:int(max_key)]
            else:
                segment_cells[int(max_key)][1] = last_intersection
                segment_cells = segment_cells[:int(max_key) + 1]
        elif segment_target in cpInAR:
            # remove the cells 0 to first intersection point
            min_key = min(intersections.keys())
            first_intersection = intersections[min_key]
            first_intersection.append(0.)
            # print("intersection point", first_intersection)
            # move the starting end of the line segment to the intersection point
            if segment_cells[int(min_key)][1] == first_intersection:
                segment_cells = segment_cells[(int(min_key) + 1):]
            else:
                segment_cells[int(min_key)][0] = first_intersection
                # print(msc_shrunk[segment_i]['cells'][int(min_key)])
                segment_cells = segment_cells[int(min_key):]
        # substitue the segment with the shortened one
        msc_shrunk[segment_i]['cells'] = segment_cells

    with open(jsonDir, 'w', encoding='utf-8') as f:
        json.dump(msc_shrunk, f, ensure_ascii=False, indent=4)


def shrinkMSCWrapper():

    msc_subset_outdir = sys.argv[1]
    ARBoundary_outdir = sys.argv[2]
    cpInAR_outdir = sys.argv[3]
    AR_id = sys.argv[4]
    MSC_shrunk_outpath = msc_subset_outdir + "MSCShrunk_" + str(AR_id) + ".json"

    msc_subset_AR_i = msc_subset_outdir + "MSCSubset_" + AR_id + ".json"
    AR_boundary_i = ARBoundary_outdir + "ARBoundary_" + AR_id + ".npy"
    cp_inAR_i = cpInAR_outdir + "ARCP_cellid_" + AR_id + ".npy"
    ip_furthest_i = cpInAR_outdir + "IP_furthest_" + AR_id + ".npy"

    with open(msc_subset_AR_i, "r") as f:
        edges = json.load(f)
        AR_bound = np.load(AR_boundary_i)
        cpInAR = np.load(cp_inAR_i)
        intersections = findMSCBoundaryIntersection(edges, AR_bound)
        getFurthestIPs(intersections, ip_furthest_i)
        shrinkMSCSubset(edges, intersections, cpInAR, MSC_shrunk_outpath)


if __name__ == "__main__":

    shrinkMSCWrapper()

    # inputMSC = "MSCData/msc_1996_364_0.vtp"
    # reader1 = vtk.vtkXMLPolyDataReader()
    # reader1.SetFileName(inputMSC)
    # reader1.Update()

    # inputCP = "MSCData/cp_1996_364_0.vtp"
    # reader2 = vtk.vtkXMLPolyDataReader()
    # reader2.SetFileName(inputCP)
    # reader2.Update()

    # inputAR = "ARCatalog/ARCatalog_1996/shape/ARCatalog_1996_shape_364_0.vtu"
    # readerAR = vtk.vtkXMLUnstructuredGridReader()
    # readerAR.SetFileName(inputAR)
    # readerAR.Update()

    # AR = readerAR.GetOutput()
    # AR_points = VN.vtk_to_numpy(AR.GetPoints().GetData())
    # AR_id = VN.vtk_to_numpy(AR.GetPointData().GetArray("AR_shape"))
    # print(len(AR_id))
    # # AR 3 and 4 are in north america
    # AR_3 = np.where(AR_id == 3)[0]
    # AR_3_points = AR_points[AR_3]

    # get the critical points inside of the AR boundaries
    # cp = reader2.GetOutput()
    # cp_coordinates = VN.vtk_to_numpy(cp.GetPoints().GetData())
    # cp_cellid = VN.vtk_to_numpy(cp.GetPointData().GetArray("CellId"))

    # AR_cp_dir = "IntermediateFiles/AR_3_cp_sim.npy"
    # AR_cp_coords = "IntermediateFiles/AR_3_cp_coords_sim.npy"
    # AR_3_cp_index, AR_3_cp_cellid = getCPinARBoundary(AR_3_points, cp_coordinates, cp_cellid, AR_cp_dir, AR_cp_coords)
    #
    # AR_bound_dir = "IntermediateFiles/AR_3_boundary.npy"
    # AR_3_bound_index, AR_3_bound_coords = getARBoundary(AR_3_points, AR_bound_dir)

    # with open("IntermediateFiles/AR_3_edges_sim.json", "r") as f:
    #     edges = json.load(f)
    #     AR_bound = np.load("IntermediateFiles/AR_boundary_ordered.npy")
    #     cpInAR = np.load("IntermediateFiles/AR_3_cp_sim.npy")
    #     intersections = findMSCBoundaryIntersection(edges, AR_bound)
        # with open("IntermediateFiles/AR_3_intersection.json", "r") as file:
        #     intersections = json.load(file)
        # shrinkMSCSubset(edges, intersections, cpInAR, "IntermediateFiles/AR_3_msc_shrunk.json")
        # with open("IntermediateFiles/AR_3_intersection.json", "w", encoding='utf-8') as file:
        #     json.dump(intersections, file, ensure_ascii=False, indent=4)

