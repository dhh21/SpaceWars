import json
import pandas as pd


def extract_locations():
    for root, dirs, files in os.walk(DATA_PATH):
        if root == DATA_PATH: continue
        print(root)
        subpath = root.split(DATA_PATH)[-1].split('/')

        if len(subpath) == 3:
            year = subpath[1]
            journal = subpath[2]
        else:
            continue

        locations = []

        for f in files:
            PATH = join(root, f)
            data = json.load(open(PATH))

            date = data['issue']['date']

            articles = data['articles']

            for article in articles:
                # if article['named_entities']:
                #    location_mentions = [ne['type'] == 'LOC' for ne in article['named_entities']]
                #    if True in location_mentions:
                #        lengths[year][journal].append(len(article['full_text']))

                if article['named_entities']:
                    for ne in article['named_entities']:
                        if ne['type'] == 'LOC' and ne['link']:
                            ne['date'] = date
                            del ne['type']
                            locations.append(ne)

        with open(join('entities', year, f'{journal}.json'), 'w') as out:
            json.dump(locations, out)