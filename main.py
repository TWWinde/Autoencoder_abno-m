import os
import argparse
import random
import logging
import numpy as np
from absl import app, flags
import tensorflow as tf

from input_pipeline.dataset import ImageDataPipeline
from train import Trainer
from utilss import utils_params, utils_misc
import gin
from models import autoencoder
parser = argparse.ArgumentParser(description='Train model')
parser.add_argument('--model', choices=['autoencoder', 'other_model'],
                    default='autoencoder', help='choose model')
parser.add_argument('--mode', choices=['train', 'test'], default='train', help='train or test')
parser.add_argument('--evaluation', choices=['evaluate_fl', 'confusionmatrix', 'Dimensionality_Reduction', 'ROC'],
                    default='evaluate_fl', help='evaluation methods')
parser.add_argument('--checkpoint-file', type=str, default='./ckpts/',
                    help='Path to checkpoint.')

args = parser.parse_args()


# fix the seed to make the training repeatable
def setup_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)
    os.environ['TF_DETERMINISTIC_OPS'] = '1'


setup_seed(66)


@gin.configurable
def main(argv):
    # generate folder structures
    run_paths = utils_params.gen_run_folder()

    # set loggers
    utils_misc.set_loggers(run_paths['path_logs_train'], logging.INFO)

    # gin-config
    gin.parse_config_files_and_bindings(['config.gin'], [])
    utils_params.save_config(run_paths['path_gin'], gin.config_str())

    # setup pipeline
    image_pipeline = ImageDataPipeline(images_list, batch_size=32)

    # 划分数据集并创建训练集、验证集和测试集的数据管道
    ds_train, ds_val, ds_test = image_pipeline.split_dataset()


    if args.model == 'autoencoder':
        model = autoencoder
    elif args.model == 'other_model':

       pass
    else:
        print('Error, model does not exist')

    model.summary()

    if args.mode == 'train':
        trainer = Trainer(model, ds_train, ds_val, ds_info, run_paths)
        for _ in trainer.train():
            continue
    else:
        checkpoint = tf.train.Checkpoint(step=tf.Variable(0), model=model)
        manager = tf.train.CheckpointManager(checkpoint,
                                             directory=args.checkpoint_file,
                                             max_to_keep=3)

        checkpoint.restore(manager.latest_checkpoint)
        if manager.latest_checkpoint:
            tf.print("restored")
        else:
            tf.print("Error")

        if args.evaluation == 'evaluate_fl':
            ds_test = ds_test.batch(32)
            evaluate_fl(model, ds_test)
        elif args.evaluation == 'confusionmatrix':
            confusionmatrix(model, ds_test)
        elif args.evaluation == 'Dimensionality_Reduction':
            Dimensionality_Reduction(model, ds_test)
        elif args.evaluation == 'ROC':
            ROC(model, ds_test)


if __name__ == "__main__":
    app.run(main)
