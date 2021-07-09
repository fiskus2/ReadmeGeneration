import os
from SoftwareAnalytics.util import get_source_files, get_core_functions, get_root_nodes
from SoftwareAnalytics.pyan_callgraph import make_callgraph, make_networkx_graph, reverse_katz_centrality
from DatasetCreation.inlining import get_core_clusters, determine_inlining_order, inline_neighbors, \
    get_lowest_indentation, remove_nested_functions
from SoftwareAnalytics.get_source_code import get_source_code, remove_multiline_function_calls
from shutil import copyfile
import sys
import re
import csv
from markdown import markdown
from bs4 import BeautifulSoup
import nltk
from itertools import chain
import traceback
from lib2to3.main import main as to_py3
from threading import Thread
import contextlib
import logging
import subprocess
from joblib import Parallel, delayed
import datetime
import multiprocessing
from joblib.externals.loky.backend.context import get_context
import time
from thread_with_trace import thread_with_trace
from glob import glob

input_dir = './data/python-projects-large/train/'
output_dir = './data/python-projects-large/inlining/train/'
num_threads = 32
num_core_functions = 10
num_what_section_sentences = 2

#Creates a code2seq dataset
#There is one function per project, which is an inlining of the most important functions in the project
#The function names are the 'what' sections of the corresponding project, which describes the purpose of the project
def main():
    print('Started', datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
    readme_classifier_input_dir = '../READMEClassifier/input/clf_target_readmes/'
    os.makedirs(output_dir, exist_ok=True)
    projects = os.listdir(input_dir)
    already_processed = glob(output_dir + '*')
    already_processed = [os.path.basename(path)[:-3] for path in already_processed]
    projects = [project for project in projects if project not in already_processed]

    #Delete old files in readme classifier input dir
    old_files = os.listdir(readme_classifier_input_dir)
    for file in old_files:
        os.remove(os.path.join(readme_classifier_input_dir, file))

    #Find readme files and copy them to readme classifier input dir
    project_to_readme = {}
    for project_folder in projects:

        id, author, project = project_folder.split(',')
        readme_file = ''
        for root, dirs, files in os.walk(input_dir + project_folder):
            for file in files:
                if file.lower() == 'readme' or file.lower() == 'readme.md':
                    readme_file = os.path.join(root, file)
                    break
            if readme_file != '':
                break

        if readme_file == '':
            continue

        project_to_readme[project_folder] = readme_file
        copyfile(readme_file, readme_classifier_input_dir + author + '.' + project + '.md')

    #Execute readme classifier
    dir = os.getcwd()
    os.chdir('../READMEClassifier/script/')
    sys.path.append(os.getcwd())
    exec(open("empty_all_tables.py").read(), globals())
    exec(open("load_target_sections.py").read(), globals())
    exec(open("classifier_classify_target.py").read(), globals())
    os.chdir(dir)

    #The 'what' secion of a readme, which describes the projects purpose
    what_sections = get_what_sections(readme_classifier_input_dir, '../READMEClassifier/output/output_section_codes.csv')

    #Project descriptors are used as backup if no what section is found
    descriptors = {}
    for project_folder in projects:
        with open(input_dir + project_folder + '/descriptor', 'r', encoding="ISO-8859-1") as file:
            descriptors[project_folder] = file.read()

    #for project_folder in projects:
    #    id, author, project = project_folder.split(',')
    #    print(project + '\t' + get_first_sentences_as_function_name(what_sections.get(author + '.' + project + '.md', ''), num_what_section_sentences).replace('\n', ' ') + '\t' + descriptors[project_folder].replace('\n', ' '))

    num_no_what_section = 0
    i = 0
    while i <= len(projects) - 1:
        args = []
        for i in range(i, min(i + 100, len(projects))): #project_folder in projects:
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

        p = multiprocessing.Pool(num_threads)
        p.map(process_project, args)

        print('Current progress:', str((100*i)/len(projects)) + '%')

    print('Projects processed: ' + str(len(projects)))
    print('Projects with no what section and descriptor: ' + str(num_no_what_section))
    print('Finished', datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))

