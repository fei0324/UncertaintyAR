import json
import matplotlib.pyplot as plt
from src.constructGraph import constructG
import numpy as np
import math
import networkx as nx
# from sortedcollections import OrderedSet
import matplotlib.patches as mpatches
# from mpl_toolkits.basemap import Basemap

# from getContourBoxplot import getLevelFunctionFromARi
import vtk
import vtk.util.numpy_support as VN


def constructMetroSetGraph(mscShrunk):
    """
    The goal of this function is to simplify the original AR skeleton from the MSC for the MetroSet visualization
    We use the graph constructed from the MSC
    TODO: Can change the input here to be a saved graph, instead of the msc json file
    First we pick the stations to be the boundary points (degree 1) and the intersection points (degree > 2) of the skeleton
    Then we use breadth first search to connect these stations while respecting the topology of the original skeleton
    :param mscShrunk: mscShrunk file
    :return: G_simplified - a networkx graph that includes the stations and the new edges
    """

    # pick the stations to be the boundary points and the intersection points
    G = constructG(mscShrunk)
    boundary_nodes = {}
    intersection_nodes = {}
    for node_id, node_degree in G.degree(G.nodes):
        if node_degree == 1:
            boundary_nodes[node_id] = G.nodes[node_id]['coordinate']
        if node_degree > 2:
            intersection_nodes[node_id] = G.nodes[node_id]['coordinate']

    station_dict = {**boundary_nodes, **intersection_nodes}

    G_simplified = nx.Graph()
    G_simplified.add_nodes_from([(id, {'coordinate': coord}) for (id, coord) in station_dict.items()])

    # check if intersection nodes exist
    if intersection_nodes:
        # do breadth first search in G starting from each of the intersection nodes
        # find the closest neighbors in G_simplified based on the original degree of the node
        for node_id in G_simplified.nodes:
            # print(node_id)
            G_neighbors = [n for n in G.neighbors(node_id)]
            # ignore the boundary nodes
            if len(G_neighbors) == 1:
                continue
            num_neighbors_needed = G.degree(node_id)
            # take into account the neighbors that are already added from previous searches
            G_sim_neighbors = list(G_simplified.neighbors(node_id))
            visited = set()
            queue = [node_id]
            # print("queue", queue)
            # TODO: Figure out why the queue is empty sometimes
            while len(G_sim_neighbors) < num_neighbors_needed and len(queue) > 0:
                current_node = queue.pop(0)
                # print("current node in while", current_node)
                # print("visited", current_node in visited)
                if current_node not in visited:
                    # avoid adding the node we start with into the list of neighbors
                    if current_node in G_simplified.nodes and current_node != node_id:
                        G_sim_neighbors.append(current_node)
                    visited.add(current_node)
                    # print("current node:", current_node)
                    # print("visited", visited)
                    current_neighbors = [n for n in G.neighbors(current_node)]
                    # as we trace the paths starting from the initial node, if we've already found a neighbor on this path,
                    # we stop the search on this path. In other words, we cannot have multiple neighbors on the same path
                    if len(set(current_neighbors) & set(G_sim_neighbors)) > 0:
                        continue
                    for G_n in current_neighbors:
                        # print("G_n", G_n)
                        # print("G simplified neighbors:", G_sim_neighbors)
                        if G_n not in visited:
                            queue.append(G_n)
            for G_sim_n in G_sim_neighbors:
                G_simplified.add_edge(node_id, G_sim_n)
    else:
        # if there are no intersection nodes, there are only two boundary nodes in the graph, connect them with an edge
        assert len(station_dict) == 2
        node_ids = list(station_dict.keys())
        G_simplified.add_edge(node_ids[0], node_ids[1])
    # nx.draw(G, pos=nx.get_node_attributes(G, 'coordinate'), node_size=7, width=4)
    # nx.draw(G_simplified, pos=nx.get_node_attributes(G_simplified, 'coordinate'), node_color='orange', node_size=7, edge_color='red', width=5)
    # plt.show()

    return G_simplified


