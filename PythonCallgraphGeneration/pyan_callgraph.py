from glob import glob
import logging
import os
import networkx as nx
import matplotlib.pyplot as plt
import sys

sys.path.insert(0, './pyan')
from pyan import CallGraphVisitor


def main():
    #projectDir = './pyan'
    #projectDir = './TestProjects/Test_ObjectOriented'
    projectDir = './TestProjects/Test_Functional'


    # Exclude all python code that likely does not implement actual features of the project
    bannedFolders = ['Test', 'test', 'Tests', 'tests',
                      'venv', '__pycache__' ]
    bannedKeywords = ['Demo', 'demo', 'Example', 'example', 'Examples', 'examples', 'setup.py']

    filenames = [fn for fn in glob(projectDir + '/**/*.py', recursive=True)]
    filenames = [filename for filename in filenames if not set(bannedFolders) & set(filename.split(os.path.sep))]
    filenames = [filename for filename in filenames if not any([keyword in filename for keyword in bannedKeywords])]
    filenames = [os.path.abspath(filename) for filename in filenames]

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.ERROR)
    logger.addHandler(logging.StreamHandler())

    cg = CallGraphVisitor(filenames, logger=logger)

    # Create graph according to pyans analysis
    g = nx.DiGraph()
    for caller, callees in cg.uses_edges.items():
        for callee in callees:
            g.add_edge(str(caller), str(callee))


    # Calcualte eigenvector centrality and sort in descending order
    inDegrees = g.in_degree()
    outDegrees = g.out_degree()

    g = g.to_undirected()

    evCentrality = nx.eigenvector_centrality(g, max_iter=1000)
    #Functions that call many functions shall be more important than functions that are called by many functions
    #This helps disregarding utility functions like logger functions
    for node in evCentrality:
        factor = 0.2 + 0.8 * (outDegrees[node] / (outDegrees[node] + inDegrees[node]))
        evCentrality[node] = evCentrality[node] * factor
    evCentrality = {k: v for k, v in sorted(evCentrality.items(), key=lambda item: item[1], reverse=True)}
    print(evCentrality)


    # When a special node is of interest in the visualization, this will show only names of the node and its neighbors
    nameToAnalyze = ''
    minCentrality = 0
    nameMap = None
    if nameToAnalyze != '':
        nameMap = {}
        for caller, callees in cg.uses_edges.items():
            calleeNames = [str(callee) for callee in callees]
            if str(caller) == nameToAnalyze or nameToAnalyze in calleeNames:
                nameMap[str(caller)] = str(caller)
            elif str(caller) not in nameMap:
                nameMap[str(caller)] = ''

            for callee in callees:
                if str(caller) == nameToAnalyze or str(callee) == nameToAnalyze:
                    nameMap[str(callee)] = str(callee)
                elif str(callee) not in nameMap:
                    nameMap[str(callee)] = ''

    if minCentrality != 0:
        for node in g.nodes:
            nameMap = {} if nameMap is None else nameMap
            if evCentrality[node] >= minCentrality:
                nameMap[node] = node

    # Draw the graph
    g = g.to_undirected()
    pos = nx.nx_agraph.graphviz_layout(g)

    nx.draw_networkx_nodes(g, pos, node_size=[evCentrality[node] * 1000 for node in g.nodes], node_color='#8FBAC8')
    nx.draw_networkx_edges(g, pos, node_size=0, width=1, edge_color='lightgrey')
    nx.draw_networkx_labels(g, pos, font_size=8, labels=nameMap)

    nx.drawing.nx_pylab.draw(g)
    plt.show()


if __name__ == "__main__":
    main()