def process_project(args):
    project, what_section = args
    start = datetime.datetime.now()
    try:
        p = thread_with_trace(target=_process_project, args=args)
        p.start()
        p.join(90)

        # If thread is active
        if p.is_alive():
            p.kill()
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
    core_functions = get_core_functions(num_core_functions, centrality, callgraph)
    clusters = get_core_clusters(core_functions, graph)
    inlinings = determine_inlining_order(clusters, graph)

    if len(core_functions) == 0 and len(centrality) > 0:
        print('Could not identify relevant functions for project: ' + project)
        return

    inlined_code = []
    for inlining in inlinings:
        root = get_root_nodes(inlining)[0]

        code = {node: get_source_code(callgraph.module_to_filename, node) for node in inlining}
        #code = {node: remove_multiline_function_calls(lines) for node, lines in code.items()}
        inlined_code.append(inline_neighbors(inlining, root, code))

    inlined_code = [remove_nested_functions(function) for function in inlined_code]

    #remove 'def' lines of all functions but the first
    for i in range(1, len(inlined_code)):
        inlined_code[i] = inlined_code[i][1:]

    unnecessary_indentation = re.search(r'^(\s*)', inlined_code[0][0]).group(1)
    inlined_code[0] = [line[len(unnecessary_indentation):] for line in inlined_code[0]]

    target_indentation = get_lowest_indentation(inlined_code[0][1:])
    for i in range(1, len(inlined_code)):
        lowest_indentation = get_lowest_indentation(inlined_code[i])
        if lowest_indentation != target_indentation:
            inlined_code[i] = [target_indentation + function[len(lowest_indentation):] for function in inlined_code[i]]

    target_sequence = get_first_sentences_as_function_name(what_section, num_what_section_sentences)
    inlined_code = list(chain(*inlined_code))
    inlined_code[0] = re.sub(r'def .+\(', 'def ' + target_sequence + '(', inlined_code[0])
    inlined_code = '\n'.join(inlined_code)

    with open(output_dir + project + '.py', 'w', encoding="utf-8") as file:
        file.write(inlined_code)


#Process the results of the readme classifier and extract the plain text 'what' section of the readmes
def get_what_sections(readme_path, classification_path):
    what_dict = {}

    with open(classification_path, encoding="utf8") as file:
        reader = csv.reader(file)
        sections = list(reader)

    sections = sections[1:] #ignore headlines

    readme_categorizations = []
    readme_categorization = None
    current_readme = ''
    malformed = False

    #filter malformed and make a list of sections for each project
    for fields in sections:
        filename = fields[2]
        heading = fields[3]

        if current_readme != filename:
            if readme_categorization is not None and len(readme_categorization) > 0:
                readme_categorizations.append(readme_categorization)

            current_readme = filename
            readme_categorization = []

        if re.search('[a-zA-Z]', heading):
            readme_categorization.append(fields)

    readme_categorizations.append(readme_categorization)

    #Find the 'what' section in the readme file and extract it
    for readme_categorization in readme_categorizations:
        readme_out = []
        keep = '1' in readme_categorization[0][4] #1 -> 'what' section
        current_readme = readme_categorization[0][2]

        try:
            with open(os.path.join(readme_path, current_readme), encoding="utf8") as file:
                readme_raw = file.readlines()
        except:
            try:
                with open(os.path.join(readme_path, current_readme), encoding="ISO-8859-1") as file:
                    readme_raw = file.readlines()
            except:
                continue

        end = 0
        for fields in readme_categorization[1:]:
            if re.search('[A-Za-z]', fields[3]) == None:
                #Empty headline, perhaps '---' was used to draw a line in markdown
                continue
            if '@abstr_code_section' in fields[3]:
                #Keyword for code sections
                continue

            start = end
            try:
                end = readme_raw.index(fields[3] + '\n')
            except ValueError:
                searchStr = fields[3][fields[3].find(' ') + 1:] + '\n'
                try:
                    end = readme_raw.index(searchStr)
                    next_line_start = readme_raw[end + 1][:2]
                    assert next_line_start == '--' or next_line_start == '=='
                except:
                    end = start + 1

            if keep:
                readme_out = readme_out + readme_raw[start:end]

            keep = '1' in fields[4]

        #Markdown to plain text
        readme_out = ''.join(readme_out)
        html = markdown(readme_out)
        text = ''.join(BeautifulSoup(html, features="lxml").findAll(text=True))
        text = [line for line in text.split('\n') if len(line) == 0 or line[0] != '|']
        text = text[1:]
        text = '\n'.join(text)
        while '\n\n' in text:
            index = text.find('\n\n')
            text = text[:index] + text[index + 1:]
        what_dict[current_readme] = text

    return what_dict


#Returns the first n sentences of a text as function name, i.e. without special character and delimited by _
def get_first_sentences_as_function_name(text, n):
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    sentences = tokenizer.tokenize(text)
    sentences = sentences[:n] if n < len(sentences) else sentences
    words = []
    for sentence in sentences:
        words += nltk.word_tokenize(sentence)

    #remove all special characters
    words = [''.join(e for e in word if e.isalnum()) for word in words]
    words = [word for word in words if word != '']

    return '_'.join(words)


if __name__ == "__main__":
    main()