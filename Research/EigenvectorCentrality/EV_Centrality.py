import networkx as nx
import matplotlib.pyplot as plt

with open('callgraph.txt') as file:
    input = file.readlines()

# Remove everything that is not a function call made by the project
inputs = [line for line in input if line.startswith('M:com.airsquared.blobsaver')]

# Remove if the called function is not a function of the projet
inputs = [line for line in inputs if ')com.airsquared.blobsaver' in line]

# Remove lambda expressions
inputs = [line for line in inputs if 'lambda$' not in line]

# Split caller and callee
split = [line.split(' ') for line in inputs]
caller = [elem[0] for elem in split]
callee = [elem[1] for elem in split]

# Functions with the same name but from a different class shall be separate nodes in the network.
# The Graph library shall therefore identify the methods by their fully qualified name, while displaying a simple name
# For this purpose the nameMap shall map fully qualified names to simple names
callerSimple = [line[line.rfind(':')+1 : line.find('(')] for line in caller]
callerSimple = [line.replace('<', '').replace('>', '') for line in callerSimple]
caller = [line[:line.find('(')] for line in caller]

nameMap = dict(zip(caller, callerSimple))


calleeSimple = [line[line.rfind(':')+1 : line.rfind('(')] for line in callee]
calleeSimple = [line.replace('<', '').replace('>', '') for line in calleeSimple]
callee = [line[:line.rfind('(')] for line in callee]

nameMap2 = dict(zip(callee, calleeSimple))
nameMap = dict(nameMap, **nameMap2)

methods = set(caller)
methods = methods.union(set(callee))


# Create the graph
g = nx.Graph()


for name in nameMap.keys():
    g.add_node(name)

for caller, callee in zip(caller, callee):
    g.add_edge(caller, callee)


# Calcualte eigenvector centrality and sort in descending order
evCentrality = nx.eigenvector_centrality(g, max_iter=1000)
evCentrality = {k: v for k, v in sorted(evCentrality.items(), key=lambda item: item[1], reverse=True)}
print(evCentrality)

# Draw the graph
pos = nx.nx_agraph.graphviz_layout(g)

nx.draw_networkx_nodes(g, pos, node_size=[evCentrality[node]*1000 for node in g.nodes], node_color='#8FBAC8')
nx.draw_networkx_edges(g, pos, node_size=0, width=1, edge_color='lightgrey')
nx.draw_networkx_labels(g, pos, labels=nameMap, font_size=10)

nx.drawing.nx_pylab.draw(g)
plt.show()