def constructMultigraph(G_list):
    """
    Construct a grpah from an input of a list of metroset graphs.
    The edges of this graph has attributes
        "algo" = [0, 1, 2, ...] that contains the list of algorithms that produced an skeleton with this edge
        "weight = len("algo")
    :param G_list: a list of metroset graphs constructed from constructMetroSetGraph() in the format of (G, algo_i)
    :return: a nx.Graph() that includes all the nodes and edges from the input graphs
    """
    G_multigraph = nx.Graph()
    G_multi_nodes = {}  # {coords: multigraph node id}
    node_id_counter = 0
    for (G, algo_i) in G_list:
        G_node_dict = {}  # match multigraph to individual graph node ids {G node id: multigraph node id}
        G_coords = nx.get_node_attributes(G, 'coordinate')
        for G_node_id in G.nodes:
            if G_coords[G_node_id] not in G_multi_nodes.keys():
                G_multigraph.add_node(node_id_counter, coordinate=G_coords[G_node_id])
                G_multi_nodes[G_coords[G_node_id]] = node_id_counter
                G_node_dict[G_node_id] = node_id_counter
                node_id_counter += 1
            else:
                G_multi_node_id = G_multi_nodes[G_coords[G_node_id]]
                G_node_dict[G_node_id] = G_multi_node_id
        for (pt0, pt1) in G.edges:
            pt0_multigraph = G_node_dict[pt0]
            pt1_multigraph = G_node_dict[pt1]
            if G_multigraph.has_edge(pt0_multigraph, pt1_multigraph):
                G_multigraph.edges[pt0_multigraph, pt1_multigraph]["algo"].append(algo_i)
                G_multigraph.edges[pt0_multigraph, pt1_multigraph]["weight"] += 1
            else:
                G_multigraph.add_edge(pt0_multigraph, pt1_multigraph, algo=[algo_i], weight=1)
        # print(nx.get_edge_attributes(G_multigraph, 'algo'))
        # print(nx.get_edge_attributes(G_multigraph, 'weight'))
        # G_multi_edge_weights = [G_multigraph[u][v]['weight']*1.3 for u, v in G_multigraph.edges]
        # nx.draw(G_multigraph, pos=nx.get_node_attributes(G_multigraph, 'coordinate'), node_color='black', node_size=7,
        #     edge_color='orange', width=G_multi_edge_weights)
        # plt.show()

    return G_multigraph


def groupNeighbors(multigraph):
    """
    For nodes with degree > 3 (these are the boundary edges), we group them together based on how close they are to
    each other.
    :param multigraph: the graph we constructed from a list of skeletons
    :return: a dictionary of the groupings of the neighbors around each node with degree > 3
        {node_id: [{n1, n2}, {n3, n4, n5}, ...]} The groups should be disjoint around each node.
    """
    edge_algos = nx.get_edge_attributes(multigraph, "algo")  # the indices (i, j) is always ordered i < j
    node_coord_list = nx.get_node_attributes(multigraph, "coordinate")
    neighbor_group_dict = {}
    for node_id, node_degree in multigraph.degree():
        node_coord = node_coord_list[node_id]
        if node_degree > 3:
            all_algos = set()
            current_neighbors = [n for n in multigraph.neighbors(node_id)]
            n_vector_dict = {}
            neighbor_groups = []
            for n in current_neighbors:
                n_algos = edge_algos[(n, node_id)] if n < node_id else edge_algos[(node_id, n)]
                all_algos.update(n_algos)

            for n in current_neighbors:
                edge_key = (n, node_id) if n < node_id else (node_id, n)
                n_algos = edge_algos[edge_key]
                # if an edge contains all the algos present at the current node, skip the edge
                # this is because two edges of the same algorithm should not be grouped into the same edge
                difference_algos = [i for i in all_algos if i not in n_algos]
                if not difference_algos:
                    continue

                # construct a vector for n using node coordinates
                n_coord = node_coord_list[n]
                n_vector = np.subtract(n_coord, node_coord)
                n_vector_dict[n] = n_vector

            # compute pairwise angle between all neighboring vectors
            num_vectors = len(n_vector_dict)
            pairwise_angles = np.zeros((num_vectors, num_vectors))
            pairwise_angles_dict = dict(zip(np.arange(num_vectors), list(n_vector_dict.keys())))
            # print(pairwise_angles_dict)

            for i in range(num_vectors):
                for j in range(i + 1, num_vectors):
                    vi = n_vector_dict[pairwise_angles_dict[i]]
                    vj = n_vector_dict[pairwise_angles_dict[j]]
                    pairwise_angles[i, j] = pairwise_angles[j, i] = _getAngle(vi, vj)
            np.fill_diagonal(pairwise_angles, np.inf)
            # get the pairwise matchings for each neighboring edge
            matchings = list(zip(np.arange(num_vectors), np.argmin(pairwise_angles, axis=1)))
            # group the pairings so we have groups of neighbors that will be snapped into one edge
            # print(matchings)
            for pair in matchings:
                # if the list is empty
                if not neighbor_groups:
                    neighbor_groups.append(set(pair))
                # if the current pair does not intersect with any of the existing sets
                elif not any([set(pair).intersection(n_group) for n_group in neighbor_groups]):
                    neighbor_groups.append(set(pair))
                else:
                    for n_group in neighbor_groups:
                        if set(pair).intersection(n_group):
                            n_group.update(pair)
            # print("final neighbor groups", neighbor_groups)

            # neighbor_groups is currently written in the index of pairwise_angles, convert it back to node_id
            for i, n_group in enumerate(neighbor_groups):
                n_group = set(pairwise_angles_dict[x] for x in n_group)
                neighbor_groups[i] = n_group
            # print(neighbor_groups)
            neighbor_group_dict[node_id] = neighbor_groups

    # G_multi_edge_weights = [multigraph[u][v]['weight'] * 1.3 for u, v in multigraph.edges]
    # nx.draw(multigraph, pos=nx.get_node_attributes(multigraph, 'coordinate'), node_color='black',
    #         node_size=7, with_labels=True,
    #         edge_color='orange', width=G_multi_edge_weights)
    # plt.show()

    return neighbor_group_dict


