import os
import time
from collections import Counter
import yaml
import scipy
import pickle
import shutil
import numpy as np
import pandas as pd
from sys import platform
from pprint import pprint
import matplotlib
import matplotlib.pyplot as plt

matplotlib.use('agg')
getwd = os.getcwd

def setwd(path):
    owd = os.getcwd()
    os.chdir(path)
    return owd

MB = 1024 * 1024

gpus = nvidia = nvidia_smi = lambda: os.system('nvidia-smi')

def set_cuda_devices(i=""):
    """Set one or more GPUs to use for training by index or all by default
        Args:
            `i` may be a list of indices or a scalar integer index
                default='' # <- Uses all GPUs if you pass nothing
    """
    def list2csv(l):
        s = ''
        ll = len(l) - 1
        for i, x in enumerate(l):
            s += str(x)
            s += ',' if i < ll else ''
        return s 
    if i.__eq__(''): # Defaults to ALL
        i = list(range(DEV_COUNT))
    if isinstance(i, list):
        i = list2csv(i)

    # ensure other gpus not initialized by tf
    os.environ['CUDA_VISIBLE_DEVICES'] = str(i)
    print("CUDA_VISIBLE_DEVICES set to {}".format(i))
    
def set_gpu_tf(gpu="", gpu_max_memory=None):
    """Set gpu for tensorflow upon initialization.  Call this BEFORE importing tensorflow"""
    set_cuda_devices(gpu)
    import tensorflow as tf
    gpus = tf.config.experimental.list_physical_devices('GPU')
    print('\nUsed gpus:', gpus)
    if gpus:
        try:
            for gpu in gpus:
                print("Setting memory_growth=True for gpu {}".format(gpu))
                tf.config.experimental.set_memory_growth(gpu, True)
                if gpu_max_memory is not None:
                    print("Setting GPU max memory to: {} mB".format(gpu_max_memory))
                    tf.config.experimental.set_virtual_device_configuration(
                        gpu, 
                        [tf.config.experimental.VirtualDeviceConfiguration(
                            memory_limit=gpu_max_memory)]
                        )
        except RuntimeError as e:
            print(e)

def get_gpu_available_memory():
    return list(
        map(
            lambda x: N.nvmlDeviceGetMemoryInfo(
                N.nvmlDeviceGetHandleByIndex(x)).free // MB, range(DEV_COUNT)
            )
        )

def get_based_gpu_idx():
    mem_free = get_gpu_available_memory()
    idx = np.argmax(mem_free)
    print("GPU:{} has {} available MB".format(idx, mem_free[idx]))
    return idx

def set_based_gpu():
    idx = get_based_gpu_idx()
    set_gpu_tf(str(idx))


try:
    import pynvml as N
    N.nvmlInit()
    DEV_COUNT = N.nvmlDeviceGetCount()
    NVML_ERR = False
except:
    print("Exception caught in pynvml.nvmlInit()")
    DEV_COUNT = 0
    NVML_ERR = True


FLAGS = {}

if FLAGS.get('gpu_slots', "BASED").upper() == "BASED":
    if not NVML_ERR:
        set_based_gpu()
    else:
        print("Error in set_based_gpu()\nDefaulting to all visible GPUs as a fallback...")
        set_gpu_tf() # `All` if there's an exception thrown in pyNVML
else:
    try:
        set_gpu_tf(FLAGS.get('gpu_slots', '0'))
    except:
        print("Could not configure GPU devices for tensorflow...")

def is_numpy(x):
    return x.__class__ in [
        np.ndarray,
        np.rec.recarray,
        np.char.chararray,
        np.ma.masked_array
    ]

def is_scalar(x):
    if is_numpy(x):
        return x.ndim == 0
    if isinstance(x, str) or type(x) == bytes:
        return True
    if hasattr(x, "__len__"):
        return len(x) == 1
    try:
        x = iter(x)
    except:
        return True
    return np.asarray(x).ndim == 0

def unpickle(fp):
    with open(fp, 'rb') as f:
        x = pickle.load(f)
    return x

def jload(fp):
    with open(fp, 'rb') as f:
        x = json.load(f)
    return x

def loadz(fp, key='arr_0'):
    x = np.load(fp, allow_pickle=True)
    if is_scalar(key):
        return x[key]
    return {k: v for k,v in x.items() if k in keys}

# Local Imports
from .utils import *

# Set constants
from tensorflow import random
random.set_seed(FLAGS.get('random_seed', 1337))

# Load raw data
DATA_DIR = "./data"
PRDP = PUDGY_RAW_DATA_PATH = os.path.join(DATA_DIR, "pudgypenguins_data_raw")
PDF = PUDGY_RAW_DF = jload(PUDGY_RAW_DATA_PATH)

# One hot data
PUDGY_ONEHOT_PATH = os.path.join(DATA_DIR, "pudgy_onehot.npz")
POH = PUDGY_ONEHOT = loadz(PUDGY_ONEHOT_PATH)

# Rarity data
ADF = ALL_RARITY_DF = unpickle(os.path.join(DATA_DIR, "all_rarity_df.pickle"))
PUDGY_RARITY_PATH = os.path.join(DATA_DIR, "pudgypenguins.xlsx")
RDF = PUDGY_RARITY_DF = pd.read_excel(PUDGY_RARITY_PATH)

# TODO: Training data
ts = traits = POH
rs = rarity_scores = RDF['Rarity score']
rsn = rarity_scores_norm = RDF['Rarity score normed']

# NEED TRANSACTION HISTORY!
# TIMESERIES MODEL
# OPENSEA API?