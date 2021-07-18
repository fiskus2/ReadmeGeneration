#Reconstructs original directories from CodeSearchNets jsonl files: https://s3.amazonaws.com/code-search-net/CodeSearchNet/v2/python.zip
from glob import glob
import os
import json
from download_repos import download_repo
from joblib import Parallel, delayed

#input_dir shall contain 'train', 'test' and 'validation' folders, which contain the extracted .jsonl files
input_dir = 'C:/Users/Elias/Downloads/python/python/final/jsonl/'
output_dir = './data/summary-dataset/'

def download_summary_repos():
    os.makedirs(output_dir, exist_ok=True)

    dirs = glob(os.path.join(input_dir, '*'))
    if len(dirs) == 0:
        dirs = [input_dir]

    for dir in dirs:
        parts = glob(os.path.join(dir, '*.jsonl'))
        base_dir = os.path.join(output_dir, os.path.basename(dir))
        os.makedirs(base_dir, exist_ok=True)

        # check which projects are already downloaded
        downloaded_folders = glob(os.path.join(base_dir, '*'))
        already_downloaded = []
        for folder in downloaded_folders:
            folder = os.path.basename(os.path.normpath(folder))
            name = folder[folder.find(',') + 1:]
            already_downloaded.append(name)

        for part in parts:
            with open(part) as file:
                content = file.readlines()
            data = [json.loads(jline) for jline in content]

            urls = []
            for fields in data:
                author, project_name = fields['repo'].split('/')
                url = 'git://github.com/' + author + '/' + project_name + '.git'
                urls.append(url)
            urls = set(urls)

            i = 0
            args = []
            for url in urls:
                args.append((base_dir, (url, ''), i, already_downloaded))
                i += 1

            results = Parallel()(map(delayed(download_repo), args))

if __name__ == '__main__':
    download_summary_repos()