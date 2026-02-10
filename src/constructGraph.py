import numpy as np
import networkx as nx
import json
import math
# from pyevtk.hl import linesToVTK
import vtk
import copy as cp
import sys
import matplotlib.pyplot as plt


def constructG(mscShrunk):
    """
    Construct an undirected graph from the msc subset inside of the AR boundary. Sometimes
    :param mscShrunk: the msc subset inside of the AR boundary
    :return: an undirected graph with nodes and edges from the msc subset,
        and edge weights being the Euclidean distance between the endpoints of each edge.
    """
    # The msc subset might contain partially overlapping segments, here we get the unique points first
    pointset = set()

    for i, segment in mscShrunk.items():
        for cell in segment['cells']:
            pointset.add(tuple(cell[0]))
            pointset.add(tuple(cell[1]))

    indices = np.arange(len(pointset))
    point_dict = dict(zip(pointset, indices))

    G = nx.Graph()
    G.add_nodes_from([(id, {'coordinate': coord[:2]}) for (coord, id) in point_dict.items()])

    for i, segment in mscShrunk.items():
        for cell in segment['cells']:
            start_p = tuple(cell[0])
            end_p = tuple(cell[1])
            edge_weight = math.dist(start_p, end_p)
            G.add_edge(point_dict[start_p], point_dict[end_p], weight=edge_weight)

    return G


# def findAxis(G):
#     """
#     Extract the axis from the constructed undirected graph
#     :param G: input undirected graph constructed from constructG
#     :return: path graph with node attribute 'coordinate'
#     """
#
#     pos = nx.get_node_attributes(G, 'coordinate')
#     # print(G.edges.data())
#     print("Computing all_pairs_dijkstra_path_length")
#     path_lengths = dict(nx.all_pairs_dijkstra_path_length(G, weight='weight'))
#     max_length = 0
#     # max_dict = {}
#     for source, target_dict in path_lengths.items():
#         max_target = max(target_dict, key=target_dict.get)
#         if target_dict[max_target] > max_length:
#             max_length = target_dict[max_target]
#             max_path = (source, max_target)
#             # max_dict[max_length] = max_path
#     # second_max_length = sorted(max_dict.keys())[1]
#     # second_max_path = max_dict[second_max_length]
#     # print(second_max_path)
#     axis = nx.dijkstra_path(G, source=max_path[0], target=max_path[1], weight='weight')
#     # axis = nx.dijkstra_path(G, source=second_max_path[0], target=second_max_path[1], weight='weight')
#     # print(axis)
#     path_g = nx.path_graph(axis)
#     # print(path_g.edges)
#     path_g_pos = {axis_i: pos[axis_i] for axis_i in axis}
#     for node in path_g.nodes:
#         path_g.nodes[node]['coordinate'] = path_g_pos[node]
#     # print(path_g.nodes.data())
#     # print(path_g.number_of_edges())
#     # print(path_g.number_of_nodes())
#     # print(path_g.edges)
#
#     # nx.draw(graph, pos=pos, node_size=5)
#     # nx.draw(path_g, pos=path_g_pos, node_size=5, node_color='red')
#     # plt.show()
#
#     return path_g


def findAxis(G, ip_furthest, outfile):
    """
    Extract the axis from the constructed undirected graph using the intersection points furthest away from each other
    :param G: input undirected graph constructed from constructG
    :return: save the axis coordinates into a .npy file
        path graph with node attribute 'coordinate'
    """

    pos = nx.get_node_attributes(G, 'coordinate')
    west_IP = tuple(ip_furthest[0])
    east_IP = tuple(ip_furthest[1])
    west_IP_id = list(pos.keys())[list(pos.values()).index(west_IP)]
    east_IP_id = list(pos.keys())[list(pos.values()).index(east_IP)]
    # print(west_IP_id)
    # print(east_IP_id)
    # print(pos[west_IP_id])
    # print(pos[east_IP_id])
    # for i, pos_val in enumerate(list(pos.values())):
    #     if pos_val == east_IP:
    #         print(i)
    # print(list(pos.values()))

    axis = nx.shortest_path(G, west_IP_id, east_IP_id, weight='weight')
    np.save(outfile, [pos[axis_i] for axis_i in axis], allow_pickle=True)

    path_g = nx.path_graph(axis)
    # print(path_g.edges)
    path_g_pos = {axis_i: pos[axis_i] for axis_i in axis}
    # print(path_g_pos)
    for node in path_g.nodes:
        path_g.nodes[node]['coordinate'] = path_g_pos[node]
    # print(path_g.nodes.data())
    # print(path_g.number_of_edges())
    # print(path_g.number_of_nodes())
    # print(path_g.edges)

    # nx.draw(G, pos=pos, node_size=5)
    # nx.draw(path_g, pos=path_g_pos, node_size=5, node_color='red')
    # plt.show()

    return path_g


def relabelPointIds(G):
    """
    The ids of the nodes of the graph need to be consecutive integers starting from 0
    :param G: input graph
    :return: the relabeled graph with nodes being consecutive integers starting from 0
        the node attributes and edges are the same as the corresponding ones in G
    """
    if max(G.nodes) == G.number_of_nodes() - 1:
        return G
    else:
        relabeled_G = nx.Graph()
        relabel_node_dict = {}
        for i, original_node_id in enumerate(G.nodes):
            relabel_node_dict[original_node_id] = i
            coord = G.nodes[original_node_id]['coordinate']
            relabeled_G.add_node(i, coordinate=coord)

        for edge in G.edges:
            relabeled_G.add_edge(relabel_node_dict[edge[0]], relabel_node_dict[edge[1]])
        return relabeled_G


