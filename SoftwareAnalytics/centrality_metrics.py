import networkx as nx

def eigenvector_centrality(graph):
    return nx.eigenvector_centrality(graph.to_undirected(), max_iter=1000)

def eigenvector_centrality_weighted(graph):
    in_degrees = graph.in_degree()
    out_degrees = graph.out_degree()

    evCentrality = eigenvector_centrality(graph)

    for node in evCentrality:
        factor = 0.2 + 0.8 * (out_degrees[node] / (out_degrees[node] + in_degrees[node]))
        evCentrality[node] = evCentrality[node] * factor

    return evCentrality

def eigenvector_centrality_weighted_edges(graph):
    weighted_graph = nx.DiGraph()

    for caller, callee in graph.edges():
        weighted_graph.add_edge(caller, callee, weight=0.1)
        weighted_graph.add_edge(callee, caller, weight=1)

    return nx.eigenvector_centrality(weighted_graph, max_iter=1000, weight='weight')

def pagerank(graph):
    return nx.pagerank(graph.to_undirected(), max_iter=1000)


def inverse_pagerank(graph):
    centrality = pagerank(graph)
    return {node: 1/(val+0.000001) for node, val in centrality.items()}


def degeneracy(graph):
    graph2 = nx.DiGraph(graph)
    graph2.remove_edges_from(nx.selfloop_edges(graph2))
    core = nx.core_number(graph2)
    core = {key: val/10 for key, val in core.items()}
    return core


def katz_centrality(graph):
    return nx.katz_centrality(graph, max_iter=1000)


def reverse_katz_centrality(graph):
    return katz_centrality(graph.reverse())


def harmonic_centrality(graph):
    return nx.harmonic_centrality(graph)


def inverse_harmonic_centrality(graph):
    centrality = nx.harmonic_centrality(graph)
    return {node: 1/(val+0.000001) for node, val in centrality.items()}


def closeness_centrality(graph):
    return nx.closeness_centrality(graph)


def reverse_closeness_centrality(graph):
    return closeness_centrality(graph.reverse())


def degree_centrality(graph):
    return nx.degree_centrality(graph)


def out_degree_centrality(graph):
    return nx.out_degree_centrality(graph)


def second_order_centrality(graph):
    undirected = graph.to_undirected()
    largest_cc = max(nx.connected_components(undirected), key=len)
    return nx.second_order_centrality(undirected.subgraph(largest_cc))


def inverse_second_order_centrality(graph):
    centrality = second_order_centrality(graph)
    return {node: 1/(val+0.000001) for node, val in centrality.items()}


def local_reaching_centrality(graph):
    return {node: nx.local_reaching_centrality(graph, node) for node in graph}


def ensemble_revKatz_revCloseness_outDeg_localReaching(graph):
    metrics = []
    metrics.append(eigenvector_centrality(graph))
    metrics.append(reverse_katz_centrality(graph))
    metrics.append(reverse_closeness_centrality(graph))
    metrics.append(out_degree_centrality(graph))
    metrics.append(local_reaching_centrality(graph))

    # Normalize centrality scores
    for i in range(len(metrics)):
        min_val = min(metrics[i].values())
        max_val = max(metrics[i].values())
        val_range = max_val - min_val
        metrics[i] = {name: (score-min_val)/val_range for name, score in metrics[i].items()}

    centrality = {}
    for function in graph:
        score = sum([metric[function] for metric in metrics])
        centrality[function] = score

    return centrality