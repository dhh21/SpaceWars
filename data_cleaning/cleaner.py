from angle_based import AngleBased
from l_method import L_method
from os import listdir
from os.path import isfile, join, abspath

import pandas as pd
import numpy as np

from fuzzywuzzy import fuzz
from scipy.spatial.distance import cdist

from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.pipeline import Pipeline

import matplotlib.pyplot as plt

import gc

from tqdm import tqdm

import re

from os import makedirs


ROOT = abspath('..')
OUTPUT_DIR = 'output_clean'

vectorizer = Pipeline([
    ('bow', CountVectorizer(lowercase=True, ngram_range=(1, 5), analyzer='char_wb')),
    # ('tfidf', TfidfTransformer())
])


punct = re.compile(r"[:\.,'/\s]")


papers = ['arbeiter_zeitung', 'helsingin_sanomat',
            'illustrierte_kronen_zeitung', 'le_matin', 'l_oeuvre']


for year in filter(lambda x: x.startswith('19'), listdir('../entities')):
    year_dir = join(ROOT, 'entities', year)

    for paper in papers: #filter(lambda x: x.endswith('.json'), listdir(year_dir)):
        
        print('Reading', join(year_dir, paper))

        PATH = join(OUTPUT_DIR, year, paper.split('.json')[0])
        makedirs(PATH, exist_ok=True)

        if not isfile(join(year_dir, paper + '.json')) or isfile(join(PATH, 'freqs.csv')): continue

        data = pd.read_json(join(year_dir, paper  + '.json'))

        data_counts = data.mention.value_counts()

        del [[data]]
        gc.collect()        

        # plt.figure()
        # data_counts.iloc[:100].plot()
        # plt.savefig('mention_freqs.png')

        X = vectorizer.fit_transform(data_counts.index)
        
        print(X.shape)

        freqs = pd.DataFrame(data_counts)

        # freqs.drop(freqs.iloc[freqs.shape[0] // 10 : ].index, axis=0, inplace=True)

        # l_method = L_method()
        # l_method.fit(freqs, 'mention')

        visited = []

        for query in freqs.iloc[: 100].index.tolist():
            if query in visited: continue

            trimmed_query = punct.sub('', query)
            candidates_fname = join(PATH, f'{trimmed_query}_candidates.csv')

            if isfile(candidates_fname): continue

            print(f'QUERY: [{query}]')

            query_vec = vectorizer.transform([query])

            n_batches = 100
            batch_size = int(X.shape[0] / n_batches)

            ### first batch initialized
            dists = 1 - cdist(query_vec.A, X[:batch_size].A, metric='cosine').T

            ### loop starts with 2nd iteration!
            for batch_idx in tqdm(range(1, n_batches+1), desc='Calculating distances'):
                start_idx = batch_idx*batch_size
                end_idx = (batch_idx+1)*batch_size if batch_idx < n_batches else data_counts.shape[0]

                current_dists = 1 - cdist(query_vec.A, X[start_idx : end_idx].A, metric='cosine').T

                dists = np.vstack((dists, current_dists))

            dists = pd.DataFrame(dists, index=data_counts.index, columns=['cos'])

            dists['freqs'] = data_counts

            dists.sort_values(ascending=False, by='cos', inplace=True)

            dists['levenshtein'] = [(fuzz.ratio(query.lower(), s.lower()) / 100) for s in dists.index]

            # dists.drop(dists.iloc[dists.shape[0] // 4:].index, axis=0, inplace=True)

            # angle_method = AngleBased(5)
            # angle_method.fit(dists, 'cos')

            l_method = L_method()
            l_method.fit(dists, 'cos')


            l_method.plot_loss(join(PATH, f'{trimmed_query}_loss'))
            l_method.plot_cutoff(dists, ['cos', 'levenshtein'], join(PATH, f'{trimmed_query}_cutoff'), title=query)

            dists = dists.iloc[:l_method.current_knee]
            visited.extend(dists.index.tolist())

            dists['query'] = [query] * l_method.current_knee
            dists.to_csv(candidates_fname)

            data_counts.to_csv(join(PATH, 'freqs.csv'))