def _getAngle(v1, v2):
    unit_v1 = v1/np.linalg.norm(v1)
    unit_v2 = v2/np.linalg.norm(v2)
    dot_product = np.dot(unit_v1, unit_v2)
    angle = np.arccos(dot_product)
    return angle


def redefineMultigrpah(multigraph, neighbor_group_dict):
    """
    Reorganize the boundary edges that we realigned. Flatten and reconnect these edges instead of overlay them.
    Update the "algo" attribut in these edges
    :param multigraph: multigraph from constructMultigraph()
    :param neighbor_group_dict: neighbor group dictionary from groupNeighbors()
    :return: an updated multigraph
    """
    edge_algos = nx.get_edge_attributes(multigraph, "algo")
    node_coords = nx.get_node_attributes(multigraph, "coordinate")
    edges_to_remove = []
    for node_id, neightbor_groups in neighbor_group_dict.items():
        # print("central node", node_id)
        node_coord = np.array(node_coords[node_id])
        for n_group in neightbor_groups:
            edge_length_dict = {}
            for neighbor_id in n_group:
                neighbor_coord = node_coords[neighbor_id]
                edge_length = np.linalg.norm(np.array(neighbor_coord) - node_coord)
                edge_length_dict[neighbor_id] = edge_length
            # sort the lengths from smallest to largest
            sorted_lengths = np.argsort(np.array(list(edge_length_dict.values())))
            # print(sorted_lengths)

            # project all edges in one group onto the longest edge
            # sorted neighbor ids from shortest to longest edge
            sorted_neighbor_ids = [list(edge_length_dict.keys())[i] for i in sorted_lengths]
            # print(list(edge_length_dict.keys()))
            # print(sorted_neighbor_ids)
            max_neighbor_id = sorted_neighbor_ids[-1]
            v1 = np.array(node_coords[max_neighbor_id]) - node_coord

            # get the "algo" attribute for the neighbor group
            n_group_algo = {}
            max_edge_key = (node_id, max_neighbor_id) if node_id < max_neighbor_id else (max_neighbor_id, node_id)
            n_group_algo[max_neighbor_id] = edge_algos[max_edge_key]

            # exclude the longest edge since all other edges will project onto this edge
            for neighbor_id in sorted_neighbor_ids[:-1]:
                # neighbor_id = list(edge_length_dict.keys())[sorted_lengths[i]]
                v2 = np.array(node_coords[neighbor_id]) - node_coord
                ortho_proj = _orthogonalProjection(v1, v2)
                new_neighbor_coord = ortho_proj + node_coord
                multigraph.nodes[neighbor_id]['coordinate'] = (new_neighbor_coord[0], new_neighbor_coord[1])

                neighbor_edge_key = (node_id, neighbor_id) if node_id < neighbor_id else (neighbor_id, node_id)
                n_group_algo[neighbor_id] = edge_algos[neighbor_edge_key]

            # update edges and the "algo" edge attribute
            # update the "algo" attribute for the shortest edge to be all the algos from all edges in the same group
            min_neighbor_id = sorted_neighbor_ids[0]
            min_edge_key = (node_id, min_neighbor_id) if node_id < min_neighbor_id else (min_neighbor_id, node_id)
            min_edge_algos = list(set(sum(list(n_group_algo.values()), [])))
            # print(min_edge_algos)
            multigraph.edges[min_edge_key]['algo'] = min_edge_algos
            multigraph.edges[min_edge_key]['weight'] = len(min_edge_algos)
            # add the new edges on the boundary to the graph
            for i in range(len(sorted_neighbor_ids) - 1):
                neighbor_id = sorted_neighbor_ids[i]
                next_neighbor_id = sorted_neighbor_ids[i + 1]
                all_neighbors_after = sorted_neighbor_ids[(i + 1):]
                # print(all_neighbors_after)
                # print(n_group_algo)
                new_edge_algos = [list(n_group_algo[j]) for j in all_neighbors_after]
                new_edge_algos = list(set(sum(new_edge_algos, [])))
                # print("new edge key", neighbor_id, next_neighbor_id, "new edge algos", new_edge_algos)
                multigraph.add_edge(neighbor_id, next_neighbor_id, algo=new_edge_algos, weight=len(new_edge_algos))
                edges_to_remove.append((node_id, next_neighbor_id))

    for u, v in edges_to_remove:
        if multigraph.has_edge(u, v):
            multigraph.remove_edge(u, v)
        # else:
        #     print("no edge", u, v)

    # G_multi_edge_weights = [multigraph[u][v]['weight'] * 1.5 for u, v in multigraph.edges]
    # degree_list = [d*3+3 for (_, d) in multigraph.degree()]
    # nx.draw(multigraph, pos=nx.get_node_attributes(multigraph, 'coordinate'), node_color='black',
    #         node_size=degree_list,
    #         edge_color='orange', width=G_multi_edge_weights)
    # plt.show()

    return multigraph


