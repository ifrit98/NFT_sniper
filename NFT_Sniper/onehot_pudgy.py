import json
import requests
import pandas as pd
import numpy as np

from PIL import Image
from io import BytesIO

def logical2idx(x):
    x = np.asarray(x)
    return np.arange(len(x))[x]

def dict_up(l):
    """Wrap up a list of dicts into one dict"""
    raise NotImplementedError

def flatten_traits(d):
    return np.concatenate([list(v.keys()) for v in d.values()])

def encode_traits(t, dtype='int32'):
    x = np.array(list(map(lambda x: TRAIT2IDX[x['value'].lower()], t)))
    y = np.zeros(N_TRAITS, dtype=dtype)
    for i in x:
        y[i] = 1
    return y

def decode_traits(t):
    i = logical2idx(t.astype(bool))
    return TRAITS_LIST[i]

x = json.load(open('./data/pudgypenguins_data_raw', 'r'))
md = x['pudgypenguins']['project_metadata']['collection']
sts = md['stats']
nfts = x['pudgypenguins']['nfts']
a = asset_link = md['image_url']
all_traits = md['traits']

TRAITS = set(sorted(flatten_traits(all_traits)))
TRAITS_LIST = np.asarray(list(TRAITS))
N_TRAITS = len(TRAITS)
TRAIT_SUPERCLASSES = set(all_traits)
TRAIT2IDX = dict(zip(TRAITS, range(N_TRAITS)))
IDX2TRAIT = dict(zip(range(N_TRAITS), TRAITS))

#preallocate
X = np.zeros((len(nfts), N_TRAITS))
for i, (nm, nft) in enumerate(nfts.items()):
    X[i] = encode_traits(nft['attributes'])

# save one hot vector
with open('./data/pudgy_onehot.npz', 'wb') as f:
    np.savez(f, X) # penguin indexed by range(0, 8887)