import numpy as np
import vtk
import vtk.util.numpy_support as VN
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import sys
import json
import seaborn_image as isns
import seaborn as sns
import pickle
import os


def getLevelFunctionFromARi(AR_points, AR_ids, AR_i_id):
    """
    Construct the level function for one AR
    :param AR_points: AR points array from the input AR file
    :param AR_ids: the "AR_shape" array from the AR file
    :param AR_i_id: the id of the specific AR
    :return: An array of size (576, 361) with points inside of the AR boundary set to 0 and outside set to 1
    """

    AR_i = np.where(AR_ids == int(AR_i_id))[0]
    points = AR_points[AR_i]
    AR_x = tuple(map(int, points[:, 0]))
    AR_y = tuple(map(int, points[:, 1]))
    level_function = np.ones((576, 361))
    level_function[(AR_x, AR_y)] = 0

    # np.save(save_path, level_function)
    return level_function


def choose2(x):
    return 1/8 * (2 * x - 1) ** 2 - 1/8


def get_combinations(n_ensembles):
    n_combination = int(choose2(n_ensembles))
    combinations = np.zeros([n_combination, 2], np.int32)
    count = 0
    for i in np.arange(n_ensembles):
        for j in np.arange(i+1, n_ensembles):
            combinations[count, 0] = i
            combinations[count, 1] = j
            count += 1
    return combinations


def epsilon_subset(A, B, eps):
    cardA = np.sum(A)
    return cardA == 0 or np.sum(np.bitwise_and(A,np.bitwise_not(B)))/cardA < eps


def contour_depth_time(data, combinations, n_ensembles, eps):
    depths = np.zeros([n_ensembles], np.float32)
    for tdx in np.arange(n_ensembles):
        target = data[tdx]
        for xdx, ydx in combinations:
            intersection = np.bitwise_and(data[xdx], data[ydx])
            union = np.bitwise_or(data[xdx], data[ydx])

            if (epsilon_subset(intersection, target, eps) and epsilon_subset(target, union, eps)):
                depths[tdx] += 1
    return depths


def parse_ensemble_json(ensemble_path):
    """
    Parse the ensemble json file to get the level functions
    :param ensemble_path:
    :return: level functions with dimension (n, y_dim, x_dim), n: number of ensemble members
    """
    level_functions = []
    readerAR = vtk.vtkXMLUnstructuredGridReader()
    f = open(ensemble_path)
    data = json.load(f)
    algo_dict = {}
    correspondence_dict = {}  # index in level_functions : index i in algorithm dict
    # records the correspondence between the entries of the level_functions and the original indices of the algorithms
    lf_counter = 0
    for i, entry in data.items():
        algo_name = entry['algo_name']
        algo_dict[int(i)] = algo_name
        print(algo_name)
        if entry['year'] != "none":
            correspondence_dict[lf_counter] = int(i)
            lf_counter += 1
            year = entry['year']
            # print(entry['day_hour_num'])
            for AR_i in entry['day_hour_num']:
                AR_i = eval(AR_i)  # turn string of tuple into tuple
                day = AR_i[0]
                hour = AR_i[1]
                AR_i_id = AR_i[2]
                inputAR = "Algorithms/" + algo_name + "/ARCatalog/ARCatalog_" + str(year) + \
                          "/shape/ARCatalog_" + str(year) + "_shape_" + str(day) + "_" + str(hour) + ".vtu"
                readerAR.SetFileName(inputAR)
                readerAR.Update()
                AR_i_output = readerAR.GetOutput()
                AR_i_points = VN.vtk_to_numpy(AR_i_output.GetPoints().GetData())
                AR_id_list = VN.vtk_to_numpy(AR_i_output.GetPointData().GetArray("AR_shape"))
                lf = getLevelFunctionFromARi(AR_i_points, AR_id_list, AR_i_id)
                level_functions.append(lf.T)

    level_functions = np.array(level_functions, dtype=np.int32)
    # print(len(level_functions_dict))
    # print(level_functions_dict)
    # print(level_functions.shape)
    # print(len(algo_dict))
    # print(correspondence_dict)

    return level_functions, algo_dict, correspondence_dict


