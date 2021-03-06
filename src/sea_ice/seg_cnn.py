# -*- coding: utf-8 -*-
#!/usr/bin/env python3
import os
from termcolor import colored

import numpy as np
np.random.seed(1337) # for reproducibility
from keras import backend as K
from keras import callbacks, optimizers, utils
from scipy.io import loadmat, savemat

from model_4 import create_model
from myUtility import get_path

#%% tensorflow setting
eat_all = 1
if not eat_all and 'tensorflow' == K.backend():
    import tensorflow as tf
    from keras.backend.tensorflow_backend import set_session
    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True
    config.gpu_options.per_process_gpu_memory_fraction = 0.7
    config.gpu_options.visible_device_list = "0"
    set_session(tf.Session(config=config))

## read data
path = get_path()
input_vector = '(1)'
# read validation data
x_val = np.array(loadmat(path['val']+'x_val_070426_3_'+input_vector[1]+'.mat')['x_val'])
y_val = np.array(loadmat(path['val']+'y_val_070426_3.mat')['y_val'])
# read training data
if 1:
    print('Use data augmentation')
    y_train = np.array(loadmat(path['aug']+'y_train_070426_3.mat')['y_train'])
    x_train = np.array([])
    for filename in sorted(os.listdir(path['aug'])): 
        if input_vector not in filename:
            continue
        print(filename)
        if 'x_train' in filename:
            x = loadmat(path['aug']+filename)
            temp_x = np.array(x['x_train'])
            if x_train.size == 0:
                x_train = temp_x
            else:
                x_train = np.concatenate((x_train, temp_x), axis=0)
            print(x_train.shape)
else: 
    print('Does not use data aegmentation')
    x_train = x_val
    y_train = y_val

#%% imput data and setting
n_labels = 2
batch_size = 50
epochs = 100
img_h, img_w = x_train.shape[1], x_train.shape[2]
y_train = utils.to_categorical(y_train, n_labels).astype('float32')
y_val = utils.to_categorical(y_val, n_labels).astype('float32')
# print(y_train.shape)

x_train = np.concatenate((x_train, x_val), axis=0)
y_train = np.concatenate((y_train, y_val), axis=0)

#%% CNN 
seg_cnn = create_model(img_h, img_w, x_train.shape[-1])
lr = 1 # change to 0.05
decay = 0.0
print(colored('@--------- Parameters ---------@','green'))
print('batch size: '+str(batch_size))
print('learning rate: '+str(lr))
print('decay:'+str(decay))
print('input vector: '+input_vector)
print(colored('@------------------------------@','green'))
if input_vector == '(4)':
    print('a')
    # optimizer = optimizers.Adagrad(lr=lr, epsilon=None, decay=decay)
    optimizer = optimizers.adadelta(lr=lr, rho=0.95, decay=decay)
    # optimizer = optimizers.SGD(lr=lr, momentum=0.9, decay=decay, nesterov=False)
else:
    # optimizer = optimizers.SGD(lr=0.01, momentum=0.9, decay=0.001, nesterov=False)
    optimizer = optimizers.adadelta(lr=lr, rho=0.95, decay=decay)


seg_cnn.compile(optimizer=optimizer, loss='binary_crossentropy',
    metrics=['accuracy'])
tb = callbacks.TensorBoard(
    log_dir=path['log']+'winter/',
    batch_size=batch_size,
    histogram_freq=0,
    write_graph=True,
    write_images=True)
earlystop = callbacks.EarlyStopping(
    monitor='val_loss',
    min_delta=1e-4, 
    patience=10)
ckp = callbacks.ModelCheckpoint(
    path['model']+'my_model_'+str(epochs)+'_'+input_vector[1]+'.h5', # file path
    monitor='val_loss',
    verbose=0,
    save_best_only=True, save_weights_only=False, mode='auto', period=1)

#%% training
seg_cnn.summary()

input_vector = input_vector[1]
seg_cnn.fit(x_train, y_train,
    batch_size=batch_size,
    validation_data=(x_val, y_val),
    verbose=1,
    epochs=epochs,
    shuffle=True,
    callbacks=[tb,ckp])
# seg_cnn.save(path['model']+'my_model_'+str(epochs)+'_'+input_vector+'.h5')

print('Session over')
