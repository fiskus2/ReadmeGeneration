#Filters the ghtorrent dataset to remove repositories that are not of interest.
#Requires a projects.csv and watchers.csv file as downloaded from ghtorrent.

import csv
from datetime import datetime
from pathlib import Path
from langdetect import detect

def log(forked_or_deleted, malformed_lines, python_projects, not_enough_stars, not_english):
    now = datetime.now()
    log_string = now.strftime("%d.%m.%Y %H:%M:%S") + '\n'
    log_string = log_string + 'Forked or deleted: ' + str(forked_or_deleted) + '\n'
    log_string = log_string + 'Malformed lines: ' + str(malformed_lines) + '\n'
    log_string = log_string + 'Not english: ' + str(not_english) + '\n'
    log_string = log_string + 'Not enough stars: ' + str(not_enough_stars) + '\n'
    log_string = log_string + 'Python Projects: ' + str(python_projects) + '\n\n'
    with open('./log.txt', 'a+') as logfile:
        logfile.write(log_string)

def main():
    projects_file_path = r'./projects.csv'
    watchers_file_path = r'./watchers.csv'
    Path("./data").mkdir(parents=True, exist_ok=True)

    #The files are several GB large and are read incrementally
    with open(projects_file_path, encoding="ISO-8859-1") as projects_file:
        with open(watchers_file_path, encoding="ISO-8859-1") as watchers_file:
            watchers_iterator = csv.reader(watchers_file, delimiter=',', quotechar='"')

            i = 0
            java_projects = 0
            python_projects = 0
            forked_or_deleted = 0
            not_enough_stars = 0
            malformed_lines = 0
            not_english = 0

            watchers_data = watchers_iterator.__next__()

            python_data = []

            for parts in csv.reader(projects_file, delimiter=',', quotechar='"'):
                #Filter all repos that are not predominantly python or are deleted
                try:
                    language = parts[5]
                    deleted = parts[8]
                except IndexError:
                    malformed_lines += 1
                    continue

                if language != 'Python' and language != 'Java':
                    continue

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
                    forked_or_deleted += 1
                    continue

                #Filter all repos with non-english descriptions
                if len(descriptor) > 0 and detect(descriptor) != 'en':
                    not_english += 1
                    continue

                #Filter all projects with less than 100 stars (watchers)
                #The watchers.csv file contains one line per watcher. The line starts with the repo id being watched.
                stars = 0
                while int(watchers_data[0]) <= id:
                    if int(watchers_data[0]) == id:
                        stars += 1
                    try:
                        watchers_data = watchers_iterator.__next__()
                    except StopIteration:
                        break

                if stars < 100:
                    not_enough_stars += 1
                    continue


                python_projects += 1
                python_data.append((new_url, descriptor, stars))
                i += 1

                if i % 100 == 0:
                    log(forked_or_deleted, malformed_lines, python_projects, not_enough_stars,
                        not_english)

            log(forked_or_deleted, malformed_lines, java_projects, python_projects, not_enough_stars, not_english)
            python_data.sort(key=lambda tup: tup[2], reverse=True)

            with open('data/python-projects.csv', mode='w', encoding="ISO-8859-1",
                      newline='') as file:
                writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
                writer.writerows(python_data)

if __name__ == "__main__":
    main()