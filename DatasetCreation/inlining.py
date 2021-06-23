
from SoftwareAnalytics.util import get_root_nodes
import networkx as nx
from networkx.algorithms.approximation.steinertree import steiner_tree
import re

#Determines how the functions shall be inlined.
#Returns a directed graph where each node is a function and each edge an inlining that shall be performed
def determine_inlining_order(clusters, graph):
    inlinings = []
    for cluster in clusters:
        if len(cluster) == 1:
            inlinings.append(graph.subgraph(cluster))
            continue

        # The steiner tree is an minimum tree spanning a specified set of nodes in a graph. It will be used to define
        # the inlining order. The steiner_tree algorithm is only implemented for connected, undirected graphs.
        # The graph is transformed accordingly. It is not possible to make a subgraph containing only the nodes of a
        # cluster, because they may be connected by an intermediate, unimportant node.
        # Only one intermediate node is allowed when inlining two core functions. All non-core nodes, that dont call
        # a core node are removed to prevent dead ends in the inlining graph, when the directions are restored.
        reduced_graph = graph.copy()
        for node in list(graph.nodes()):
            if node not in cluster and not any([callee in cluster for callee in graph.successors(node)]):
                reduced_graph.remove_node(node)

        inlining = steiner_tree(reduced_graph.to_undirected(), cluster)
        inlinings.append(inlining)

    # After the steiner tree has been created, the direction information can now be restored from the original graph
    directed_inlinings = []
    for inlining in inlinings:
        directed_inlining = nx.DiGraph()
        if len(inlining) > 1:
            for from_node in inlining:
                for to_node in graph.successors(from_node):
                    if to_node in inlining and inlining.has_edge(from_node, to_node):
                        directed_inlining.add_edge(from_node, to_node)
        else:
            directed_inlining.add_node(list(inlining.nodes())[0])

        # To allow inlining, each cluster must have exactly one root. Additional roots will be moved to a new cluster.
        roots = get_root_nodes(directed_inlining)
        if len(roots) > 1:
            for root in roots[1:]:
                directed_inlining.remove_node(root)
                clusters.append([root])

        root = roots[0]

        # While the undirected graph was a tree, restoring the direction information may cause a cycle when two
        # functions call each other, which leads to an infinite loop when inlining. The edge leading towards the
        # root is deleted, so all nodes remain reachable from the root
        try:
            cycles = nx.simple_cycles(directed_inlining)
            for cycle in cycles:
                # cycles cannot be longer than 2, otherwise the undirected graph would not be a tree. That is unless
                # two cycles are adjacent to each other, which is not recogniced by nx.simple_cycles
                assert len(cycle) == 2
                nodeA = cycle[0][0]
                nodeB = cycle[0][1]

                path = nx.shortest_path(directed_inlining, root, nodeB)
                if nodeA in [path]:
                    directed_inlining.remove_edge(nodeB, nodeA)
                else:
                    directed_inlining.remove_edge(nodeA, nodeB)

        except nx.NetworkXNoCycle:
            pass

        directed_inlinings.append(directed_inlining)


    return directed_inlinings


#Creates a set of cluster of nodes in the callgraph that are close enough to each other to be inlined.
#Close enough means that two core functions are connected by at most one intermediate, unimportant function
def get_core_clusters(core_functions, graph):
    path_lists = []
    for from_node in core_functions:
        path_list = []
        for to_node in core_functions:
            try:
                path = nx.shortest_path(graph, from_node, to_node) if from_node != to_node else []
            except nx.NetworkXNoPath:
                path = []
            path_list.append(path)
        path_list[core_functions.index(from_node)] = [from_node]
        path_lists.append(path_list)

    clusters = []

    for path_list in path_lists:
        #The paths include start and end node, so length 3 means one intermediate node
        members = [path[-1] for path in path_list if len(path) > 0 and len(path) <= 3]
        cluster_found = False
        for cluster in clusters:
            if any([member in cluster for member in members]):
                cluster.update(members)
                cluster_found = True

        if not cluster_found:
            clusters.append(set(members))

    return clusters

