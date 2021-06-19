# Calculates different centralities on different callgraphs and saves the result for comparison
from centrality_metrics import *
from pyan_callgraph import make_callgraph, make_networkx_graph, make_module_graph, get_source_files, get_module_of_function
from pathlib import Path
from git import Repo

def main():
    projects = []
    projects.append(('./pyan', None))
    projects.append(('TestProjects/betterbib', 'https://github.com/nschloe/betterbib.git'))
    projects.append(('TestProjects/tootbot', 'https://github.com/corbindavenport/tootbot.git'))
    projects.append(('TestProjects/MORAN_v2', 'https://github.com/Canjie-Luo/MORAN_v2.git'))
    projects.append(('TestProjects/grad-cam-pytorch', 'https://github.com/jacobgil/pytorch-grad-cam.git'))

    metrics = []
    metrics.append(eigenvector_centrality)
    metrics.append(eigenvector_centrality_weighted)
    metrics.append(eigenvector_centrality_weighted_edges)
    metrics.append(pagerank)
    metrics.append(inverse_pagerank)
    metrics.append(degeneracy)
    metrics.append(katz_centrality)
    metrics.append(reverse_katz_centrality)
    metrics.append(harmonic_centrality)
    metrics.append(inverse_harmonic_centrality)
    metrics.append(closeness_centrality)
    metrics.append(reverse_closeness_centrality)
    metrics.append(degree_centrality)
    metrics.append(out_degree_centrality)
    metrics.append(second_order_centrality)
    metrics.append(inverse_second_order_centrality)
    metrics.append(local_reaching_centrality)
    metrics.append(ensemble_revKatz_revCloseness_outDeg_localReaching)


    Path("Centralities").mkdir(exist_ok=True)

    for project_dir, github_link in projects:
        project_name = project_dir[project_dir.rfind('/') + 1:]

        if not Path(project_dir).exists():
            print('Downloading ' + project_name)
            Repo.clone_from(github_link, project_dir)


        filenames = get_source_files(project_dir)
        callgraph = make_callgraph(filenames)
        graph = make_networkx_graph(callgraph)
        graph_backup = make_networkx_graph(callgraph) # A copy of the graph to verify that no metric has changed it
        module_graph = make_module_graph(filenames)


        centralities = {}
        module_centralities = {}
        for metric in metrics:
            centrality = metric(graph)

            # Sort in descending order
            centrality = [(str(k), str(v)) for k, v in sorted(centrality.items(), key=lambda item: item[1], reverse=True)]
            centralities[metric.__name__] = centrality

            module_centralities[metric.__name__] = metric(module_graph)



        centralities_module_weighted = {}
        function_to_module = {}
        for metric_name, centrality, module_centrality in zip(centralities.keys(), centralities.values(), module_centralities.values()):
            average_module_centrality = sum(module_centrality.values()) / len(module_centrality)
            centrality_module_weighted = {}
            for function_name, rating in centrality:
                module = get_module_of_function(function_name, module_graph)
                module_score = module_centrality[module] if module in module_centrality else average_module_centrality
                rating = float(rating) * module_score

                function_to_module[function_name] = str(module) + ': ' + str(module_score)
                centrality_module_weighted[function_name] = rating

            centrality_module_weighted = [(str(k), str(v)) for k, v in sorted(centrality_module_weighted.items(), key=lambda item: item[1], reverse=True)]
            centralities_module_weighted[metric_name] = centrality_module_weighted



        csv = ',,,'.join(list(centralities.keys())) + '\n'


        for ratings in zip(*(centralities.values())):
            csv += ',,'.join([','.join(rating) for rating in ratings])
            csv += '\n'

        csv += '\n'
        csv += '\n'

        for ratings in zip(*(centralities_module_weighted.values())):
            for function_name, rating in ratings:
                csv += function_name + ',' + rating + ',' + function_to_module[function_name] + ','
            csv += '\n'



        with open('./Centralities/' + project_name + '.csv', 'w+') as file:
            file.write(csv)

        assert graph.__eq__(graph_backup)



if __name__ == "__main__":
    main()