import numpy as np
import vtk
import vtk.util.numpy_support as VN
import matplotlib.pyplot as plt
import os
import pickle


def round2point5(array):
    new_array = np.zeros(array.shape)
    for i in range(len(array)):
        x = array[i][0]
        y = array[i][1]

        if x % 1 <= 0.25:
            x = np.floor(x)
        elif 0.25 < x % 1 < 0.75:
            x = int(x) + 0.5
        elif x % 1 >= 0.75:
            x = np.ceil(x)

        if y % 1 <= 0.25:
            y = np.floor(y)
        elif 0.25 < y % 1 < 0.75:
            y = int(y) + 0.5
        elif y % 1 >= 0.75:
            y = np.ceil(y)

        new_array[i] = [x, y]

    return new_array


def getAxisOnOcean(axis_i, sst):
    # betwwen 0 to 0.25 round to 0, between 0.25 and 0.75 round to 0.5, > 0.75 round to 1
    rounded_axis_i = round2point5(axis_i)
    rounded_sst = round2point5(sst)

    set_axis_i = set(map(tuple, rounded_axis_i))
    set_sst = set(map(tuple, rounded_sst))
    pts_on_ocean = set_axis_i.intersection(set_sst)

    axis_on_ocean = np.zeros((1, 2))

    for pt in pts_on_ocean:
        pt_indices = np.where((rounded_axis_i[:, 0] == pt[0]) & (rounded_axis_i[:, 1] == pt[1]))[0]
        axis_on_ocean = np.concatenate((axis_on_ocean, axis_i[pt_indices]), axis=0)

    axis_on_ocean = axis_on_ocean[1:]

    return axis_on_ocean



def samplePrecipBelow(axis_i, precip_points, precip_vals, r):

    axis_i = list(map(tuple, axis_i))
    # print(axis_i)
    # print(precip_points)
    # print(len(precip_points))
    num_cols, num_rows = precip_points[-1][0] + 1, precip_points[-1][1] + 1
    precip_points = list(map(tuple, precip_points))
    # print(precip_points)

    precip_sampled = []
    for axis_i_pt in axis_i:
        axis_i_pt_x = axis_i_pt[0]
        axis_i_pt_y = axis_i_pt[1]
        floor_y = np.floor(axis_i_pt_y)
        ceil_y = np.ceil(axis_i_pt_y)
        floor_x = np.floor(axis_i_pt_x)
        ceil_x = np.ceil(axis_i_pt_x)
        # # print(floor_x, floor_y)
        # index_bl = precip_points.index((floor_x, floor_y))
        # # print(index_bl)
        # ul_start = index_bl + num_cols*r - (r-1)
        # # print("upperleft ", ul_start)
        # # print("upperleft coord", precip_points[int(ul_start)])
        # width = 2*r
        # precip_vals_indices = []
        #
        # for i in range(width):
        #     # print("i", i)
        #     row_start = ul_start - num_cols*i
        #     # print("row start: ", row_start)
        #     precip_vals_indices.append(int(row_start))
        #     # print(precip_points[int(row_start)])
        #     for j in range(1, width):
        #         # print("j", j)
        #         precip_vals_indices.append(int(row_start + j))
        #
        # precip_under_pt = precip_vals[precip_vals_indices]
        # precip_sampled.append(sum(precip_under_pt) / len(precip_under_pt))


        index_bl, index_tl, index_br, index_tr = precip_points.index((floor_x, floor_y)), \
                                                 precip_points.index((floor_x, ceil_y)), \
                                                 precip_points.index((ceil_x, floor_y)), \
                                                 precip_points.index((ceil_x, ceil_y))



        precip_under_pt = precip_vals[[index_bl, index_tl, index_br, index_tr]]
        precip_sampled.append(sum(precip_under_pt)/4)

    return precip_sampled