def graph2vtu(G, outfile):
    """
    Make graph G or path graph into a .vtp file
    :param outfile: the outfile path
    :param G: the graph G from constructG() or the path graph from findAxis()
        the nodes need to have the attribute 'coordinate' in 2d
    :return: a .vtp file that line up with the ivt file
    """
    G = relabelPointIds(G)
    assert max(G.nodes) == G.number_of_nodes() - 1

    points = vtk.vtkPoints()
    # points.SetNumberOfPoints(G.number_of_nodes())
    line = vtk.vtkLine()
    cells = vtk.vtkCellArray()

    for i, node in enumerate(G.nodes):
        coord_2d = G.nodes[node]['coordinate']
        # print(coord_2d)
        points.InsertNextPoint(coord_2d[0], coord_2d[1], 0.)

    for i, edge in enumerate(G.edges):
        # print(edge)
        line.GetPointIds().SetId(0, edge[0])
        line.GetPointIds().SetId(1, edge[1])
        cells.InsertNextCell(line)
    poly = vtk.vtkPolyData()
    poly.SetPoints(points)
    poly.SetLines(cells)

    writer = vtk.vtkXMLPolyDataWriter()
    writer.SetFileName(outfile)
    writer.SetInputData(poly)
    writer.Write()


def getSkeletonAxis():

    MSC_subset_dir = sys.argv[1]
    AR_id = sys.argv[2]
    CP_outdir = sys.argv[3]
    graph_axis_outdir = sys.argv[4]

    MSC_shrunk_filepath = MSC_subset_dir + "MSCShrunk_" + AR_id + ".json"
    ip_furthest_filepath = CP_outdir + "IP_furthest_" + AR_id + ".npy"
    graph_filepath = graph_axis_outdir + "skeleton_" + AR_id + ".vtp"
    axis_filepath = graph_axis_outdir + "axis_" + AR_id + ".vtp"
    axis_nppath = graph_axis_outdir + "axis_" + AR_id + ".npy"

    with open(MSC_shrunk_filepath, "r") as f:
        msc = json.load(f)
        graph = constructG(msc)
        graph2vtu(graph, graph_filepath)
        ip_furthest = np.load(ip_furthest_filepath)
        path_g = findAxis(graph, ip_furthest, axis_nppath)
        graph2vtu(path_g, axis_filepath)


if __name__ == "__main__":

    getSkeletonAxis()

    # with open("Algorithms/guan_waliser_v3/IntermediateFiles/MSCSubset_1996_0_0/MSCShrunk_6.json", "r") as f:
    #     msc = json.load(f)
    #     graph = constructG(msc)
        # graph2vtu(graph)
        # ip_furthest = np.load("Algorithms/guan_waliser_v3/IntermediateFiles/ARCP_1996_0_0/IP_furthest_6.npy")
        # ip_furthest = [[418.5, 209], [423.5, 215]]
        # axis_nppath = "Algorithms/guan_waliser_v3/GraphAxis/GraphAxis_1996_0_0/axis_6.npy"
        # print(ip_furthest)
        # print(graph[70])
        # for pt in ip_furthest:
        #     plt.scatter(pt[0], pt[1], c='orange')
        # path_g = findAxis(graph, ip_furthest, axis_nppath)
        # graph2vtu(path_g, "test_path_g.vtp")
        # print(path_g)
        # print(path_g.edges.data())
        # print(path_g.edges[1694, 989]['weight'])


        # print(path_pos)
        # pos = nx.get_node_attributes(graph, 'coordinate')
        # print(pos)
        # nx.draw(graph, pos=pos, node_size=5)
        # plt.show()
        # print(graph.nodes())
        # print("Computing all_pairs_dijkstra_path")
        # paths = dict(nx.all_pairs_dijkstra_path(graph, weight='weight'))
        # print("Computing all_pairs_dijkstra_path_length")
        # path_lengths = dict(nx.all_pairs_dijkstra_path_length(graph, weight='weight'))
        # max_length = 0
        # for source, target_dict in path_lengths.items():
        #     max_target = max(target_dict, key=target_dict.get)
        #     if target_dict[max_target] > max_length:
        #         max_length = target_dict[max_target]
        #         print(max_length)
        #         max_path = (source, max_target)
        #         print(max_path)
        # # print(max_path)
        # # print(max_length)
        # # print(path_lengths[max_path[0]][max_path[1]])
        # axis = nx.dijkstra_path(graph, source=max_path[0], target=max_path[1], weight='weight')
        # path_g = nx.path_graph(axis)
        # # print(path_g.nodes())
        # path_g_pos = {axis_i: pos[axis_i] for axis_i in axis}
        # # print(len(path_g_pos))
        # nx.draw(path_g, pos=path_g_pos, node_size=5, node_color='red')
        # plt.show()
    #
    #     # print(paths.value())
    #
    # # G = nx.path_graph(5)
    # # path = dict(nx.all_pairs_shortest_path(G))
    # # print(path[0])
