from os.path import join, abspath, isfile
from os import listdir

import pandas as pd
import matplotlib.pyplot as plt

ROOT = abspath('..')


papers = ['arbeiter_zeitung', 'helsingin_sanomat',
            'illustrierte_kronen_zeitung', 'le_matin', 'l_oeuvre']

years = ['1913', '1914', '1915', '1916', '1917', '1918', '1919', '1920']


stats = pd.DataFrame(index=years, columns=papers)
# print(stats)

# for year in filter(lambda x: x.startswith('19'), listdir('../entities')):
#     year_dir = join(ROOT, 'entities', year)

#     for paper in papers: #filter(lambda x: x.endswith('.json'), listdir(year_dir)):
#         if not isfile(join(year_dir, paper  + '.json')): continue

#         print('Reading', join(year_dir, paper))

#         data = pd.read_json(join(year_dir, paper  + '.json'))


#         stats.loc[year][paper] = data.mention.value_counts().shape[0]

# print(stats)

stats = pd.read_json('stats.json')

plt.figure()

stats.plot.bar(stacked=True, rot=1, colormap='Set3')
plt.grid()
plt.savefig('stats.png')


stats.to_latex('stats.tex')