def _orthogonalProjection(v1, v2):
    """
    Compute the orthogonal projection of v2 onto v1
    :param v1: the vector to be projected on. We need to compute its projection matrix.
    :param v2: the vector to project onto v1.
    :return: a vector
    """
    projection_mat = np.outer(v1, v1) / v1.dot(v1)
    ortho_proj = projection_mat.dot(v2.T)

    return ortho_proj


def separateGraphs(multigraph_cleaned, num_algos, num_algos_wo_none, increment, edge_width):
    """
    Separate the cleaned multigraph into a dictionary of graphs and add offset value for each edge.
    Each graph is from a separate algorithm.
    :param increment: used to compute offset. Increment is how much we offset for two edges from adjacent algorithms
    :param multigraph_cleaned: reorganized and updated multigraph from redefineMultigraph()
    :param num_algos: number of algorithms
    :return: a dictionary {algo_id: graph_cleaned}
        a graph with all the thick edges that contain all the algorithms, if the number of algorithms is larger than 5
        We separate these edges to visualize them as single edges instead of a bundle of edges.
    """
    graph_dict = {}
    for i in range(num_algos):
        graph_dict[i] = nx.Graph()

    # If nhe number of algorithms is more than 5, add edges with all the present algorithms in the this separate graph.
    thick_edge_graph = nx.Graph()

    node_coords = nx.get_node_attributes(multigraph_cleaned, 'coordinate')
    edge_algos_list = nx.get_edge_attributes(multigraph_cleaned, 'algo')
    for edge_tuple in multigraph_cleaned.edges:
        edge_algos = sorted(edge_algos_list[edge_tuple])
        num_algos_on_edge = len(edge_algos)
        if num_algos_wo_none == num_algos_on_edge:
            thick_edge_graph.add_edge(edge_tuple[0], edge_tuple[1])
            thick_edge_graph.add_node(edge_tuple[0], coordinate=node_coords[edge_tuple[0]])
            thick_edge_graph.add_node(edge_tuple[1], coordinate=node_coords[edge_tuple[1]])
        else:
            # if the edge has an odd number of algorithms, center is the middle edge
            if num_algos_on_edge % 2 == 1:
                # [0, 1, 2] center_index = 1
                center_index = num_algos_on_edge // 2
            else:
                # [0, 1, 2, 3] center is between 1 and 2
                center_index = num_algos_on_edge // 2 - 0.5
            for i, algo in enumerate(edge_algos):
                graph_algo = graph_dict[algo]
                if num_algos_on_edge > 5:
                    smaller_increment = increment*(5/num_algos_on_edge)
                    # thinner_width = edge_width*(5/num_algos_on_edge)
                    thinner_width = edge_width - 0.2
                    # print(edge_tuple)
                    # print(num_algos_on_edge)
                    # print(thinner_width)
                    graph_algo.add_edge(edge_tuple[0], edge_tuple[1],
                                        offset=(center_index - i) * smaller_increment, width=thinner_width)
                else:
                    # print(edge_tuple)
                    # print(num_algos_on_edge)
                    # print(edge_width)
                    graph_algo.add_edge(edge_tuple[0], edge_tuple[1],
                                        offset=(center_index - i) * increment, width=edge_width)
                graph_algo.add_node(edge_tuple[0], coordinate=node_coords[edge_tuple[0]])
                graph_algo.add_node(edge_tuple[1], coordinate=node_coords[edge_tuple[1]])
    # colors = {2: 'orange', 1: 'red', 3: 'green', 0: 'blue'}
    # for i in range(num_algos):
    #     graph_algo = graph_dict[i]
    #     nx.draw(graph_algo, pos=nx.get_node_attributes(graph_algo, 'coordinate'), node_color='black',
    #             node_size=7,
    #             edge_color=colors[i], width=3)
    # plt.show()
    return graph_dict, thick_edge_graph