def samplePrecipBelowWithR(axis_i, precip_points, precip_vals, r):

    axis_i = list(map(tuple, axis_i))
    # print(axis_i)
    # print(precip_points)
    # print(len(precip_points))
    num_cols, num_rows = precip_points[-1][0] + 1, precip_points[-1][1] + 1
    precip_points = list(map(tuple, precip_points))
    # print(precip_points)

    precip_sampled = []
    for axis_i_pt in axis_i:
        axis_i_pt_x = axis_i_pt[0]
        axis_i_pt_y = axis_i_pt[1]
        floor_y = np.floor(axis_i_pt_y)
        # ceil_y = np.ceil(axis_i_pt_y)
        floor_x = np.floor(axis_i_pt_x)
        # ceil_x = np.ceil(axis_i_pt_x)
        # print(floor_x, floor_y)
        index_bl = precip_points.index((floor_x, floor_y))
        # print(index_bl)
        ul_start = index_bl + num_cols*r - (r-1)
        # print("upperleft ", ul_start)
        # print("upperleft coord", precip_points[int(ul_start)])
        width = 2*r
        precip_vals_indices = []

        for i in range(width):
            # print("i", i)
            row_start = ul_start - num_cols*i
            # print("row start: ", row_start)
            precip_vals_indices.append(int(row_start))
            # print(precip_points[int(row_start)])
            for j in range(1, width):
                # print("j", j)
                precip_vals_indices.append(int(row_start + j))

        precip_under_pt = precip_vals[precip_vals_indices]
        precip_sampled.append(sum(precip_under_pt) / len(precip_under_pt))

    return precip_sampled