def drawContourBoxplot(ensemble_path, color_dict, xlimit, ylimit, bands=[50,75,100]):

    level_functions, algo_dict, correspondence_dict = parse_ensemble_json(ensemble_path)
    level_functions = np.expand_dims(level_functions, axis=0)
    [times, n_ensembles, y_dim, x_dim] = level_functions.shape

    # Compute contour band depths
    epsilon = 0.001
    combinations = get_combinations(n_ensembles)
    data = level_functions[0]
    depths = contour_depth_time(data, combinations, n_ensembles, epsilon)
    print(depths)
    order = np.argsort(depths)[::-1]  # reverese the depth order so 0 is the median
    scores = depths[order]
    array_path = ensemble_path[:-5] + ".npy"
    pickle_path = ensemble_path[:-5] + "_dict" + ".pickle"
    algo_dict_path = ensemble_path[:-5] + "_algo" + ".pickle"
    print(array_path)
    print(correspondence_dict)
    np.save(array_path, order)
    with open(pickle_path, 'wb') as handle:
        pickle.dump(correspondence_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open(algo_dict_path, 'wb') as handle1:
        pickle.dump(algo_dict, handle1, protocol=pickle.HIGHEST_PROTOCOL)
    print('cbd order:', order)
    print('depths: ', scores)

    iqr = order[:n_ensembles // 2]
    print(iqr)

    image_data = level_functions[0]
    print(image_data.shape)
    # print(np.min(image_data[iqr], axis=0))

    int50 = np.min(image_data[iqr], axis=0)
    uni50 = np.max(image_data[iqr], axis=0)
    band50 = uni50 - int50
    print(band50.shape)

    seventyfive = order[:int(n_ensembles * (3/4))]
    # seventyfive = order[order[scores < (np.max(scores) - np.min(scores)) * 0.75 + np.min(scores)]]
    print(seventyfive)

    int75 = np.min(image_data[seventyfive], axis=0)
    uni75 = np.max(image_data[seventyfive], axis=0)
    band75 = uni75 - int75

    # ninety = order[order[scores < (np.max(scores) - np.min(scores)) + np.min(scores)]]
    # ninety = order[order[scores < (np.max(scores) - np.min(scores)) + np.min(scores)]]
    # print(ninety)
    int100 = np.min(image_data[order], axis=0)
    uni100 = np.max(image_data[order], axis=0)
    band100 = uni100 - int100

    # AR_mean = np.mean(image_data, axis=0)
    # AR_median = image_data[order[0]]

    isns.set_context("notebook")
    isns.set_image(cmap="rocket_r", origin="lower")

    ax = isns.imgplot(band50 + band75 + band100, cbar=False)
    ax.set_xlim(xlimit)
    ax.set_ylim(ylimit)

    band_colors = {0: "#040416", 1: "#94346c", 2: "#f47454"}
    band_proxy = []
    for i, band in enumerate(bands):
        i_patch = mpatches.Patch(color=band_colors[i], label=str(band) + "%")
        band_proxy.append(i_patch)
    plt.legend(handles=band_proxy, loc="lower right")

    img_name = ensemble_path[:-5].split("/")[-1]
    # print(contours_img_name)
    # plt.savefig("./CaseStudies/20061023/" + img_name + "_box.png")
    # plt.show()

    fig, ax1 = plt.subplots(figsize=(17, 10))
    proxy_artists = {}
    for i in range(len(order)):
        algo_index = correspondence_dict[order[i]]
        print(algo_dict[algo_index])
        ax1.contour(image_data[order[i]], levels=[0.5], origin='lower', colors=color_dict[algo_index], linewidths=4)
        ax1.set_xlim(xlimit)
        ax1.set_ylim(ylimit)

    algos_not_none = list(correspondence_dict.values())
    print(algos_not_none)
    for i, algo_name in algo_dict.items():
        if i in algos_not_none:
            i_patch = mpatches.Patch(color=color_dict[i], label=algo_name)
            proxy_artists[algo_name] = i_patch
        else:
            proxy_artists[algo_name] = mpatches.Rectangle((0, 0), 1, 1, fill=False, edgecolor='black', label=algo_name)
    plt.legend(handles=proxy_artists.values(), loc="lower right")

    # plt.imshow(band50, origin='lower', cmap='gray')
    # plt.imshow(band50 + band90, origin='lower', cmap='gray')
    # ax.contour(image_data[order[0]], levels=[0.5], origin='lower', colors='green')
    # ax.contour(AR_mean, levels=[0.5], origin='lower', colors='orange')
    # ax.contour(AR_median, levels=[1], origin='lower', colors='red')

    # plt.contour(image_data[order[0]], levels=[0], origin='lower')
    # plt.contour(image_data[order[0]], origin='lower')
    background_name = ensemble_path[:-4] + "png"
    background_img = plt.imread(background_name)
    plt.imshow(background_img, zorder=0, extent=[xlimit[0], xlimit[1], ylimit[1], ylimit[0]])
    # img_name = background_name.split("/")[-1]
    # plt.savefig("./CaseStudies/20061023/" + img_name + "_contours.png")
    # plt.show()


if __name__ == "__main__":

    color_dict = {0: "#1F77B4", 1: "#f7d42a", 2: "#2CA02C", 3: "#D62728", 4: "#9467BD", 5: "#8C564B", 6: "#E377C2",
                  7: "#7F7F7F", 8: "#BCBD22", 9: "#17BECF", 10: "#FF9896", 11: "#AEC7E8", 12: "#A699E8"}

    # Step 1: Generate contour boxplot data using the drawContourBoxplot function. Input the same json file.
    # drawContourBoxplot(".demo/2017_7_2.json", color_dict, [240, 410], [220, 320])
    # drawContourBoxplot("./Ensembles/20170107-0109/2017_8_3.json", color_dict, [240, 410], [220, 320])
    # drawContourBoxplot("./Ensembles/20061023-1024/2006_296_0.json", color_dict, [240, 410], [220, 320])

    # Step 2: Create contour boxplot
    # data_dir = "./Ensembles/20170107-0109"
    data_dir = "./Ensembles/20061023-1024"
    dict_files = []
    algo_files = []
    for file_name in os.listdir(data_dir):
        if file_name.endswith("_dict.pickle"):
            dict_files.append(file_name)
        if file_name.endswith("_algo.pickle"):
            algo_files.append(file_name)

    print(len(dict_files))
    print(len(algo_files))
    order_name_list = []  # the band_depth order (max to min) with algo names
    iqr_list = []
    seventyfive_list = []
    for file_name in os.listdir(data_dir):
        if file_name.endswith(".npy"):
            order = np.load(os.path.join(data_dir, file_name))
            print(order)
            time_step = file_name[:10]
            print(time_step)
            for dict_f in dict_files:
                if dict_f[:10] == time_step:
                    print(os.path.join(data_dir, dict_f))
                    with open(os.path.join(data_dir, dict_f), 'rb') as dict_handle:
                        lf2algo = pickle.load(dict_handle)
                        print(lf2algo)
            for algo_f in algo_files:
                if algo_f[:10] == time_step:
                    print(os.path.join(data_dir, algo_f))
                    with open(os.path.join(data_dir, algo_f), 'rb') as algo_handle:
                        algo_dict = pickle.load(algo_handle)
                        print(algo_dict)

            # make dict {level function index: algo name}
            lf2algoname = {}
            for lf, algo_index in lf2algo.items():
                lf2algoname[lf] = algo_dict[algo_index]
            print(lf2algoname)

            order_name = []
            for i, lf_index in enumerate(order):
                order_name.append(lf2algoname[lf_index])
            order_name_list.append(order_name)
            len_order = len(order_name)
            iqr_list.append(order_name[:len_order//2])
            seventyfive = order_name[len_order//2:int(len_order * (3 / 4))]
            seventyfive_list.append(seventyfive)
    print(len(order_name_list))
    print(len(iqr_list))
    print(iqr_list)
    print(seventyfive_list)

    algo_iqr_frequency = {'ar_connect': 0, 'climatenet': 0, 'guan_waliser_v3': 0, 'mundhenk_v3': 0, 'panlu': 0, 'reid500': 0,
    'rutz': 0, 'sail_v1': 0, 'teca_bard_v1.0.1': 0, 'tempest_250': 0, 'tempest_500': 0, 'tempest_700': 0, 'lora_v2': 0}
    algo_frequency = {'ar_connect': 0, 'climatenet': 0, 'guan_waliser_v3': 0, 'mundhenk_v3': 0, 'panlu': 0, 'reid500': 0,
    'rutz': 0, 'sail_v1': 0, 'teca_bard_v1.0.1': 0, 'tempest_250': 0, 'tempest_500': 0, 'tempest_700': 0, 'lora_v2': 0}
    algo_75_frequency = {'ar_connect': 0, 'climatenet': 0, 'guan_waliser_v3': 0, 'mundhenk_v3': 0, 'panlu': 0,
                          'reid500': 0, 'rutz': 0, 'sail_v1': 0, 'teca_bard_v1.0.1': 0, 'tempest_250': 0, 'tempest_500': 0,
                          'tempest_700': 0, 'lora_v2': 0}
    print(list(algo_frequency.keys()))
    for algo in list(algo_frequency.keys()):
        # print(algo)
        for order_name in order_name_list:
            if algo in order_name:
                algo_frequency[algo] += 1
        for iqr_arr in iqr_list:
            if algo in iqr_arr:
                algo_iqr_frequency[algo] += 1
        for seventyfive_arr in seventyfive_list:
            if algo in seventyfive_arr:
                algo_75_frequency[algo] += 1
    print(algo_frequency)
    print(algo_iqr_frequency)
    print(algo_75_frequency)
    algo_freq_list = list(algo_frequency.values())
    algo_iqr_freq_list = list(algo_iqr_frequency.values())
    algo_75_freq_list = list(algo_75_frequency.values())

    plt.style.use('ggplot')
    plot_colors = ["#1F77B4", "#FF710E", "#2CA02C"]
    fig, ax = plt.subplots()
    bottom = np.zeros(13)

    x = np.arange(13)
    ax.plot(x, algo_freq_list, 'o-', label="Total", color=plot_colors[2])
    algo_names = list(algo_iqr_frequency.keys())
    freq_bar_chart = {"IQR": algo_iqr_freq_list, "50-75th Percentile": algo_75_freq_list}

    width=0.8
    color_counter = 0
    for perc, freq in freq_bar_chart.items():
        p = ax.bar(algo_names, freq, width, label=perc, bottom=bottom, color=plot_colors[color_counter])
        bottom += freq
        color_counter += 1
    # plt.hist([list(algo_iqr_frequency.values()), list(algo_75_frequency.values())], bins=12, stacked=True)
    # plt.plot(x, )), label="ARDT 50-75% Frequency")
    ax.set_ylim([0, 7])
    ax.set_title("ARDT Identification Frequency for October 23-24, 2006")
    ax.title.set_size(12)
    ax.legend(loc="upper right")
    ax.set_xticks(x, algo_names, rotation=45, ha='right')
    plt.tight_layout()
    plt.show()


    """
    algo_frequency: {'ar_connect': 10, 'climatenet': 12, 'guan_waliser_v3': 12, 'mundhenk_v3': 12, 'panlu': 11, 'reid500': 8, 'rutz': 12, 'sail_v1': 5, 'teca_bard_v1.0.1': 8, 'tempest_250': 12, 'tempest_500': 11, 'tempest_700': 9}
    algo_iqr_frequency: {'ar_connect': 9, 'climatenet': 0, 'guan_waliser_v3': 0, 'mundhenk_v3': 11, 'panlu': 9, 'reid500': 4, 'rutz': 5, 'sail_v1': 0, 'teca_bard_v1.0.1': 6, 'tempest_250': 6, 'tempest_500': 8, 'tempest_700': 0}
    algo_75_frequency: {'ar_connect': 1, 'climatenet': 3, 'guan_waliser_v3': 2, 'mundhenk_v3': 1, 'panlu': 2, 'reid500': 4, 'rutz': 3, 'sail_v1': 0, 'teca_bard_v1.0.1': 2, 'tempest_250': 5, 'tempest_500': 3, 'tempest_700': 5}
    """










    # level_functions, algo_dict = parse_ensemble_json("Ensembles/2017_6_0.json")
    # # level_functions = parse_ensemble_json("Ensembles/2017_8_0.json")
    # level_functions = np.expand_dims(level_functions, axis=0)
    # # level_functions = level_functions.astype(np.int32)
    # # print(level_functions.shape)
    # #
    # [times, n_ensembles, y_dim, x_dim] = level_functions.shape
    #
    # # Compute contour band depths
    # epsilon = 0.001
    # combinations = get_combinations(n_ensembles)
    # data = level_functions[0]
    # depths = contour_depth_time(data, combinations, n_ensembles, epsilon)
    # print(depths)
    # order = np.argsort(depths)[::-1]  # reverese the depth order so 0 is the median
    # scores = depths[order]
    # print('cbd order:', order)
    # print('depths: ', scores)
    #
    # iqr = order[:n_ensembles // 2]
    # print(iqr)
    #
    # image_data = level_functions[0]
    # print(image_data.shape)
    # # print(np.min(image_data[iqr], axis=0))
    #
    # int50 = np.min(image_data[iqr], axis=0)
    # uni50 = np.max(image_data[iqr], axis=0)
    # band50 = uni50 - int50
    # print(band50.shape)
    #
    # # sixty = order[order[scores < (np.max(scores) - np.min(scores)) * 0.65 + np.min(scores)]]
    # #
    # # int60 = np.min(image_data[sixty], axis=0)
    # # uni60 = np.max(image_data[sixty], axis=0)
    # # band60 = uni60 - int60
    #
    # seventyfive = order[order[scores < (np.max(scores) - np.min(scores))*0.75 + np.min(scores)]]
    #
    # int75 = np.min(image_data[seventyfive], axis=0)
    # uni75 = np.max(image_data[seventyfive], axis=0)
    # band75 = uni75 - int75
    #
    # # ninety = order[order[scores < (np.max(scores) - np.min(scores)) + np.min(scores)]]
    # # ninety = order[order[scores < (np.max(scores) - np.min(scores)) + np.min(scores)]]
    # # print(ninety)
    # int100 = np.min(image_data[order], axis=0)
    # uni100 = np.max(image_data[order], axis=0)
    # band100 = uni100 - int100
    # # print(band100)
    #
    # # AR_mean = np.mean(image_data, axis=0)
    # AR_median = image_data[order[0]]
    #
    # isns.set_context("notebook")
    # isns.set_image(cmap="rocket_r", origin="lower")
    #
    # ax = isns.imgplot(band50 + band75 + band100, cbar=False)
    # # ax = isns.imgplot(band100)
    #
    # # fig, ax = plt.subplots()
    # # orange_purple = {0: "#FF9300", 1: "#34A853", 2: "#F62AA0", 3: "#EA4335"}
    # # palette = {0: "#4285F4", 1: "#34A853", 2: "#FBBC05", 3: "#EA4335"}
    # # palette = {0: "#1F77B4", 1: "#FF7F0E", 2: "#2CA02C", 3: "#D62728", 4: "#9467BD", 5: "#8C564B", 6: "#E377C2",
    # #               7: "#7F7F7F", 8: "#BCBD22", 9: "#17BECF", 10: "#FF9896", 11: "#AEC7E8", 12: "#FFBB78"}
    # # proxy_artists = []
    # # for i in range(len(order)):
    # #     print(algo_dict[order[i]])
    # #     ax.contour(image_data[order[i]], levels=[0.5], origin='lower', colors=palette[order[i]])
    # #
    # # for i in range(len(order)):
    # #     i_patch = mpatches.Patch(color=palette[i], label=algo_dict[i])
    # #     proxy_artists.append(i_patch)
    # # plt.legend(handles=proxy_artists, loc="lower right")
    #
    # # plt.imshow(band50, origin='lower', cmap='gray')
    # # plt.imshow(band50 + band90, origin='lower', cmap='gray')
    # # ax.contour(image_data[order[0]], levels=[0.5], origin='lower', colors='green')
    # # ax.contour(AR_mean, levels=[0.5], origin='lower', colors='orange')
    # # ax.contour(AR_median, levels=[1], origin='lower', colors='red')
    # ax.set_xlim([280, 450])
    # ax.set_ylim([190, 300])
    # # plt.contour(image_data[order[0]], levels=[0], origin='lower')
    # # plt.contour(image_data[order[0]], origin='lower')
    # plt.show()