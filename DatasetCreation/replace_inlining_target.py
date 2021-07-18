#Takes an inlining dataset and the original code to create a new inlining dataset with a new target string
#This saves time in comparison to creating a new dataset, because callgraph generation and inlining need not be executed

import os
import datetime
from glob import glob
import multiprocessing
from make_inlining_dataset import classify_readmes, get_what_sections
import re
from make_inlining_dataset import get_first_sentences_as_function_name


code_input_dir = './data/python-projects-med/test/'
inlining_input_dir = './data/python-projects-med/inlining/test/'
output_dir = './data/python-projects-med/inlining-long-targets/test/'
num_threads = 1
num_core_functions = 10
num_what_section_sentences = 10

def main():
    print('Started', datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
    readme_classifier_input_dir = '../READMEClassifier/input/clf_target_readmes/'
    os.makedirs(output_dir, exist_ok=True)
    inlined_projects = os.listdir(inlining_input_dir)
    inlined_projects = [project[:-3] for project in inlined_projects] # remove '.py'
    already_processed = glob(output_dir + '*')
    already_processed = [os.path.basename(path)[:-3] for path in already_processed]
    inlined_projects = [project for project in inlined_projects if project not in already_processed]


    # The 'what' secion of a readme, which describes the projects purpose
    # Processes the original readmes of projects for which an inlined code file exists
    classify_readmes(inlined_projects, code_input_dir, readme_classifier_input_dir)
    what_sections = get_what_sections(readme_classifier_input_dir, '../READMEClassifier/output/output_section_codes.csv')

    # Project descriptors are used as backup if no what section is found
    #descriptors = {}
    #for project_folder in projects:
    #    with open(inlining_input_dir + project_folder + '/descriptor', 'r', encoding="ISO-8859-1") as file:
    #        descriptors[project_folder] = file.read()


    num_no_what_section = 0
    i = 0
    while i <= len(inlined_projects) - 1:
        args = []
        for i in range(i, min(i + 100, len(inlined_projects))):  # project_folder in projects:
            project_folder = inlined_projects[i]
            id, author, project = project_folder.split(',')
            try:
                what_section = what_sections[author + '.' + project + '.md']
                args.append([project_folder, what_section])
            except KeyError:
            #    what_section = descriptors[project_folder]

            #if len(what_section) != 0:
            #    args.append((project_folder, what_section))
            #else:
                num_no_what_section += 1

        i += 1

        pool = multiprocessing.Pool(num_threads)
        pool.map(process_project, args)

        print('Current progress:', str((100 * i) / len(inlined_projects)) + '%')

    print('Projects processed: ' + str(len(inlined_projects)))
    print('Projects with no what section and descriptor: ' + str(num_no_what_section))
    print('Finished', datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))

def process_project(args):
    project, what_section = args
    target_sequence = get_first_sentences_as_function_name(what_section, num_what_section_sentences)
    with open(inlining_input_dir + project + '.py', 'r', encoding="utf-8") as file:
        code = file.readlines()

    code[0] = re.sub(r'def .+\(', 'def ' + target_sequence + '(', code[0])
    with open(output_dir + project + '.py', 'w', encoding="utf-8") as file:
        file.writelines(code)

if __name__ == "__main__":
    main()