#Recursively inlines functioncalls (or scripts) as defined by the given graph
#graph: A directed graph. Nodes are functions. Edges define the inlining to be performed.
#node: The node from which to start recursively inlining.
#code: A dictionary. Keys are nodes in the graph. Values are the corresponding code as string.
def inline_neighbors(graph, node, code):
    neighbors = list(graph.successors(node))
    insertion_locations = {}

    for neighbor in neighbors:

        # Find the location of the function call
        # For classes the 'function call' is the import statement
        if neighbor.startswith('<Node class:'):
            class_name = neighbor.split('.')[-1][:-1]
            for i in range(len(code[node])):
                if re.match('(import.*?' + class_name + ')|(from ' + class_name + ' import)', code[node][i]) is not None:
                    insertion_locations[neighbor] = i
                    break

            if neighbor not in insertion_locations:
                # In the callgraph, the code in a class (not method) is attributed to the function using a method of the class.
                # The code is executed when the class is imported, usually before the function. Thus, the code is inlined
                # at the beginning of the function.
                insertion_locations[neighbor] = 1

        # Constructors
        elif neighbor.split('.')[-1][:-1] == '__init__':
            class_name = neighbor.split('.')[-2]
            for i in range(len(code[node])):
                if class_name + '(' in code[node][i]:
                    insertion_locations[neighbor] = i
                    break

        else: # Function and method calls
            neighbor_function_name = neighbor.split('.')[-1][:-1]
            for i in range(len(code[node])):
                line = code[node][i]
                call_index = line.index(neighbor_function_name + '(') if neighbor_function_name + '(' in line else -1
                if call_index != -1:
                    insertion_locations[neighbor] = i
                    break

    inlined = code[node]

    # Adjust indentation to match the target code
    for neighbor in neighbors:
        neighbor_code = inline_neighbors(graph, neighbor, code)
        if 'def ' in neighbor_code[0] or 'class ' in neighbor_code[0]:
            neighbor_code = neighbor_code[1:] #Remove 'def...' and 'class...'


        insertion_line = inlined[insertion_locations[neighbor]]


        target_indentation = re.match(r'^(\s*)', insertion_line).group(0)
        lowest_neighbor_indentation = get_lowest_indentation(neighbor_code)

        # Replace indentation of code to be inlined with indentation of target code
        for i in range(len(neighbor_code)):
            neighbor_code[i] = neighbor_code[i][len(lowest_neighbor_indentation):]
            neighbor_code[i] = target_indentation + neighbor_code[i]

        # Return statements must be removed for inlining
        # The returned value will be inserted at the place of the function call
        last_return_expr = ''
        return_found = False
        for i in range(len(neighbor_code) - 1, -1, -1):
            return_expr = re.match(r'^\s*return\s+(.+)', neighbor_code[i])
            if return_expr:
                if not return_found:
                    last_return_expr = return_expr.group(1)
                    return_found = True

            # remove all return statements
            elif 'return' in remove_strings([neighbor_code[i]])[0]:
                neighbor_code[i] = neighbor_code[i][:neighbor_code[i].find('return')] + 'pass'


        insertion_location = insertion_locations[neighbor]
        inlined[insertion_location:insertion_location] = neighbor_code
        for function in insertion_locations:
            if insertion_locations[function] >= insertion_location and not node.startswith('<Node class:'):
                insertion_locations[function] += len(neighbor_code)

        callee_name = neighbor.split('.')[-1][:-1]
        if not neighbor.startswith('<Node class:') and callee_name != '__init__':
            calling_line_index = insertion_locations[neighbor]
            calling_line = inlined[calling_line_index]

            # The regex will match the function call only up to the opening parenthesis. The regex cant determine
            # the end of the call because it cant count the opening and closing parentheses
            callee_name = neighbor.split('.')[-1][:-1]

            call_regex_direct = r'[^\w]({}\()'.format(callee_name) #e.g.: myfun()
            call_regex_dot = r'([^\s]+\.{}\()'.format(callee_name) #e.g.: someobject.myfun()
            call_regex = re.compile(call_regex_dot)
            call = call_regex.search(calling_line)

            if call is None:
                call_regex = re.compile(call_regex_direct)
                call = call_regex.search(calling_line)
            call = call.group(1)

            call_start_index = calling_line.find(call)
            call_end_index = call_start_index + len(call)
            parenthesis_level = 0
            while parenthesis_level >= 0:
                if calling_line[call_end_index] == '(':
                    parenthesis_level += 1
                elif calling_line[call_end_index] == ')':
                    parenthesis_level -= 1
                call_end_index += 1

            #replace function call with returned expression
            calling_line = calling_line[:call_start_index] + last_return_expr + calling_line[call_end_index:]
            inlined[calling_line_index] = calling_line

    return inlined


# Argument lists that extend over several lines will be moved to the function name,
# so that the whole function call is in one line
# code: a list of lines of source code
def remove_multiline_function_calls(code):
    if len(code) == 0:
        return code
    try:
        for i in range(len(code)):
            line = remove_strings([code[i]])[0]
            brace_level = line.count('(') - line.count(')')
            assert brace_level >= 0
            #if re.search(r'[^\s]\(', line) is not None and line.strip()[-1] != ')' and line.strip()[-1] != ':':
            if brace_level != 0:
                while brace_level != 0:
                    code[i] += code[i+1]
                    del code[i+1]
                    line = remove_strings([code[i]])[0]
                    brace_level = line.count('(') - line.count(')')

    except IndexError:
        #The length changes due to the deletion, so the range goes out of bounds
        pass

    return code

#Removes strings without replacement
#text: a list of lines of code
def remove_strings(text):
    keep = True
    quotetype = ''
    new_text = []
    for i in range(len(text)):
        new_line = ''
        for j in range(len(text[i])):
            if keep:
                if (text[i][j] == '"' or text[i][j] == "'") and (j == 0 or text[i][j] != '\\'):
                    quotetype = text[i][j]
                    keep = False
                new_line += text[i][j]
            else:
                if text[i][j] == quotetype and (j == 0 or text[i][j] != '\\'):
                    keep = True
        new_text.append(new_line)

    return new_text


#Replaces nested functions with empty lines. Code must be one function as list of lines, not the code of an entire file
def remove_nested_functions(code):
    if len(code) == 0:
        return code

    keep = True
    function_indentation = ''
    for i in range(1, len(code)):
        if keep:
            search = re.search(r'(\s+)def ', code[i])
            if search is not None:
                keep = False
                function_indentation = search.group(1)

        elif code[i] != '' and not code[i].isspace():
            #nested function ends, when line does not start with function_indentation or does start with function_indentation
            #but does not contain any further indentation for the nested function
            keep = (not code[i].startswith(function_indentation)) or not code[i][len(function_indentation)].isspace()


        if not keep:
            code[i] = ''

    return code

#Returns the shortest indentation.
#code: a list of lines of code
def get_lowest_indentation(code):
    lowest_indentation = None
    for line in code:
        if line == '':
            continue
        if re.match(r'^\s+$', line) is not None:
            continue

        indentation = re.search(r'^(\s*)', line).group(1)
        if lowest_indentation == None or len(indentation) < len(lowest_indentation):
            lowest_indentation = indentation

    return lowest_indentation if lowest_indentation != None else ''