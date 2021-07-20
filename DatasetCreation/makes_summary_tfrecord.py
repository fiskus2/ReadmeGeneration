#Creates a tfrecord to train pegasus
#Features are the predicted docstrings of core functions, targets are readme files of the corresponding project

import pandas as pd
import tensorflow as tf
from glob import glob
import os
from pathlib import Path

dataset_part = 'train'
dataset_path = str(Path('./data/summary-dataset/processed/' + dataset_part + '/*'))
save_path = str(Path('./data/summary-dataset/processed/' + dataset_part + '.tfrecord'))
os.makedirs(os.path.dirname(save_path), exist_ok=True)

inputs = []
targets = []
projects = glob(dataset_path)
for project_path in projects:
    try:
        with open(os.path.join(project_path, 'pred.txt'), 'r', encoding="ISO-8859-1") as file:
            input = file.read()

        with open(os.path.join(project_path, 'readme.md'), 'r', encoding="ISO-8859-1") as file:
            target = file.read()

    except FileNotFoundError:
        continue

    inputs.append(input)
    targets.append(target)

input_dict = dict(
    inputs=inputs,
    targets=targets
    )

data = pd.DataFrame(input_dict)
with tf.io.TFRecordWriter(save_path) as writer:
    for row in data.values:
        inputs, targets = row[:-1], row[-1]
        example = tf.train.Example(
            features=tf.train.Features(
                feature={
                    "inputs": tf.train.Feature(bytes_list=tf.train.BytesList(value=[inputs[0].encode('utf-8')])),
                    "targets": tf.train.Feature(bytes_list=tf.train.BytesList(value=[targets.encode('utf-8')])),
                }
            )
        )
        writer.write(example.SerializeToString())
