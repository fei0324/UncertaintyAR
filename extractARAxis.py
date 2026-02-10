import vtk
import os
import sys
import time as tm
import vtk.util.numpy_support as VN
import numpy as np

# from getARBoundary import getOrderedARBoundary
# from getCPinARBoundary import getCPinARBoundary
# from getMSCSubset import wrapper

if __name__ == "__main__":

    print("Start time: ", tm.time())
    algo_name = sys.argv[1] # algorithm folder name
    year = sys.argv[2]
    day = sys.argv[3]
    time = sys.argv[4]
    # inputAR = sys.argv[1]  # AR points from the catalog
    # inputIVT = sys.argv[2]
    # algo_name = sys.argv[3]  # algorithm folder name
    sim_threshold = sys.argv[5]

    inputAR = "Algorithms/" + algo_name + "/ARCatalog/ARCatalog_" + str(year) + "/shape/ARCatalog_" + str(year)\
              + "_shape_" + str(day) + "_" + str(time) + ".vtu"
    print(inputAR)
    inputIVT = "MERRA2IVT/ivt_" + str(year) + "/ivt_" + str(year) + "_" + str(day) + "_" + str(time) + ".vti"
    print(inputIVT)
    # algo_name = inputAR.split("/")[1]
    print(algo_name)
    # name_parse = inputAR.split("_")
    # year = name_parse[-4]
    # day = name_parse[-2]
    # time = name_parse[-1][0]
    print(year, day, time)
    print(sim_threshold)

    inputCP = "MSCData/cp_" + str(year) + "_" + str(day) + "_" + str(time) + "_" + str(sim_threshold) + ".vtp"
    inputMSC = "MSCData/msc_" + str(year) + "_" + str(day) + "_" + str(time) + "_" + str(sim_threshold) + ".vtp"

    # Generate the CP and MSC files from Paraview if they don't exist already
    if not (os.path.exists(inputCP) and os.path.exists(inputMSC)):
        print("Generate the CP and MSC files from Paraview.")
        submitCommand = "pvpython ./src/getMSCfromIVT.py " + inputIVT + " " + sim_threshold + " " + inputCP + " " + inputMSC
        os.system(submitCommand)

    CP_outdir = "Algorithms/" + algo_name + "/IntermediateFiles/ARCP_" + str(year) + "_" + str(day) + "_" + str(time) + "_" + str(sim_threshold) +  "/"
    print(CP_outdir)
    os.makedirs(CP_outdir, exist_ok=True)
    AlphaShape_outdir = "Algorithms/" + algo_name + "/IntermediateFiles/AlphaShape_" + str(year) + "_" + str(day) + "_" + str(time) + "_" + str(sim_threshold) + "/"
    print(AlphaShape_outdir)
    os.makedirs(AlphaShape_outdir, exist_ok=True)
    MSC_subset_dir = "Algorithms/" + algo_name + "/IntermediateFiles/MSCSubset_" + str(year) + "_" + str(day) + "_" + str(time) + "_" + str(sim_threshold) + "/"
    print(MSC_subset_dir)
    os.makedirs(MSC_subset_dir, exist_ok=True)
    print(inputMSC)
    MSC_name = inputMSC.split("/")[-1]
    print(MSC_name)
    graph_axis_outdir = "Algorithms/" + algo_name + "/GraphAxis/GraphAxis_" + str(year) + "_" + str(day) + "_" + str(time) + "_" + str(sim_threshold) + "/"
    print(graph_axis_outdir)
    os.makedirs(graph_axis_outdir, exist_ok=True)

    # print("Computing AR boundaries.")
    # submitCommand = "python ./src/getARBoundary.py " + inputAR + " " + AR_outdir
    # os.system(submitCommand)

    print("Getting the set of AR ids.")
    readerAR = vtk.vtkXMLUnstructuredGridReader()
    readerAR.SetFileName(inputAR)
    readerAR.Update()
    AR = readerAR.GetOutput()
    AR_points = VN.vtk_to_numpy(AR.GetPoints().GetData())
    AR_id_list = VN.vtk_to_numpy(AR.GetPointData().GetArray("AR_shape"))
    AR_id_set = set(AR_id_list)
    print(AR_id_set)

    for AR_id in AR_id_set:
        loop_i_start = tm.time()
        AR_id = str(int(AR_id))
        print(AR_id)

        # Get the ARs in Pacific/North America region
        AR_i = np.where(AR_id_list == int(AR_id))[0]
        points = AR_points[AR_i]
        # Get the top, bottom, left, and right most points of the AR
        # Check if they are all in the Pacific/North American boundary
        max_x = np.max(points[:, 0])
        max_y = np.max(points[:, 1])
        min_x = np.min(points[:, 0])
        min_y = np.min(points[:, 1])
        top_most = np.where(points[:, 1] == max_y)[0]
        bottom_most = np.where(points[:, 1] == min_y)[0]
        left_most = np.where(points[:, 0] == min_x)[0]
        right_most = np.where(points[:, 0] == max_x)[0]
        all_boundary_pts = np.concatenate((points[top_most], points[bottom_most], points[left_most], points[right_most]))
        # if np.all((all_boundary_pts[:, 0] >= 200) & (all_boundary_pts[:, 0] <= 500)
        #              & (all_boundary_pts[:, 1] >= 190) & (all_boundary_pts[:, 1] <= 340)):

        if len(all_boundary_pts) > 0:
            print("Getting critical points inside of the AR boundary.")
            submitCommand = "python ./src/getCPinARBoundary.py " + inputAR + " " + inputCP + " " + CP_outdir + " " + AR_id
            os.system(submitCommand)

            print("Computing MSC subset using the critical points.")
            msc_subset_outpath = MSC_subset_dir + "MSCSubset_" + AR_id + ".json"
            submitCommand = "pvpython ./src/getMSCSubset.py " + inputMSC + " " + CP_outdir + " " + AR_id + " " + msc_subset_outpath
            os.system(submitCommand)

            print("Shrink MSC subset.")
            submitCommand = "python ./src/getAlphaShape.py " + inputAR + " " + AR_id + " " + MSC_subset_dir + " " + CP_outdir + " " + AlphaShape_outdir
            print(submitCommand)
            os.system(submitCommand)

            print("Computing skeleton and axis.")
            submitCommand = "python ./src/constructGraph.py " + MSC_subset_dir + " " + AR_id + " " + CP_outdir + " " + graph_axis_outdir
            os.system(submitCommand)

    loop_i_end = tm.time()
    print("Loop i time: ", loop_i_end - loop_i_start)





