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
import os, stat, shutil
import itertools

download_dir = '.\\data\\python-projects-med\\'
input_file = '.\\data\\python-projects-med\\filtered.csv'

def handleRemoveReadonly(func, path, exc):
    new_path = u'\\\\?\\' + os.path.abspath(path) if '?' not in path else path
    os.chmod(new_path, stat.S_IRWXU| stat.S_IRWXG| stat.S_IRWXO) # 0777
    func(new_path)

#Downloads one repository. Used for parallelization
def download_repo(args):
    folder, parts, i, already_downloaded = args

    url = parts[0]
    descriptor = parts[1]

    url_parts = url.split('/')
    author = url_parts[-2] #e.g. 'vinta'
    project = url_parts[-1] #e.g. 'awesome-python.git'

    if author + ',' + project[:-4] in already_downloaded:
        return


    # ',' is used as delimiter, because it cannot occur in github project names
    repo_dir = os.path.join(folder, str(i) + ',' + author + ',' + project[:-4])

    if i % 100 == 0:
        print(str(i))

    try:
        Repo.clone_from('git://github.com/' + author + '/' + url_parts[-1], repo_dir)
    except Exception as e:
        try:
            shutil.rmtree(u'\\\\?\\' + os.path.abspath(repo_dir), ignore_errors=False, onerror=handleRemoveReadonly)
        except FileNotFoundError:
            pass

        print('')
        print(str(e))
        print(str(url))
        print('')
        return

    #Delete all files that are not python or Readme files to save space
    try:
        for root, dirs, files in os.walk(repo_dir):
            for file in files:
                if not file.lower().startswith('readme') \
                        and not file.lower().endswith('.py') \
                        or file.lower() == 'setup.py':
                    os.chmod(os.path.join(root, file), stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                    os.remove(os.path.join(root, file))

        #The project description is added as a new file
        with open(repo_dir + '\\descriptor', 'w', encoding="ISO-8859-1") as file:
            file.write(descriptor)

    except (FileNotFoundError, OSError):
        #This happens when a path gets too long or has too many levels of symbolic links. The project is discarded in that case
        try:
            shutil.rmtree(repo_dir, ignore_errors=False, onerror=handleRemoveReadonly)
        except OSError:
            print('OSError in project: ', repo_dir)


def main():
    Path(download_dir).mkdir(parents=True, exist_ok=True)
    downloaded_folders = glob.glob(download_dir + '*\\*\\')

    #check which projects are already downloaded
    already_downloaded = []
    for folder in downloaded_folders:
        folder = os.path.basename(os.path.normpath(folder))
        name = folder[folder.find(',') + 1:]
        already_downloaded.append(name)

    filenames = glob.glob(input_file)

    i = 0

    for filename in filenames:
        with open(filename, encoding="ISO-8859-1", newline='') as projects_file:
            reader = csv.reader(projects_file, delimiter=',', quotechar='"')
            rows = list(reader)

            # Split into train, test and validation folders 80-10-10
            split_paths = []
            for i in range(len(rows)):
                rnd = random.randint(0, 9)
                if rnd == 0:
                    split_folder = 'test\\'
                elif rnd == 1:
                    split_folder = 'validation\\'
                else:
                    split_folder = 'train\\'
                split_paths.append(download_dir + split_folder)

            args = list(zip(split_paths, rows, range(i, i + len(rows)), itertools.repeat(already_downloaded)))

            i += len(rows)
            results = Parallel()(map(delayed(download_repo), args))
            print(str(results))


if __name__ == "__main__":
    main()