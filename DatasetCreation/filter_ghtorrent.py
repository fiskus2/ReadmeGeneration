#Filters the ghtorrent dataset to remove repositories that are not of interest.
#Requires a projects.csv and watchers.csv file as downloaded from ghtorrent.

import csv
from datetime import datetime
from pathlib import Path
from langdetect import detect, LangDetectException
import itertools
import multiprocessing
import os

output_file = './data/python-projects-med/filtered.csv'

def log(forked_or_deleted, malformed_lines, java_projects, python_projects, not_enough_stars, not_english):
    now = datetime.now()
    log_string = now.strftime("%d.%m.%Y %H:%M:%S") + '\n'
    log_string = log_string + 'Forked or deleted: ' + str(forked_or_deleted) + '\n'
    log_string = log_string + 'Malformed lines: ' + str(malformed_lines) + '\n'
    log_string = log_string + 'Not english: ' + str(not_english) + '\n'
    log_string = log_string + 'Not enough stars: ' + str(not_enough_stars) + '\n'
    log_string = log_string + 'Java Projects: ' + str(java_projects) + '\n'
    log_string = log_string + 'Python Projects: ' + str(python_projects) + '\n\n'
    with open('./log.txt', 'a+') as logfile:
        logfile.write(log_string)

def main():
    projects_file_path = r'.\data\mysql-2019-06-01\projects.csv'
    watchers_file_path = r'.\data\mysql-2019-06-01\watchers.csv'
    min_stars = 400
    Path(os.path.dirname(output_file)).mkdir(parents=True, exist_ok=True)

    #The files are several GB large and are read incrementally
    with open(projects_file_path, encoding="ISO-8859-1") as projects_file:
        with open(watchers_file_path, encoding="ISO-8859-1") as watchers_file:
            projects_reader = csv.reader(projects_file, delimiter=',', quotechar='"')
            watchers_reader = csv.reader(watchers_file, delimiter=',', quotechar='"')
            project_index = 0
            project_lines = []
            watchers = {}
            watcher_parts = watchers_reader.__next__()
            results = []
            finished = False

            #process 1 mio projects per iteration
            while not finished:
                try:
                    for index in range(project_index, project_index + 1000000):
                        project_lines.append(projects_reader.__next__())
                except StopIteration:
                    finished = True
                project_index += 1000000

                last_id = int(project_lines[-1][0])

                #process the appropriate amount of watchers
                # The watchers.csv file contains one line per watcher. The line starts with the repo id being watched.
                while True:
                    try:
                        watchers[int(watcher_parts[0])] += 1
                    except KeyError:
                        watchers[int(watcher_parts[0])] = 1

                    try:
                        watcher_parts = watchers_reader.__next__()
                    except StopIteration:
                        break

                    if int(watcher_parts[0]) > last_id:
                        break

                # The watchers dict is copied for each project and should have the minimum necessary size
                watchers = {id: count for id, count in watchers.items() if count >= min_stars}

                pool = multiprocessing.Pool()
                results += pool.map(filter_repo, zip(project_lines, itertools.repeat(watchers)))
                project_lines = []
                watchers = {}
                print(str((project_index*100)/137611262) + '%')

            results = [project for project in results if project != None]
            results.sort(key=lambda tup: tup[2], reverse=True)

        with open(output_file, mode='w', encoding="ISO-8859-1",
                  newline='') as file:
            writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
            writer.writerows(results)


def filter_repo(args):
    parts = args[0]
    watchers = args[1]

    #Filter all repos that are not predominantly python or are deleted
    try:
        language = parts[5]
        deleted = parts[8]
    except IndexError:
        return# 'malformed_line'

    if language != 'Python':
        return

    id = int(parts[0])
    url = parts[1]
    descriptor = parts[4]
    forked = parts[7]

    url_parts = url.split('/')
    author = url_parts[-2]
    project = url_parts[-1]
    new_url = 'git://github.com/' + author + '/' + project + '.git'

    #Filter all repos that are forks, to prevent duplications
    if forked != '\\N' or deleted != '0':
        return# 'forked_or_deleted'

    #Filter all repos with non-english descriptions
    try:
        if len(descriptor) > 0 and detect(descriptor) != 'en':
            return# 'not_english'

    except LangDetectException:
        pass

    #Filter all projects with too few stars (watchers)
    stars = 0 if id not in watchers else watchers[id]
    if stars == 0:
        return# 'not_enough_stars'

    return((new_url, descriptor, stars))

if __name__ == "__main__":
    main()