def constructShiftedGraph(graph_cleaned):

    # nx.draw(graph_cleaned, pos=nx.get_node_attributes(graph_cleaned, 'coordinate'), node_color='black',
    #         node_size=7,
    #         edge_color='orange', width=3)

    """
    Construct MetroSet visualization by shifting the original edges to avoid overlapping edges
    :param graph_cleaned: a cleaned graph from one algorithm
    :return: a new graph with shifted edges.
        This new graph actually has a lot more edges and nodes than the original and its not connected.
        All the edges are individual edges not connected to other edges.
        The nodes for each edge are separate from the nodes for other adjacent edges.
    """

    shifted_graph = nx.Graph()
    node_coords = nx.get_node_attributes(graph_cleaned, 'coordinate')
    edge_offset_list = nx.get_edge_attributes(graph_cleaned, 'offset')
    edge_width_list = nx.get_edge_attributes(graph_cleaned, 'width')
    node_id_counter = 0
    for (pt0, pt1) in graph_cleaned.edges:
        edge_offset = edge_offset_list[(pt0, pt1)]
        print(edge_offset)
        print(edge_width_list[(pt0, pt1)])
        pt0_coord = node_coords[pt0]
        pt1_coord = node_coords[pt1]
        w = edge_width_list[(pt0, pt1)]  # edge width
        # slope is undefined shift left and right
        if math.isclose((pt1_coord[0] - pt0_coord[0]), 0, abs_tol=1e-05):
            pt0_shifted = node_id_counter
            shifted_graph.add_node(pt0_shifted, coordinate=(pt0_coord[0] + edge_offset*w, pt0_coord[1]))
            node_id_counter += 1
            pt1_shifted = node_id_counter
            shifted_graph.add_node(pt1_shifted, coordinate=(pt1_coord[0] + edge_offset*w, pt1_coord[1]))
            node_id_counter += 1
            shifted_graph.add_edge(pt0_shifted, pt1_shifted, width=edge_width_list[(pt0, pt1)])
        else:
            slope = (pt1_coord[1] - pt0_coord[1]) / (pt1_coord[0] - pt0_coord[0])
            # slope is 0 shift up and down
            if math.isclose(slope, 0, abs_tol=1e-05):
                pt0_shifted = node_id_counter
                shifted_graph.add_node(pt0_shifted, coordinate=(pt0_coord[0], pt0_coord[1] - edge_offset*w))
                node_id_counter += 1
                pt1_shifted = node_id_counter
                shifted_graph.add_node(pt1_shifted, coordinate=(pt1_coord[0], pt1_coord[1] - edge_offset*w))
                node_id_counter += 1
                shifted_graph.add_edge(pt0_shifted, pt1_shifted, width=edge_width_list[(pt0, pt1)])
            # if the edge not vertical or horizontal, need to shift both x and y
            else:
                x_offset = -1 * slope * w * edge_offset / np.sqrt(1 + slope ** 2)
                y_offset = w * edge_offset / np.sqrt(1 + slope ** 2)
                if slope > 0:
                    # x_offset = edge_offset / (1 + 1 / slope)
                    # y_offset = (edge_offset * (1 / slope)) / (1 + 1 / slope)
                    pt0_shifted = node_id_counter
                    shifted_graph.add_node(pt0_shifted, coordinate=(pt0_coord[0] - x_offset, pt0_coord[1] - y_offset))
                    node_id_counter += 1
                    pt1_shifted = node_id_counter
                    shifted_graph.add_node(pt1_shifted, coordinate=(pt1_coord[0] - x_offset, pt1_coord[1] - y_offset))
                    node_id_counter += 1
                    shifted_graph.add_edge(pt0_shifted, pt1_shifted, width=w)
                else:
                    # x_offset = edge_offset * (-1 / (1 - 1 / slope))
                    # y_offset = edge_offset * ((1 / slope) / (1 - 1 / slope))
                    pt0_shifted = node_id_counter
                    shifted_graph.add_node(pt0_shifted, coordinate=(pt0_coord[0] - x_offset, pt0_coord[1] - y_offset))
                    node_id_counter += 1
                    pt1_shifted = node_id_counter
                    shifted_graph.add_node(pt1_shifted, coordinate=(pt1_coord[0] - x_offset, pt1_coord[1] - y_offset))
                    node_id_counter += 1
                    shifted_graph.add_edge(pt0_shifted, pt1_shifted, width=w)

    return shifted_graph

    # nx.draw(shifted_graph, pos=nx.get_node_attributes(shifted_graph, 'coordinate'), node_color='black',
    #         node_size=15,
    #         edge_color='red', width=5)
    # plt.show()


def addNodeSize(multigraph_cleaned):

    edge_algos = nx.get_edge_attributes(multigraph_cleaned, "algo")
    node_size = {}
    for node_id in multigraph_cleaned.nodes:
        node_neighbors = [n for n in multigraph_cleaned.neighbors(node_id)]
        max_algo_length = 0
        for n_neighbor in node_neighbors:
            edge_key = (node_id, n_neighbor) if node_id < n_neighbor else (n_neighbor, node_id)
            if len(edge_algos[edge_key]) > max_algo_length:
                # stop growing node size when the number of algorithms is larger than 5
                if len(edge_algos[edge_key]) > 5:
                    max_algo_length = 5
                else:
                    max_algo_length = len(edge_algos[edge_key])
        node_size[node_id] = max_algo_length
    # for id, size in node_size.items():
    #     print(id, size)
    nx.set_node_attributes(multigraph_cleaned, node_size, "size")

    return multigraph_cleaned


