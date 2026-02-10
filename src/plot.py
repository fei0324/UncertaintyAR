import matplotlib.pyplot as plt
import json
import numpy as np

with open("Algorithms/ar_connect/IntermediateFiles/MSCSubset_2006_306_0_20/MSCShrunk_3.json", "r") as f:
    edges = json.load(f)
    x = []
    y = []
    for i, edge in edges.items():
        # print(edge.keys())
        for cell in edge['cells']:
            x.append(cell[0][0])
            y.append(cell[0][1])
            x.append(cell[1][0])
            y.append(cell[1][1])

    plt.scatter(x, y)
f.close()

with open("Algorithms/guan_waliser_v3/IntermediateFiles/MSCSubset_2006_306_0_20/MSCShrunk_4.json", "r") as f:
    edges = json.load(f)
    x = []
    y = []
    for i, edge in edges.items():
        # print(edge.keys())
        for cell in edge['cells']:
            x.append(cell[0][0])
            y.append(cell[0][1])
            x.append(cell[1][0])
            y.append(cell[1][1])

    plt.scatter(x, y)
f.close()

# IP_path = "IntermediateFiles/ARCP_1996_364_0/IP_furthest_3.npy"
# furthest_ips = np.load(IP_path)
# plt.scatter(*zip(*furthest_ips))

# AR_3_bound = np.load("IntermediateFiles/AR_3_boundary.npy")
# bound_x = []
# bound_y = []
# for point in AR_3_bound:
#     bound_x.append(point[0])
#     bound_y.append(point[1])
#
# plt.scatter(bound_x, bound_y)

# AR_3_bound_ordered = np.load("IntermediateFiles/ARBoundaries_1996_364_0/ARboundary_10.npy")
# bound_x = []
# bound_y = []
# for point in AR_3_bound_ordered:
#     bound_x.append(point[0])
#     bound_y.append(point[1])
# plt.scatter(bound_x, bound_y)

# AR_3_cp = np.load("IntermediateFiles/ARCP_1996_364_0/ARCP_coords_10.npy")
# print(AR_3_cp)
# cp_x = []
# cp_y = []
# for cp in AR_3_cp:
#     cp_x.append(cp[0])
#     cp_y.append(cp[1])
# plt.scatter(cp_x, cp_y)

# with open("IntermediateFiles/AR_3_intersection.json", "r") as file:
#     intersections = json.load(file)
#     ip_x = []
#     ip_y = []
#     for _, val in intersections.items():
#         for _, point in val.items():
#             ip_x.append(point[0])
#             ip_y.append(point[1])
#     plt.scatter(ip_x, ip_y)
# file.close()
plt.show()

    # for cp in AR_3_cp:
    #     cp_x.append(point[0])
    # plt.show()

