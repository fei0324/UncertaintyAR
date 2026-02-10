import numpy as np
import vtk
import vtk.util.numpy_support as VN
import sys
import matplotlib.pyplot as plt


def getCPinARBoundary(AR_points, cp_coords, cp_cellid, id_outdir, coords_outdir):
    """
    Get the critical points inside of an AR boundary
    :param AR_points: the points of one AR extracted from the AR catalog (3d)
    :param cp_coords: coordinates of the critical points from the Morse Smale Complex
    :param cp_cellid: critical point CellId from paraview
    :return: A list of critical points indices inside of the AR boundary
    """

    cp_indices = []
    AR_tuples = [tuple(x) for x in AR_points]
    # print(AR_tuples)

    # cp_xs, cp_ys = [], []
    cp_inbound_coords = []
    for cp_index, cp in enumerate(cp_coords):
        cp_x, cp_y = cp[0], cp[1]
        topleft = (np.floor(cp_x), np.ceil(cp_y), 0)
        topright = (np.ceil(cp_x), np.ceil(cp_y), 0)
        bottomleft = (np.floor(cp_x), np.floor(cp_y), 0)
        bottomright = (np.ceil(cp_x), np.floor(cp_y), 0)

        inBoundary = {topleft in AR_tuples,
                      topright in AR_tuples,
                      bottomleft in AR_tuples,
                      bottomright in AR_tuples}

        if any(inBoundary):
            cp_indices.append(cp_index)
            cp_inbound_coords.append(np.array([cp_x, cp_y, 0]))
            # print(cp_inbound_coords)
            # cp_xs.append(cp_x)
            # cp_ys.append(cp_y)

    AR_cp_cellid = cp_cellid[cp_indices]

    # save ids and coords as .npy files
    np.save(id_outdir, AR_cp_cellid, allow_pickle=True)
    np.save(coords_outdir, np.array(cp_inbound_coords), allow_pickle=True)

    return cp_indices, AR_cp_cellid


def getCPinARBoundaryWrapper():

    inputAR = sys.argv[1]
    inputCP = sys.argv[2]
    CPoutdir = sys.argv[3]
    id = sys.argv[4]
    # print(id)

    readerAR = vtk.vtkXMLUnstructuredGridReader()
    readerAR.SetFileName(inputAR)
    readerAR.Update()
    AR = readerAR.GetOutput()
    AR_points = VN.vtk_to_numpy(AR.GetPoints().GetData())
    AR_id = VN.vtk_to_numpy(AR.GetPointData().GetArray("AR_shape"))
    AR_i = np.where(AR_id == int(id))[0]
    points = AR_points[AR_i]

    # AR_x = []
    # AR_y = []
    # for point in points:
    #     AR_x.append(point[0])
    #     AR_y.append(point[1])
    # plt.scatter(AR_x, AR_y)
    # plt.show()

    readerCP = vtk.vtkXMLPolyDataReader()
    readerCP.SetFileName(inputCP)
    readerCP.Update()
    cp = readerCP.GetOutput()
    cp_coords = VN.vtk_to_numpy(cp.GetPoints().GetData())
    # print(cp_coords)
    cp_cellid = VN.vtk_to_numpy(cp.GetPointData().GetArray("CellId"))
    # print(cp_cellid)
    id_outdir = CPoutdir + "ARCP_cellid_" + str(id) + ".npy"
    coords_outdir = CPoutdir + "ARCP_coords_" + str(id) + ".npy"

    getCPinARBoundary(points, cp_coords, cp_cellid, id_outdir, coords_outdir)


if __name__ == "__main__":

    getCPinARBoundaryWrapper()

    # readerCP = vtk.vtkXMLPolyDataReader()
    # inputCP = "ivt_1996_364_0_cp.vtp"
    # readerCP.SetFileName(inputCP)
    # readerCP.Update()
    # cp = readerCP.GetOutput()
    # cp_coords = VN.vtk_to_numpy(cp.GetPoints().GetData())
    # cp_cellid = VN.vtk_to_numpy(cp.GetPointData().GetArray("CellId"))
    # id_outdir = "IntermediateFiles/ARCP_1996_364_0/"