def drawFromJSON(ensemble_path, sim_threshold, color_dict, xlimit, ylimit):
    f = open(ensemble_path)
    data = json.load(f)
    G_list = []
    num_algos_total = 0
    for i, entry in data.items():
        algo_name = entry['algo_name']
        if entry['year'] != "none":
            year = entry['year']
            num_algos_total += 1
            for AR_i in entry['day_hour_num']:
                AR_i = eval(AR_i)  # turn string of tuple into tuple
                day = AR_i[0]
                hour = AR_i[1]
                AR_i_id = AR_i[2]
                AR_msc_path = open("Algorithms/" + algo_name + "/IntermediateFiles/MSCSubset_" + str(year) + "_" + str(day)
                                   + "_" + str(hour) + "_" + str(sim_threshold) + "/MSCShrunk_" + str(AR_i_id) + ".json")
                AR_msc = json.load(AR_msc_path)
                AR_metroset = constructMetroSetGraph(AR_msc)
                G_list.append((AR_metroset, int(i)))

                # for adding contours to the individual AR plot
                # inputAR = "Algorithms/" + algo_name + "/ARCatalog/ARCatalog_" + str(year) + \
                #           "/shape/ARCatalog_" + str(year) + "_shape_" + str(day) + "_" + str(hour) + ".vtu"
                # readerAR = vtk.vtkXMLUnstructuredGridReader()
                # readerAR.SetFileName(inputAR)
                # readerAR.Update()
                # AR_i_output = readerAR.GetOutput()
                # AR_i_points = VN.vtk_to_numpy(AR_i_output.GetPoints().GetData())
                # AR_id_list = VN.vtk_to_numpy(AR_i_output.GetPointData().GetArray("AR_shape"))
                # lf = getLevelFunctionFromARi(AR_i_points, AR_id_list, AR_i_id)
                # lf = lf.T
                # plt.contour(lf, levels=[0.5], origin='lower', colors='black', linewidths=2)
                # plt.xlim(xlimit)
                # plt.ylim(ylimit)
                # # draw graph for each algorithm
                # nx.draw(AR_metroset, pos=nx.get_node_attributes(AR_metroset, 'coordinate'), node_color='black',
                #         node_size=20,
                #         edge_color=color_dict[int(i)], width=5)

            # add background to individual graph
            # background_name = ensemble_path[:-4] + "png"
            # print(background_name)
            # background_img = plt.imread(background_name)
            # plt.imshow(background_img, zorder=0, extent=[xlimit[0], xlimit[1], ylimit[1], ylimit[0]])
            # img_name = background_name.split("/")[-1]
            # plt.savefig("./PVIS2024/figs/" + str(algo_name) + ".png", bbox_inches='tight', dpi=300)
            # plt.show()
    # print(G_list)
    G_multi = constructMultigraph(G_list)
    # nx.draw(G_multi, pos=nx.get_node_attributes(G_multi, 'coordinate'), node_color='black',
    #         node_size=20,
    #         edge_color='orange', width=5)
    # plt.show()
    neighbor_group_dict = groupNeighbors(G_multi)
    multigraph_cleaned = redefineMultigrpah(G_multi, neighbor_group_dict)
    multigraph_cleaned = addNodeSize(multigraph_cleaned)
    # print(multigraph_cleaned)
    graph_dict, thick_edge_graph = separateGraphs(multigraph_cleaned, len(data), num_algos_total, 0.13, 3)

    plt.figure(figsize=(17, 10))
    proxy_artists = {}
    for i, graph in graph_dict.items():
        algo_name = data[str(i)]['algo_name']
        shifted_graph = constructShiftedGraph(graph)
        edge_width_list = list(nx.get_edge_attributes(shifted_graph, 'width').values())
        # print(edge_width_list)
        nx.draw_networkx(shifted_graph, pos=nx.get_node_attributes(shifted_graph, 'coordinate'), node_color='black',
                node_size=0, with_labels=False,
                edge_color=color_dict[i], width=edge_width_list,
                label=algo_name)

        if algo_name not in proxy_artists.keys():
            if data[str(i)]['year'] == "none":
                proxy_artists[algo_name] = mpatches.Rectangle((0, 0), 1, 1, fill=False, edgecolor='black', label=algo_name)
            else:
                proxy_artists[algo_name] = mpatches.Patch(color=color_dict[i], label=algo_name)
    # print(proxy_artists)
    plt.legend(handles=proxy_artists.values(), loc="lower right")

    nx.draw_networkx(thick_edge_graph, pos=nx.get_node_attributes(thick_edge_graph, 'coordinate'), node_color='black',
                     node_size=0, with_labels=False, edge_color='orange', width=10)
    node_size_list = [i**2.4 + i*1.2 for i in list(nx.get_node_attributes(multigraph_cleaned, 'size').values())]
    whitenode_size_list = [i**2 for i in list(nx.get_node_attributes(multigraph_cleaned, 'size').values())]
    nx.draw_networkx_nodes(multigraph_cleaned, pos=nx.get_node_attributes(multigraph_cleaned, 'coordinate'),
                           node_color='#4C4E52', node_size=node_size_list)
    nx.draw_networkx_nodes(multigraph_cleaned, pos=nx.get_node_attributes(multigraph_cleaned, 'coordinate'),
                           node_color='white', node_size=whitenode_size_list)

    plt.xlim(xlimit)
    plt.ylim(ylimit)

    # add background
    background_name = ensemble_path[:-4] + "png"
    print(background_name)
    background_img = plt.imread(background_name)
    # plt.imshow(background_img, zorder=0, extent=[xlimit[0], xlimit[1], ylimit[0], ylimit[1]])
    plt.imshow(background_img, zorder=0, extent=[xlimit[0], xlimit[1], ylimit[0], ylimit[1]])
    img_name = background_name.split("/")[-1]
    # plt.savefig("./CaseStudies/20061023/" + img_name, bbox_inches='tight')
    # plt.savefig("./CaseStudies/20170107/" + img_name, bbox_inches='tight')
    # plt.savefig("./PVIS2024/figs/method-metroset.png", bbox_inches='tight', dpi=300)

    plt.savefig("./figures/metrosets/" + img_name, bbox_inches='tight')

    plt.show()


