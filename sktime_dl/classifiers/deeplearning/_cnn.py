# Time convolutional neural network, adapted from the implementation from Fawaz et. al
# https://github.com/hfawaz/dl-4-tsc/blob/master/classifiers/cnn.py
#
# Network originally proposed by:
#
# @article{zhao2017convolutional,
#   title={Convolutional neural networks for time series classification},
#   author={Zhao, Bendong and Lu, Huanzhang and Chen, Shangfeng and Liu, Junliang and Wu, Dongya},
#   journal={Journal of Systems Engineering and Electronics},
#   volume={28},
#   number={1},
#   pages={162--169},
#   year={2017},
#   publisher={BIAI}
# }

__author__ = "James Large"

import keras
import numpy as np

from sktime_dl.classifiers.deeplearning._base import BaseDeepClassifier


class CNNClassifier(BaseDeepClassifier):

    def __init__(self,
                 nb_epochs=2000,
                 batch_size=16,
                 kernel_size=7,
                 avg_pool_size=3,
                 nb_conv_layers=2,
                 filter_sizes=[6, 12],

                 random_seed=0,
                 verbose=False,
                 model_save_directory=None):

        self.verbose = verbose
        self.model_save_directory = model_save_directory

        self.callbacks = []
        self.random_seed = random_seed
        self.random_state = np.random.RandomState(self.random_seed)

        # calced in fit
        self.input_shape = None
        self.model = None
        self.history = None

        # TUNABLE PARAMETERS
        self.nb_epochs = nb_epochs
        self.batch_size = batch_size
        self.kernel_size = kernel_size
        self.avg_pool_size = avg_pool_size
        self.nb_conv_layers = nb_conv_layers
        self.filter_sizes = filter_sizes

    def build_model(self, input_shape, nb_classes, **kwargs):
        """
        Construct a compiled, un-trained, keras model that is ready for training
        ----------
        input_shape : tuple
            The shape of the data fed into the input layer
        nb_classes: int
            The number of classes, which shall become the size of the output layer
        Returns
        -------
        output : a compiled Keras Model
        """
        padding = 'valid'
        input_layer = keras.layers.Input(input_shape)

        if input_shape[0] < 60:  # for italypowerondemand dataset
            padding = 'same'

        if len(self.filter_sizes) > self.nb_conv_layers:
            self.filter_sizes = self.filter_sizes[:self.nb_conv_layers]
        elif len(self.filter_sizes) < self.nb_conv_layers:
            self.filter_sizes = self.filter_sizes + [self.filter_sizes[-1]] * (
                    self.nb_conv_layers - len(self.filter_sizes))

        conv = keras.layers.Conv1D(filters=self.filter_sizes[0],
                                   kernel_size=self.kernel_size,
                                   padding=padding,
                                   activation='sigmoid')(input_layer)
        conv = keras.layers.AveragePooling1D(pool_size=self.avg_pool_size)(conv)

        for i in range(1, self.nb_conv_layers):
            conv = keras.layers.Conv1D(filters=self.filter_sizes[i],
                                       kernel_size=self.kernel_size,
                                       padding=padding,
                                       activation='sigmoid')(conv)
            conv = keras.layers.AveragePooling1D(pool_size=self.avg_pool_size)(conv)

        flatten_layer = keras.layers.Flatten()(conv)
        output_layer = keras.layers.Dense(units=nb_classes, activation='sigmoid')(flatten_layer)

        model = keras.models.Model(inputs=input_layer, outputs=output_layer)
        model.compile(loss='mean_squared_error', optimizer=keras.optimizers.Adam(),
                      metrics=['accuracy'])

        return model

    def fit(self, X, y, input_checks=True, **kwargs):
        """
        Build the classifier on the training set (X, y)
        ----------
        X : array-like or sparse matrix of shape = [n_instances, n_columns]
            The training input samples.  If a Pandas data frame is passed, column 0 is extracted.
        y : array-like, shape = [n_instances]
            The class labels.
        input_checks: boolean
            whether to check the X and y parameters
        Returns
        -------
        self : object
        """
        X = self.check_and_clean_data(X, y, input_checks=input_checks)

        y_onehot = self.convert_y(y)
        self.input_shape = X.shape[1:]

        self.model = self.build_model(self.input_shape, self.nb_classes)

        if self.verbose:
            self.model.summary()

        self.history = self.model.fit(X, y_onehot, batch_size=self.batch_size, epochs=self.nb_epochs,
                                      verbose=self.verbose, callbacks=self.callbacks)

        self.save_trained_model()

        return self
