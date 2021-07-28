import os

streams = []
for i in range(10):
    streams.append(os.popen('python3 code2seq.py --shard ' + str(i) + ' --test data/docstring-dataset/docstring-dataset.test.c2s --load_path ./models/docstring-dataset/ --model_path models/docstring-dataset/checkpoints --predict C:/Workspace/ReadmeGeneration/DatasetCreation/data/summary-dataset/processed/test/*/postprocessed/data.csv'))

for i in range(10):
    with open('logs/' + str(i) + '.log', 'w') as file:
        file.write(streams[i].read())
