#Download github repositories to create a dataset.
#Requires a filtered csv file of repositories as created by filter_ghtorrent.py
import os
import csv
from git import Repo
from pathlib import Path
import glob
import shutil
from joblib import Parallel, delayed
import random

#Downloads one repository. Used for parallelization
def download_repo(args):
    parts = args[0]
    i = args[1]

    url = parts[0]
    descriptor = parts[1]

    url_parts = url.split('/')
    author = url_parts[-2]
    project = url_parts[-1]

    #Split into train, test and validation folders 80-10-10
    rnd = random.randint(0, 9)
    if rnd == 0:
        split_folder = 'test/'
    elif rnd == 1:
        split_folder = 'validation/'
    else:
        split_folder = 'train/'

    repo_dir = './data/code/' + split_folder + str(i) + '-' + author + '-' + project

    if i % 100 == 0:
        print(str(i))

    try:
        Repo.clone_from(url, repo_dir)
    except Exception as e:
        try:
            shutil.rmtree(repo_dir)
        except FileNotFoundError:
            pass

        print('')
        print(str(e))
        print(str(url))
        print('')
        return

    #Delete all files that are not python or Readme files to save space
    for root, dirs, files in os.walk(repo_dir):
        for file in files:
            if not file.lower().startswith('readme') \
                    and not file.lower().endswith('.py') \
                    or file.lower() == 'setup.py':
                os.remove(os.path.join(root, file))

    #The project description is added as a new file
    with open(repo_dir + '/descriptor', 'w') as file:
        file.write(descriptor)


def main():
    Path("./data/code/").mkdir(parents=True, exist_ok=True)
    filenames = glob.glob('./data/*.csv')

    i = 0

    for filename in filenames:
        with open(filename, encoding="ISO-8859-1", newline='') as projects_file:
            reader = csv.reader(projects_file, delimiter=',', quotechar='"')
            rows = list(reader)
            args = list(zip(rows, range(i, i + len(rows))))

            i += len(rows)
            results = Parallel(n_jobs=4, backend="threading")(map(delayed(download_repo), args))
            print(str(results))


if __name__ == "__main__":
    main()