from os import listdir
from os.path import isdir, join, abspath

import pandas as pd

from fuzzywuzzy import fuzz, process
from scipy.spatial.distance import pdist

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import pairwise_distances as pdist

import matplotlib.pyplot as plt

import numpy as np


ROOT = abspath('..')


query = 'Helsingfors'
metric = 'cosine'

bower = CountVectorizer(lowercase=True, ngram_range=(1, 5), analyzer='char_wb')


for year in filter(lambda x: x.startswith('19'), listdir('../entities')):
    year_dir = join(ROOT, 'entities', year)

    for paper in filter(lambda x: x.endswith('.json'), listdir(year_dir)):
        
        data = pd.read_json(join(year_dir, paper))

        data_counts = data.mention.value_counts()

        print(data_counts)

        X = bower.fit_transform(data_counts.index)

        dists = pd.DataFrame(pdist(X, metric=metric, n_jobs=-1), columns=data_counts.index, index=data_counts.index)

        sims = 1 - dists

        nns = pd.DataFrame(sims[query].sort_values(ascending=False))
        nns.rename(columns={query:metric}, inplace=True)

        # nns['str_len'] = [len(s) for s in nns.index]
        nns['levenshtein'] = [(fuzz.ratio(query.lower(), s.lower()) / 100) for s in nns.index]

        # print(nns)

        nns.plot(alpha=.5)
        plt.savefig('similarity.png')

        # nns.loc[nns.cosine < .5].str_len.plot()
        # plt.savefig('str_len.png')

        # nns.loc[nns.cosine < .5].fuzzy.plot()
        # plt.savefig('fuzzy.png')

        for item in filter(lambda x: x.cosine > .5, nns.itertuples()):
            print(f'[{item.Index}] : {item.cosine:.4}')

        # nns.to_csv('test.csv')
        break

    break



def get_fuzz(data_counts, query):
    for mention in data_counts.index.tolist():
        print(mention, fuzz.ratio(query, mention))