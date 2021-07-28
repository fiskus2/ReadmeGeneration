import numpy as np
import tensorflow as tf

from config import Config
from interactive_predict import InteractivePredictor
from modelrunner import ModelRunner
from args import read_args
from glob import glob

if __name__ == '__main__':
    physical_devices = tf.config.list_physical_devices('GPU')
    if len(physical_devices):
        tf.config.experimental.set_memory_growth(physical_devices[0], True)
        # tf.config.set_visible_devices([], 'GPU')

    args = read_args()

    np.random.seed(args.seed)
    tf.random.set_seed(args.seed)

    if args.debug:
        config = Config.get_debug_config(args)
        tf.config.experimental_run_functions_eagerly(True)
    else:
        config = Config.get_default_config(args)

    print('Created model')
    if config.TRAIN_PATH:
        model = ModelRunner(config)
        model.train()
    #if config.TEST_PATH and not args.data_path:
        #model = ModelRunner(config)
        #results, precision, recall, f1, rouge, bleu = model.evaluate('test')
        #print('Accuracy: ' + str(results))
        #print('Precision: ' + str(precision) + ', recall: ' + str(recall) + ', F1: ' + str(f1))
        #print('Rouge: ', rouge)
        #print('Bleu: ', bleu)
    if args.predict:
        model = ModelRunner(config)
        predictor = InteractivePredictor(config, model)
        paths = glob(args.predict)

        if args.shard:
            paths = [path for path in paths if path[args.predict.find('*') + 1:].startswith(str(args.shard))]
        predictor.predict(paths)