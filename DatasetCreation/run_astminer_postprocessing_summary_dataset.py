from astminer_postprocessing import main as postprocess
from glob import glob
import os
from pathlib import Path

dataset_path = str(Path("./data/summary-dataset/processed/train/*/py/"))
output_path = "./data/summary-dataset/processed/train/*/postprocessed/"

projects = glob(dataset_path)
for project_path in projects:
    project_folder = project_path.split(os.path.sep)[-2]
    project_output_path = output_path.replace('*', project_folder)

    postprocess(project_path + os.path.sep, project_output_path)