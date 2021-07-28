from common import Common
import os
from preprocess import process_file

SHOW_TOP_CONTEXTS = 10
MAX_PATH_LENGTH = 8
MAX_PATH_WIDTH = 2


class InteractivePredictor:
    exit_keywords = ['exit', 'quit', 'q']

    def __init__(self, config, model):
        self.model = model
        self.config = config

    @staticmethod
    def read_file(input_filename):
        with open(input_filename, 'r', encoding="ISO-8859-1") as file:
            return file.readlines()

    def predict(self, input_paths):

        for input_path in input_paths:
            output = []
            _, predict_lines = process_file(input_path, 'test', 'tmp', 200, 1000)
            model_results = self.model.predict(predict_lines)

            for result in model_results:
                words = result[1]
                output.append(' '.join(Common.filter_impossible_names(words)) + '\n')

            output = [line.replace(' endofsentence', '.') for line in output]

            output_path = os.path.normpath(input_path).split(os.path.sep)
            output_path = os.path.sep.join(output_path[:-2])
            output_path = os.path.join(output_path, 'pred.txt')
            with open(output_path, 'w', encoding="ISO-8859-1") as file:
                file.writelines(output)

