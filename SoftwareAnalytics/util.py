from glob import glob
import os

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

def get_core_functions(n, centrality, callgraph, only_functions=False):
    core_functions = []
    i = 0

    blacklist = []
    blacklist.append('*')
    blacklist.append('---')
    blacklist.append('???')
    blacklist.append('^^^')

    while len(core_functions) < n and i < len(centrality):
        candidate = centrality[i][0]
        i += 1

        # Dont use functions that could not be resolved properly
        if any([symbol in candidate for symbol in blacklist]):
            continue

        if only_functions and not (candidate.startswith('<Node function') or candidate.startswith('<Node method')):
            continue

        # Only use functions that are part of the project
        for nodes in callgraph.defines_edges.values():
            if str(candidate) in str(nodes):
                core_functions.append(candidate)
                break

    return core_functions

def get_root_nodes(graph):
    return [node for node in graph if graph.in_degree(node) == 0]