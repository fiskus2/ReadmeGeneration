import networkx as nx
import matplotlib.pyplot as plt
import re
import json

with open('JFreeChart_Callgraph.txt') as file:
    input = file.readlines()

# Remove everything that is not a function call made by the project
inputs = [line for line in input if line.startswith('M:')]

# Remove if the called function is not a function of the project
inputs = [line for line in inputs if ')org.jfree' in line]

# Remove lambda expressions
inputs = [line for line in inputs if 'lambda$' not in line]

# Split caller and callee
split = [line.split(' ') for line in inputs]
caller = [elem[0] for elem in split]
callee = [elem[1] for elem in split]

caller = [line.replace('<', '').replace('>', '') for line in caller]
callee = [line.replace('<', '').replace('>', '') for line in callee]

# Functions with the same name but from a different class shall be separate nodes in the network.
# The Graph library shall therefore identify the methods by their fully qualified name, while displaying a simple name
# For this purpose the nameMap shall map fully qualified names to simple names
callerSimple = [line[line.rfind(':')+1 : line.find('(')] for line in caller]
caller = [line[:line.find('(')] for line in caller]
caller = [line[2:].replace(':', '.') for line in caller]

nameMap = dict(zip(caller, callerSimple))


calleeSimple = [line[line.rfind(':')+1 : line.rfind('(')] for line in callee]
callee = [line[:line.rfind('(')] for line in callee]
callee = [line[3:].replace(':', '.') for line in callee]

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
evCentralities = nx.eigenvector_centrality(g, max_iter=1000)
evCentralities = {k: v for k, v in sorted(evCentralities.items(), key=lambda item: item[1], reverse=True)}
print(evCentralities)

# Draw the graph
#pos = nx.nx_agraph.graphviz_layout(g)

#nx.draw_networkx_nodes(g, pos, node_size=[evCentralities[node]*1000 for node in g.nodes], node_color='#8FBAC8')
#nx.draw_networkx_edges(g, pos, node_size=0, width=1, edge_color='lightgrey')
#nx.draw_networkx_labels(g, pos, labels=nameMap, font_size=10)

#nx.drawing.nx_pylab.draw(g)
#plt.show()


with open('JFreeChart_Comments.json') as file:
    comments = file.read()

comments = json.loads(comments)
commentString = ""
for name in list(evCentralities.keys())[0:30]:
    if name in comments.keys():
        comment = comments[name]
        comment = comment[:comment.index('@param')]
        comment = comment.replace('{', '')
        comment = comment.replace('}', '')
        comment = re.sub('@\S*', '', comment)
        comment = comment.replace('\t', ' ')
        comment = comment.replace('/**', '')
        comment = comment.replace('*/', '')
        comment = comment.replace(' *', '')
        comment = re.sub(' +', ' ', comment)
        comment = comment.replace('\n\n', '\n')
        comment = comment.replace('\n \n', '\n')
        commentString = commentString + comment


with open('JFreeChart_JavadocsCleaned.txt', 'w') as out:
        out.write(commentString)
