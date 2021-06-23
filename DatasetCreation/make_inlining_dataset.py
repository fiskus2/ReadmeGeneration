import os
from SoftwareAnalytics.util import get_source_files, get_core_functions, get_root_nodes
from SoftwareAnalytics.pyan_callgraph import make_callgraph, make_networkx_graph, reverse_katz_centrality
from DatasetCreation.inlining import get_core_clusters, determine_inlining_order, inline_neighbors, \
    remove_multiline_function_calls, get_lowest_indentation, remove_nested_functions
from SoftwareAnalytics.get_source_code import get_source_code
from shutil import copyfile
import sys
import re
import csv
from markdown import markdown
from bs4 import BeautifulSoup
import nltk
from itertools import chain

input_dir = './data/python-projects-med/tmp/'
output_dir = './data/python-projects-med/inlining/'
num_core_functions = 10
num_what_section_sentences = 2

#Creates a code2seq dataset
#There is one function per project, which is an inlining of the most important functions in the project
#The function names are the 'what' sections of the corresponding project, which describes the purpose of the project
def main():
    readme_classifier_input_dir = '../READMEClassifier/input/clf_target_readmes/'
    projects = os.listdir(input_dir)

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

    projects = [project for project in projects]
    for project_folder in projects:
        id, author, project = project_folder.split(',')
        try:
            what_section = what_sections[author + '.' + project + '.md']
        except KeyError:
            continue
        if len(what_section) != 0:
            process_project(project_folder, what_section)


#Determines the most important functions of a project and inlines them into one function
def process_project(project, what_section):
    filenames = get_source_files(input_dir + project)
    callgraph = make_callgraph(filenames)
    graph = make_networkx_graph(callgraph)
    centrality = reverse_katz_centrality(graph)
    core_functions = get_core_functions(num_core_functions, centrality, callgraph)
    clusters = get_core_clusters(core_functions, graph)
    inlinings = determine_inlining_order(clusters, graph)

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
            if malformed:
                print('Malformed readme: ' + current_readme)
            elif readme_categorization is not None:
                readme_categorizations.append(readme_categorization)

            current_readme = filename
            readme_categorization = []
            malformed = False

        malformed = malformed or not re.search('[a-zA-Z]', heading)
        readme_categorization.append(fields)

    readme_categorizations.append(readme_categorization)

    #Find the 'what' section in the readme file and extract it
    for readme_categorization in readme_categorizations:
        readme_out = []
        keep = '1' in readme_categorization[0][4] #1 -> 'what' section
        current_readme = readme_categorization[0][2]

        with open(os.path.join(readme_path, current_readme), encoding="utf8") as file:
            readme_raw = file.readlines()

        end = 0
        for fields in readme_categorization[1:]:

            start = end
            try:
                end = readme_raw.index(fields[3] + '\n')
            except ValueError:
                searchStr = fields[3][fields[3].find(' ') + 1:] + '\n'
                end = readme_raw.index(searchStr)
                next_line_start = readme_raw[end + 1][:2]
                assert next_line_start == '--' or next_line_start == '=='

            if keep:
                readme_out = readme_out + readme_raw[start:end]

            keep = '1' in fields[4]

        #Markdown to plain text
        readme_out = ''.join(readme_out)
        html = markdown(readme_out)
        text = ''.join(BeautifulSoup(html).findAll(text=True))
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