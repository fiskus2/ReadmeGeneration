import pickle
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

#Dataset: https://github.com/quarkslab/dataset-call-graph-blogpost-material
list_of_goodware_graph=pickle.load(open("goodware_graphs.p", "rb"))
list_of_malware_graph=pickle.load(open("malware_graphs.p", "rb"))
evCentralities = []

for project in list_of_goodware_graph + list_of_malware_graph:
    functions = project[1].keys()

    # Create the graph
    g = nx.Graph()


    for name in functions:
        g.add_node(name)

    for function in functions:
        for callee in project[1][function]:
            g.add_edge(function, callee)


    # Calcualte eigenvector centrality
    evCentrality = nx.eigenvector_centrality(g, max_iter=10000)
    evCentralities = evCentralities + list(evCentrality.values())
    print(evCentrality)


#Display distribution
sns.set_style('whitegrid')
sns.kdeplot(np.array(evCentralities), bw=0.02)
plt.show()