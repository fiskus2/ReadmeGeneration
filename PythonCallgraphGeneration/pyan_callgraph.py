# Constructs a callgraph of a python projects, calculates the eigenvector centrality of all functions and displays the graph
from glob import glob
import logging
import os
import networkx as nx
import matplotlib.pyplot as plt
import sys
from modulegraph import modulegraph

sys.path.insert(0, './pyan')
from pyan import CallGraphVisitor
from pyan import anutils

# Exclude all python code that likely does not implement actual features of the project
def get_source_files(projectDir):
    banned_folders = ['Test', 'test', 'Tests', 'tests',
                     'venv', '__pycache__']
    banned_keywords = ['Demo', 'demo', 'Example', 'example', 'Examples', 'examples', 'setup.py']

    filenames = [fn for fn in glob(projectDir + '/**/*.py', recursive=True)]
    filenames = [filename for filename in filenames if not set(banned_folders) & set(filename.split(os.path.sep))]
    filenames = [filename for filename in filenames if not any([keyword in filename for keyword in banned_keywords])]
    filenames = [os.path.abspath(filename) for filename in filenames]
    return filenames

#Create a callgraph using pyan
def make_callgraph(filenames, debugLog=False):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG if debugLog else logging.ERROR)
    logger.addHandler(logging.StreamHandler())

    return CallGraphVisitor(filenames, logger=logger)

#Creates a networkx graph from a callgraph created by pyan
def make_networkx_graph(callgraph):
    g = nx.DiGraph()
    for caller, callees in callgraph.uses_edges.items():
        for callee in callees:
            g.add_edge(str(caller), str(callee))

    return g

#Creates a networkx graph from an importgraph created by modulegraph
def make_module_graph(filenames):
    modules = {file: anutils.get_module_name(file) for file in filenames}
    paths = [file[:file.rfind('/')] for file in filenames]

    modg = modulegraph.ModuleGraph(paths)
    for file in filenames:
        modg.run_script(file)
        pass

    graph = nx.DiGraph()
    for edge in list(modg.graph.edges.values()):
        try:
            importer = str(modules[edge[0]] if edge[0] in modules else edge[0])
            if importer == '<ModuleGraph>':
                continue

            imported = edge[1]
            if edge[1][0:2] == '..':
                imported = imported[2:]
                if '.' in importer:
                    ns = importer[:importer.rfind('.')]
                    if '.' in ns:
                        ns = ns[:ns.rfind('.') + 1]
                        imported = ns + imported

            if edge[1][0] == '.':
                imported = imported[1:]
                if '.' in importer:
                    imported = importer[:importer.rfind('.') + 1] + imported

            graph.add_edge(importer, imported)
        except KeyError:
            print('Unknown module: ' + str(edge[0]))

    return graph


def display_module_graph(graph, centrality, hideLeaves=False):
    # When a special node is of interest in the visualization, this will show only names of the node and its neighbors

    # Draw the graph
    pos = nx.nx_agraph.graphviz_layout(graph)

    if hideLeaves:
        edge_color = '#A0A0A0'
        node_color = '#3030FF'
    else:
        edge_color = []
        for edge in graph.edges:
            edge_color.append('#E9E9E9' if graph.out_degree()[edge[1]] == 0 else '#A0A0A0')

        node_color = []
        for node in graph:
            node_color.append('#B0B0FF' if graph.out_degree()[node] == 0 else '#3030FF')

    nameMap=None


    nx.draw_networkx_nodes(graph, pos, node_size=[centrality[node] * 1000 for node in graph.nodes], node_color=node_color)
    nx.draw_networkx_edges(graph, pos, node_size=0, width=1, edge_color=edge_color, arrowsize=20)
    nx.draw_networkx_labels(graph, pos, font_size=8, labels=nameMap, alpha=0.5)

    plt.show()


#Calculates the eigenvector centrality weighted by the out degree of a networkx graph
def weighted_centrality(graph):
    in_degrees = graph.in_degree()
    out_degrees = graph.out_degree()

    graph = graph.to_undirected()

    evCentrality = nx.eigenvector_centrality(graph, max_iter=1000)

    # Functions that call many functions shall be more important than functions that are called by many functions
    # This helps disregarding utility functions like logger functions
    for node in evCentrality:
        factor = 0.2 + 0.8 * (out_degrees[node] / (out_degrees[node] + in_degrees[node]))
        evCentrality[node] = evCentrality[node] * factor
    evCentrality = {k: v for k, v in sorted(evCentrality.items(), key=lambda item: item[1], reverse=True)}
    return evCentrality


