## EV_Centrality.py
Calculates the eigenvector centrality of a function in the callgraph as a measure of the functions importance. The graph is then displayed with the size of the nodes representing its eigenvector centrality.

The callgraph.txt was generated using [java-callgraph.](https://github.com/gousiosg/java-callgraph)

[Blobsaver](https://github.com/airsquared/blobsaver) has been used as an example project to analyze.

## EV_Centrality_Distribution.py
Calculates the eigenvector centralities of functions in a [callgraph Dataset](https://github.com/quarkslab/dataset-call-graph-blogpost-material) and displays their distribution.

## FilterComments.py
Takes the callgraph and a JSON file containing method names and their Javadoc comments. Outputs a file containing a cleaned version of the comments of the methods with the highes eigenvector centrality.

JFreeChart_Callgraph.txt was generated using [java-callgraph.](https://github.com/gousiosg/java-callgraph)

JFreeChart_Comments.json contains a dictionary of fully qualified method names and their Javadoc comments. It was generated with the help of [javadoc-extractor.](https://github.com/ftomassetti/javadoc-extractor)