if __name__ == "__main__":

    color_dict = {0: "#1F77B4", 1: "#f7d42a", 2: "#2CA02C", 3: "#D62728", 4: "#9467BD", 5: "#8C564B", 6: "#E377C2",
                  7: "#7F7F7F", 8: "#BCBD22", 9: "#17BECF", 10: "#FF9896", 11: "#AEC7E8", 12: "#A699E8"}
    # color_dict = {0: "#1F77B4", 1: "#FF7F0E", 2: "#2CA02C", 3: "#D62728", 4: "#9467BD", 5: "#8C564B", 6: "#E377C2",
    #               7: "#7F7F7F", 8: "#BCBD22", 9: "#17BECF", 10: "#FF9896", 11: "#AEC7E8"}
    # drawFromJSON("Ensembles/2006_308_0_4algo.json", 20, color_dict)

    drawFromJSON("./demo/2017_7_2.json", 30, color_dict, [328, 430], [210, 290])

    # drawFromJSON("./Ensembles/20140212-0216/2014_45_0.json", 30, color_dict, [295, 420], [205, 290])
    # drawFromJSON("./Ensembles/20140212-0216/2014_45_0.json", 30, color_dict, [290, 422], [200, 290])
    # drawFromJSON("./Ensembles/20170107-0109/2017_7_1.json", 30, color_dict, [328, 430], [210, 290])
    # drawFromJSON("./Ensembles/20170107-0109/2017_7_2.json", 30, color_dict, [328, 430], [210, 290])
    # drawFromJSON("./Ensembles/20170107-0109/2017_7_3.json", 30, color_dict, [328, 430], [210, 290])
    # drawFromJSON("./Ensembles/20170107-0109/2017_8_0.json", 30, color_dict, [328, 430], [210, 290])
    # drawFromJSON("./Ensembles/20061023-1024/2006_295_0.json", 20, color_dict, [252, 390], [224, 302])
    # drawFromJSON("./Ensembles/20061023-1024/2006_295_1.json", 20, color_dict, [252, 390], [224, 302])
    # drawFromJSON("./Ensembles/20061023-1024/2006_295_2.json", 20, color_dict, [252, 390], [224, 302])
    # drawFromJSON("./Ensembles/20061023-1024/2006_295_3.json", 20, color_dict, [252, 390], [224, 302])
    # drawFromJSON("./Ensembles/20061023-1024/2006_296_0.json", 20, color_dict, [252, 390], [224, 302])

    # guan_waliser_path_1 = open("./Algorithms/guan_waliser_v3/IntermediateFiles/MSCSubset_2006_306_0_20/MSCShrunk_4.json")
    # gw_msc_1 = json.load(guan_waliser_path_1)
    # gw_1_metroset = constructMetroSetGraph(gw_msc_1)
    # nx.draw(gw_1_metroset, pos=nx.get_node_attributes(gw_1_metroset, 'coordinate'), node_color='black', node_size=20,
    #         edge_color=color_dict[0], width=5)
    # guan_waliser_path_2 = open(
    #     "./Algorithms/guan_waliser_v3/IntermediateFiles/MSCSubset_2006_306_0_20/MSCShrunk_13.json")
    # gw_msc_2 = json.load(guan_waliser_path_2)
    # gw_2_metroset = constructMetroSetGraph(gw_msc_2)
    # nx.draw(gw_2_metroset, pos=nx.get_node_attributes(gw_2_metroset, 'coordinate'), node_color='black', node_size=20,
    #         edge_color=color_dict[0], width=5)
    # plt.show()
    # ar_path = open("./Algorithms/ar_connect/IntermediateFiles/MSCSubset_2006_306_0_20/MSCShrunk_3.json")
    # ar_msc = json.load(ar_path)
    # ar_metroset = constructMetroSetGraph(ar_msc)
    # nx.draw(ar_metroset, pos=nx.get_node_attributes(ar_metroset, 'coordinate'), node_color='black', node_size=20,
    #         edge_color=color_dict[1], width=5)
    # plt.show()
    # mundhenk_path = open("./Algorithms/mundhenk_v3/IntermediateFiles/MSCSubset_2006_306_0_20/MSCShrunk_9.json")
    # mundhenk_msc = json.load(mundhenk_path)
    # mundhenk_metroset = constructMetroSetGraph(mundhenk_msc)
    # nx.draw(mundhenk_metroset, pos=nx.get_node_attributes(mundhenk_metroset, 'coordinate'), node_color='black', node_size=20,
    #         edge_color=color_dict[2], width=5)
    # plt.show()
    # teca_path = open("./Algorithms/teca_bard_v1.0.1/IntermediateFiles/MSCSubset_2006_306_0_20/MSCShrunk_4.json")
    # teca_msc = json.load(teca_path)
    # teca_metroset = constructMetroSetGraph(teca_msc)
    # nx.draw(teca_metroset, pos=nx.get_node_attributes(teca_metroset, 'coordinate'), node_color='black', node_size=20,
    #         edge_color=color_dict[3], width=5)
    # plt.show()
    # G_list = [(gw_1_metroset, 0), (gw_2_metroset, 0), (ar_metroset, 1), (mundhenk_metroset, 2), (teca_metroset, 3)]
    # algo_dict = {0: "guan_waliser_v3", 1: "ar_connect", 2: "mundhenk", 3: "teca_bard_v1.0.1"}
    #
    # G_multi = constructMultigraph(G_list)
    # neighbor_group_dict = groupNeighbors(G_multi)
    # multigraph_cleaned = redefineMultigrpah(G_multi, neighbor_group_dict)
    # multigraph_cleaned = addNodeSize(multigraph_cleaned)
    # print(multigraph_cleaned)
    # graph_dict = separateGraphs(multigraph_cleaned, 4, 0.4)
    # # color_dict = {0: "#1F77B4", 1: "#FF7F0E", 2: "#2CA02C", 3: "#D62728"}
    # for i, graph in graph_dict.items():
    #     shifted_graph = constructShiftedGraph(graph)
    #     nx.draw_networkx(shifted_graph, pos=nx.get_node_attributes(shifted_graph, 'coordinate'), node_color='black',
    #             node_size=0, with_labels=False,
    #             edge_color=color_dict[i], width=4,
    #             label=algo_dict[i])
    # plt.legend(loc="lower right")
    # node_size_list = [i**3.5+10 for i in list(nx.get_node_attributes(multigraph_cleaned, 'size').values())]
    # whitenode_size_list = [i**2.8 for i in list(nx.get_node_attributes(multigraph_cleaned, 'size').values())]
    # print(node_size_list)
    # nx.draw_networkx_nodes(multigraph_cleaned, pos=nx.get_node_attributes(multigraph_cleaned, 'coordinate'),
    #                        node_color='#4C4E52', node_size=node_size_list)
    # nx.draw_networkx_nodes(multigraph_cleaned, pos=nx.get_node_attributes(multigraph_cleaned, 'coordinate'),
    #                        node_color='white', node_size=whitenode_size_list)
    # plt.show()

    # ar_path = open("./Algorithms/guan_waliser_v3/IntermediateFiles/MSCSubset_2006_306_0_20/MSCShrunk_4.json")
    # ar_msc = json.load(ar_path)
    # arcp = np.load("./Algorithms/ar_connect/IntermediateFiles/ARCP_2006_306_0_20/ARCP_coords_3.npy")

    # x = []
    # y = []
    # for i, edge in ar_msc.items():
    #     # print(edge.keys())
    #     for cell in edge['cells']:
    #         x.append(cell[0][0])
    #         y.append(cell[0][1])
    #         x.append(cell[1][0])
    #         y.append(cell[1][1])
    #
    # plt.scatter(x, y)

    # metroset_graph = constructMetroSetGraph(ar_msc)
    # nx.draw(metroset_graph, pos=nx.get_node_attributes(metroset_graph, 'coordinate'), node_color='orange', node_size=7, edge_color='red', width=3)
    # plt.show()

    # metroSetStations = []
    #
    # for i in range(len(ar_connect_msc)):
    #     for cell in ar_connect_msc[str(i)]['cells']:
    #         if cell[0][0] % 5 == 0:
    #             metroSetStations.append(cell[0])
    # print(metroSetStations)
    #
    # x = []
    # y = []
    # for pt in metroSetStations:
    #     x.append(pt[0])
    #     y.append(pt[1])
    #
    # plt.scatter(x, y)
    # # plt.show()
    #
    # boundary_coords, intersection_coords = findBoundaryPoints(ar_msc)
    # x = []
    # y = []
    # for pt in boundary_coords:
    #     x.append(pt[0])
    #     y.append(pt[1])
    #
    # plt.scatter(x, y)
    # x = []
    # y = []
    # for pt in intersection_coords:
    #     x.append(pt[0])
    #     y.append(pt[1])
    #
    # plt.scatter(x, y)
    # plt.show()

    # connectInteriorStations(ar_connect_msc)
    # connectCP(ar_connect_msc, arcp)