def display_graph(graph, callgraph, centrality, short_names=True, hide_leaves=False):
    # When a special node is of interest in the visualization, this will show only names of the node and its neighbors
    name_to_analyze = ''
    show_callers = True
    show_callees = True

    # Additionally shows all nodes above a certain centrality
    min_centrality = 0

    if hide_leaves:
        newGraph = nx.DiGraph()
        for edge in graph.edges:
            if graph.out_degree()[edge[1]] > 0:
                newGraph.add_edge(edge[0], edge[1])
        graph = newGraph

    name_map = None
    if name_to_analyze != '':
        name_map = {}
        for caller, callees in callgraph.uses_edges.items():
            callee_names = [str(callee) for callee in callees]
            if (
                    name_to_analyze in str(caller)
                    or (show_callers and name_to_analyze in callee_names)
            ):
                name_map[str(caller)] = str(caller)
            elif str(caller) not in name_map:
                name_map[str(caller)] = ''

            for callee in callees:
                if (
                        (show_callees and name_to_analyze in str(caller))
                        or name_to_analyze in str(callee)
                ):
                    name_map[str(callee)] = str(callee)
                elif str(callee) not in name_map:
                    name_map[str(callee)] = ''

    if min_centrality != 0:
        for node in graph.nodes:
            name_map = {} if name_map is None else name_map
            if centrality[node] >= min_centrality:
                name_map[node] = node

    if short_names:
        name_map = {node: node[node.rfind('.', 0, node.rfind('.') - 1)+1 : -1] for node in graph}

    # Draw the graph
    pos = nx.nx_agraph.graphviz_layout(graph)

    if hide_leaves:
        edge_color = '#A0A0A0'
        node_color = '#3030FF'
    else:
        edge_color = []
        for edge in graph.edges:
            edge_color.append('#E9E9E9' if graph.out_degree()[edge[1]] == 0 else '#A0A0A0')

        node_color = []
        for node in graph:
            node_color.append('#B0B0FF' if graph.out_degree()[node] == 0 else '#3030FF')


    nx.draw_networkx_nodes(graph, pos, node_size=[centrality[node] * 1000 for node in graph.nodes], node_color=node_color)
    nx.draw_networkx_edges(graph, pos, node_size=0, width=1, edge_color=edge_color, arrowsize=20)
    nx.draw_networkx_labels(graph, pos, font_size=8, labels=name_map, alpha=0.5)

    plt.show()


#Try to determine the module of a function such that pyan and modulegraph agree
def get_module_of_function(function, module_graph):
    if function[0] == '<' and ':' in function:
        function = function[function.find(':') + 1: function.rfind('.')]

    if function not in module_graph:
        if '.' in function:
            function = function[: function.rfind('.')]
            return get_module_of_function(function, module_graph)
        else:
            return None
    else:
        return function


def main():
    #projectDir = './pyan'
    #projectDir = './TestProjects/Test_ObjectOriented'
    projectDir = './TestProjects/Test_Functional'
    #projectDir = './TestProjects/betterbib'

    filenames = get_source_files(projectDir)
    callgraph = make_callgraph(filenames)

    mg = make_module_graph(filenames)
    mg_centrality = weighted_centrality(mg)
    display_module_graph(mg, mg_centrality, hideLeaves=False)
    graph = make_networkx_graph(callgraph)


    undetermined_module = set()
    for node in graph:
        name = node[node.find(':') + 1: node.rfind('.')]
        if name not in mg_centrality:
            if '.' in name:
                name = name[: name.rfind('.')]
            else:
                undetermined_module.add(name)
            if name not in mg_centrality:
                undetermined_module.add(name)

    print('Module not determinable for:')
    for name in undetermined_module:
        print(name)

    centrality = weighted_centrality(graph)
    print(centrality)
    display_graph(graph, callgraph, centrality, hide_leaves=False)


if __name__ == "__main__":
    main()