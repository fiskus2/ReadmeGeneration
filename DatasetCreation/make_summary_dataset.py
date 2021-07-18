from make_inlining_dataset import classify_readmes, get_what_sections
import os
import datetime
from glob import glob
import json
import multiprocessing
from thread_with_trace import thread_with_trace
from SoftwareAnalytics.util import get_source_files, get_core_functions
from SoftwareAnalytics.pyan_callgraph import make_callgraph, make_networkx_graph, reverse_katz_centrality
from DatasetCreation.inlining import get_core_clusters, remove_nested_functions
from SoftwareAnalytics.get_source_code import get_source_code
import logging
import contextlib
import traceback
from lib2to3.main import main as to_py3
import sys
import re


dataset_part = 'train'
input_dir = './data/python-projects-med/' + dataset_part + '/'
output_dir = './data/summary-dataset/' + dataset_part + '/'
num_threads = 12
num_core_functions = 10

def main():
    print('Started', datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
    readme_classifier_input_dir = '../READMEClassifier/input/clf_target_readmes/'
    os.makedirs(output_dir, exist_ok=True)
    projects = os.listdir(input_dir)
    already_processed = glob(output_dir + '*')
    already_processed = [os.path.basename(path)[:-3] for path in already_processed]
    projects = [project for project in projects if project not in already_processed]

    #The 'what' secion of a readme, which describes the projects purpose
    classify_readmes(projects, input_dir, readme_classifier_input_dir)
    what_sections = get_what_sections(readme_classifier_input_dir, '../READMEClassifier/output/output_section_codes.csv')

    # Project descriptors are used as backup if no what section is found
    descriptors = {}
    for project_folder in projects:
        with open(input_dir + project_folder + '/descriptor', 'r', encoding="ISO-8859-1") as file:
            descriptors[project_folder] = file.read()

    num_no_what_section = 0
    i = 0
    while i <= len(projects) - 1:
        args = []
        for i in range(i, min(i + 100, len(projects))):  # project_folder in projects:
            project_folder = projects[i]
            id, author, project = project_folder.split(',')
            try:
                what_section = what_sections[author + '.' + project + '.md']
            except KeyError:
                what_section = descriptors[project_folder]

            if len(what_section) != 0:
                args.append((project_folder, what_section))
            else:
                num_no_what_section += 1

        i += 1

        pool = multiprocessing.Pool(num_threads)
        pool.map(process_project, args)

        print('Current progress:', str((100 * i) / len(projects)) + '%')

    print('Projects processed: ' + str(len(projects)))
    print('Projects with no what section and descriptor: ' + str(num_no_what_section))
    print('Finished', datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))


def process_project(args):
    project, what_section = args
    start = datetime.datetime.now()
    try:
        thread = thread_with_trace(target=_process_project, args=args)
        thread.start()
        thread.join(90)

        # If thread is active
        if thread.is_alive():
            thread.kill()
            print('Project ', project, ' took too long and was terminated')
        #_process_project(project, what_section)
    except Exception as err:
        #raise err
        print('Unhandeled error in project ' + project + ': ' + str(err))
    finally:
        end = datetime.datetime.now()
        print('--Processed ', project, ': ', str((end-start).seconds))


#Determines the most important functions of a project and inlines them into one function
#Converted: whether a conversion from python2 to python3 has been attempted
def _process_project(project, what_section, converted=False):
    filenames = get_source_files(input_dir + project)
    if len(filenames) == 0:
        print('Found no relevant files for project: ' + project)
        return
    try:
        callgraph = make_callgraph(filenames)
    except SyntaxError as err:
        print('Syntax error processing ' + project + '. Error: ' + str(err))
        if not converted:
            print('\tAttempting conversion to python 3')

            #Attempting to silence the to_py3() function, only works partially
            def dummy(*args):
                pass
            logger = logging.getLogger('RefactoringTool')
            logger.info = dummy
            logger.debug = dummy
            logger.error = dummy
            logger.critical = dummy
            logger.propagate = False
            logger.disabled = True

            print('2to3 output start')
            with open(os.devnull, 'w') as dev_null:
                with contextlib.redirect_stdout(dev_null):
                    with contextlib.redirect_stderr(dev_null):
                        to_py3("lib2to3.fixes", ['-x', 'filter', '-x', 'map', '-x', 'unicode', '-x', 'xrange', '-x', 'zip', '-n', '-w', input_dir + project])
            print('2to3 output end')
            _process_project(project, what_section, converted=True)
        return
    except KeyError as err:
        if 'for candidate_to_node in self.defines_edges[to_node]:' in traceback.format_exc():
            print('Mysterious Pyan import problem')
        else:
            raise err
        return
    except ValueError as err:
        print(str(err) + ' Project: ' + project)
        return
    except Exception as err:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print('Exception in pyan: ', exc_type, fname, exc_tb.tb_lineno)
        return

    if converted:
        print('\tConversion Successful')

    graph = make_networkx_graph(callgraph)
    centrality = reverse_katz_centrality(graph)

    #Gets 150% of needed core functions, in case the sourcecode of some functions cannot be found
    core_functions = get_core_functions(round(num_core_functions*1.5), centrality, callgraph)

    i = 0
    while i != min(num_core_functions, len(core_functions)):
        code = get_source_code(callgraph.module_to_filename, core_functions[i])
        if len(code) == 0:
            continue

        unnecessary_indentation = re.search(r'^(\s*)', code[0]).group(1)
        code = [line[len(unnecessary_indentation):] for line in code]
        code = remove_nested_functions(code)

        dir = os.path.join(output_dir, project)
        if not os.path.exists(dir):
            os.mkdir(dir)
        with open(os.path.join(dir, str(i) + '.py'), 'w', encoding="ISO-8859-1") as file:
            file.write('\n'.join(code))

        i += 1

    with open(os.path.join(dir, 'readme.md'), 'w', encoding="ISO-8859-1") as file:
        file.write(what_section)


if __name__ == "__main__":
    main()