if __name__ == "__main__":

    sst_path = 'sst_clean.vtu'
    readerSST = vtk.vtkXMLUnstructuredGridReader()
    readerSST.SetFileName(sst_path)
    readerSST.Update()
    sst = readerSST.GetOutput()
    sst_coords = VN.vtk_to_numpy(sst.GetPoints().GetData())[:, :2]

    # Plot boxplots for ARs in the Pacific/North America region
    start_day = 351
    end_day = 365
    time_step_list = []
    for i in range(start_day, end_day + 1):
        time_step_list.append(str(i) + '_0')
        time_step_list.append(str(i) + '_1')
        time_step_list.append(str(i) + '_2')
        time_step_list.append(str(i) + '_3')
    print(time_step_list)

    boxplot_on_ocean = []
    boxplot_overall = []
    our_axis_on_ocean = []
    our_axis_on_ocean_sum = []
    catalog_on_ocean = []
    catalog_on_ocean_sum = []
    our_axis_overall = []
    our_axis_overall_sum = []
    catalog_overall = []
    catalog_overall_sum = []

    # our_axis_on_ocean = {}
    # catalog_on_ocean = {}
    # our_axis_overall = {}
    # catalog_overall = {}
    # our_skeleton = {}

    for time_step in time_step_list:
        input_precip_path = 'MERRA2Precipitation/Precipitation24hrAfterSum/precipitation_1996_' + time_step + '.vti'
        readerPrecip = vtk.vtkXMLImageDataReader()
        readerPrecip.SetFileName(input_precip_path)
        readerPrecip.Update()
        precip = readerPrecip.GetOutput()

        num_points = precip.GetNumberOfPoints()
        precip_vals = VN.vtk_to_numpy(precip.GetPointData().GetArray("precipitation"))
        precip_points = []

        for i in range(num_points):
            precip_point = precip.GetPoint(i)
            precip_points.append(np.array(precip_point[:2]))
        precip_points = np.array(precip_points)

        input_axis_dir = 'IntermediateFiles/GraphAxis_1996_' + time_step + '/'
        # No more than 20 axes in each time step
        for i in range(20):
            AR_id = str(i)
            axis_i_path = input_axis_dir + 'axis_' + AR_id + '.npy'
            if os.path.isfile(axis_i_path):
                print(axis_i_path)
                axis_i = np.load(axis_i_path)

                input_shape_path = 'ARCatalog/ARCatalog_1996/shape/ARCatalog_1996_shape_' + time_step + '.vtu'
                readerShape = vtk.vtkXMLUnstructuredGridReader()
                readerShape.SetFileName(input_shape_path)
                readerShape.Update()
                shape_catalog = readerShape.GetOutput()
                shape_points = VN.vtk_to_numpy(shape_catalog.GetPoints().GetData())
                shape_id = VN.vtk_to_numpy(shape_catalog.GetPointData().GetArray("AR_shape"))
                shape_id = np.array(list(map(int, shape_id)))
                shape_i_catalog = np.where(shape_id == int(AR_id))[0]
                shape_i_points = shape_points[shape_i_catalog][:, :2]

                axis_catalog_path = 'ARCatalog/ARCatalog_1996/axis/ARCatalog_1996_axis_' + time_step + '.vtu'
                readerAxis = vtk.vtkXMLUnstructuredGridReader()
                readerAxis.SetFileName(axis_catalog_path)
                readerAxis.Update()
                axis_catalog = readerAxis.GetOutput()
                axis_points = VN.vtk_to_numpy(axis_catalog.GetPoints().GetData())
                axis_id = VN.vtk_to_numpy(axis_catalog.GetPointData().GetArray("AR_axis"))
                axis_id = np.array(list(map(int, axis_id)))
                # AR_id = 4
                axis_i_catalog = np.where(axis_id == int(AR_id))[0]
                # print(axis_i_catalog)
                axis_i_catalog_points = axis_points[axis_i_catalog][:, :2]

                topo_axis_on_ocean = getAxisOnOcean(axis_i, sst_coords)
                topo_catalog_axis_on_ocean = getAxisOnOcean(axis_i_catalog_points, sst_coords)
                axis_i_ocean_sampled_precip = samplePrecipBelowWithR(topo_axis_on_ocean, precip_points, precip_vals, 1)
                axis_i_catalog_ocean_sampled_precip = samplePrecipBelowWithR(topo_catalog_axis_on_ocean, precip_points,
                                                                             precip_vals, 1)
                axis_i_sampled_precip = samplePrecipBelowWithR(axis_i, precip_points, precip_vals, 1)
                axis_i_catalog_sampled_precip = samplePrecipBelowWithR(axis_i_catalog_points, precip_points,
                                                                       precip_vals, 1)

                division_by_zeros = [len(axis_i_ocean_sampled_precip) > 0,
                                     len(axis_i_catalog_ocean_sampled_precip) > 0,
                                     len(axis_i_sampled_precip) > 0,
                                     len(axis_i_catalog_sampled_precip) > 0]

                if all(division_by_zeros):
                    our_axis_i_on_ocean = sum(axis_i_ocean_sampled_precip) / len(axis_i_ocean_sampled_precip)
                    catalog_axis_i_on_ocean = sum(axis_i_catalog_ocean_sampled_precip) / len(axis_i_catalog_ocean_sampled_precip)
                    our_axis_i_overall = sum(axis_i_sampled_precip) / len(axis_i_sampled_precip)
                    catalog_axis_i_overall = sum(axis_i_catalog_sampled_precip) / len(axis_i_catalog_sampled_precip)

                    our_axis_on_ocean.append(our_axis_i_on_ocean)
                    our_axis_on_ocean_sum.append(sum(axis_i_ocean_sampled_precip))
                    catalog_on_ocean.append(catalog_axis_i_on_ocean)
                    catalog_on_ocean_sum.append(sum(axis_i_catalog_ocean_sampled_precip))
                    our_axis_overall.append(our_axis_i_overall)
                    our_axis_overall_sum.append(sum(axis_i_sampled_precip))
                    catalog_overall.append(catalog_axis_i_overall)
                    catalog_overall_sum.append(sum(axis_i_catalog_sampled_precip))

                    # our_axis_on_ocean[str(time_step) + '_' + str(AR_id)] = (sum(axis_i_ocean_sampled_precip), our_axis_i_on_ocean)
                    # catalog_on_ocean[str(time_step) + '_' + str(AR_id)] = (sum(axis_i_catalog_ocean_sampled_precip), catalog_axis_i_on_ocean)
                    # our_axis_overall[str(time_step) + '_' + str(AR_id)] = (sum(axis_i_sampled_precip), our_axis_i_overall)
                    # catalog_overall[str(time_step) + '_' + str(AR_id)] = (sum(axis_i_catalog_sampled_precip), catalog_axis_i_overall)
                    # boxplot_on_ocean.append(our_axis_on_ocean - catalog_axis_on_ocean)
                    # boxplot_overall.append(our_axis - catalog_axis)


    # our_axis_on_ocean_fpath = open("IntermediateFiles/our_axis_on_ocean.pkl", "wb")
    # pickle.dump(our_axis_on_ocean, our_axis_on_ocean_fpath)
    # our_axis_on_ocean_fpath.close()
    # catalog_on_ocean_fpath = open("IntermediateFiles/catalog_on_ocean.pkl", "wb")
    # pickle.dump(catalog_on_ocean, catalog_on_ocean_fpath)
    # catalog_on_ocean_fpath.close()
    # our_axis_overall_fpath = open("IntermediateFiles/our_axis_overall.pkl", "wb")
    # pickle.dump(our_axis_overall, our_axis_overall_fpath)
    # our_axis_overall_fpath.close()
    # catalog_overall_fpath = open("IntermediateFiles/catalog_overall.pkl", "wb")
    # pickle.dump(catalog_overall, catalog_overall_fpath)
    # catalog_overall_fpath.close()

    print("Number of ARs", len(our_axis_overall))
    # fig_on_ocean = plt.figure()
    # plt.title("Captured Precipitation Difference On Ocean")
    # bp_on_ocean = plt.boxplot(boxplot_on_ocean, showmeans=True)
    # for key in bp_on_ocean:
    #     print(f'{key}: {[item.get_ydata() for item in bp_on_ocean[key]]}\n')
    # plt.savefig("figures/captured_precip_on_ocean_1.png")
    # plt.close(fig_on_ocean)
    #
    # fig_overall = plt.figure()
    # plt.title("Captured Precipitation Difference Overall")
    # bp_overall = plt.boxplot(boxplot_overall, showmeans=True)
    # for key in bp_overall:
    #     print(f'{key}: {[item.get_ydata() for item in bp_overall[key]]}\n')
    # plt.savefig("figures/captured_precip_overall_1.png")
    # plt.close(fig_overall)

    # plot ocean comparison average precipitation per pixel
    # fig_on_ocean, ax_ocean = plt.subplots()
    # plt.title("Captured Precipitation On Ocean")
    # bp_comparison_ocean_global = {'Topo': our_axis_on_ocean, 'Catalog': catalog_on_ocean}
    # ax_ocean.boxplot(bp_comparison_ocean_global.values(), showmeans=True)
    # ax_ocean.set_xticklabels(bp_comparison_ocean_global.keys())
    # plt.savefig("figures/captured_precipitation/ocean_comparision_" + str(start_day)+ "_" + str(end_day) + ".png")
    # plt.close(fig_on_ocean)

    # plot ocean comparison sum precipitation
    fig_on_ocean_sum, ax_ocean_sum = plt.subplots()
    plt.title("Total Captured Precipitation On Ocean")
    bp_comparison_ocean_sum = {'Topo': our_axis_on_ocean_sum, 'Catalog': catalog_on_ocean_sum}
    ax_ocean_sum.boxplot(bp_comparison_ocean_sum.values(), showmeans=True)
    ax_ocean_sum.set_xticklabels(bp_comparison_ocean_sum.keys())
    plt.savefig("figures/captured_precipitation/ocean_comparision_sum_" + str(start_day) + "_" + str(end_day) + ".png")
    plt.close(fig_on_ocean_sum)

    # fig_catalog_on_ocean = plt.figure()
    # plt.title("Captured Precipitation On Ocean (Catalog)")
    # bp_catalog_on_ocean = plt.boxplot(catalog_on_ocean, showmeans=True)
    # for key in bp_catalog_on_ocean:
    #     print(f'{key}: {[item.get_ydata() for item in bp_catalog_on_ocean[key]]}\n')
    # plt.savefig("figures/catalog_on_ocean.png")
    # plt.close(fig_catalog_on_ocean)

    # plot overall comparison average precipitation per pixel
    # fig_overall, ax_overall = plt.subplots()
    # plt.title("Captured Precipitation Overall")
    # bp_comparison_overall_global = {'Topo': our_axis_overall, 'Catalog': catalog_overall}
    # ax_overall.boxplot(bp_comparison_overall_global.values(), showmeans=True)
    # ax_overall.set_xticklabels(bp_comparison_overall_global.keys())
    # plt.savefig("figures/captured_precipitation/overall_comparison_" + str(start_day) + "_" + str(end_day) + ".png")
    # plt.close(fig_overall)

    # plot overall comparison sum precipitation
    fig_overall_sum, ax_overall_sum = plt.subplots()
    plt.title("Total Captured Precipitation Overall")
    bp_comparison_overall_sum = {'Topo': our_axis_overall_sum, 'Catalog': catalog_overall_sum}
    ax_overall_sum.boxplot(bp_comparison_overall_sum.values(), showmeans=True)
    ax_overall_sum.set_xticklabels(bp_comparison_overall_sum.keys())
    plt.savefig("figures/captured_precipitation/overall_comparison_sum_" + str(start_day) + "_" + str(end_day) + ".png")
    plt.close(fig_overall_sum)

    # fig_catalog_overall = plt.figure()
    # plt.title("Captured Precipitation Overall (Catalog)")
    # bp_catalog_overall = plt.boxplot(catalog_overall, showmeans=True)
    # for key in bp_catalog_overall:
    #     print(f'{key}: {[item.get_ydata() for item in bp_catalog_overall[key]]}\n')
    # plt.savefig("figures/catalog_overall.png")
    # plt.close(fig_catalog_overall)
