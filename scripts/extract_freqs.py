from os import listdir
from os.path import join
import pandas as pd


def extract_freqs():
    for year in listdir('entities'):
        year_data = pd.DataFrame()
        for journal_json in listdir(join(f'entities/{year}')):
            if journal_json.startswith('.'): continue

            data = pd.read_json(f'entities/{year}/{journal_json}')
            print(year, journal_json)
            try:
                wiki_counts = pd.DataFrame(data.link.value_counts())
                wiki_counts.index = [url.split('/')[-1] for url in wiki_counts.index]
            except:
                print(data)
                break

            col = ''.join([tok[:4] for tok in journal_json.split('_')])

            wiki_counts.columns = [col]

            if year_data.empty:
                year_data = wiki_counts
            else:
                year_data = pd.concat((year_data, wiki_counts), axis=1)
        year_data.fillna(0, inplace=True)
        year_data.to_json(f'freqs/{year}.json')