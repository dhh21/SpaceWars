import os
import csv
import math
import json
import pandas as pd
from shapely import wkt
from pathlib import Path
from timeit import default_timer as timer

NEWSPAPER_NAMES = {
    'arbeiter_zeitung': 'Arbeiter-Zeitung',                         # done
    'neue_freie_presse': 'Neue Freie Presse',                       # done
    'illustrierte_kronen_zeitung': 'Illustrierte Kronen-Zeitung',   # done
    'helsingin_sanomat': 'Helsingin Sanomat',                       # done
    'le_matin': 'Le Matin',                                         # missing 1919-1920
    'l_oeuvre': 'L\'Œuvre'                                          # missing 1915-1916
}


def get_missing_info(data_path):
    dict_dict = {}
    for filename in os.listdir(data_path):
        with open(os.path.join(data_path, filename), 'r') as json_file:
            json_obj = json.load(json_file)
            for article in json_obj['articles']:
                if article['named_entities']:
                    for ne in article['named_entities']:
                        if ne['type'] == 'LOC':
                            dict_dict[ne['id']] = {'article_id': article['id'],
                                                   'fulltext': article['full_text'],
                                                   'issue_id': json_obj['issue']['id'],
                                                   'lang': json_obj['issue']['language']}
    return dict_dict


def get_coordinates(geometry):
    if geometry:
        geo_as_string = wkt.loads(geometry)
        lat = geo_as_string.centroid.y
        lon = geo_as_string.centroid.x
        return lat, lon


def get_context(fulltext, start_idx, end_idx):
    return fulltext[:int(start_idx)], fulltext[int(end_idx):]


def generate_article_link(issue_id, article_id):
    return 'https://platform.newseye.eu/de/catalog/' + issue_id + '#' + article_id


def combine_data(csv_path, dict_dict, np_name):
    dict_list = []
    with open(csv_path, 'r', newline='', ) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader)
        for row in csv_reader:
            mention_dict = {
                'mention_id': row[1],
                'mention': row[4],
                'start_idx': row[5],
                'end_idx': row[6],
                'left_context': get_context(dict_dict[row[1]]['fulltext'], row[5], row[6])[0],
                'right_context': get_context(dict_dict[row[1]]['fulltext'], row[5], row[6])[1],
                'article_id': dict_dict[row[1]]['article_id'],
                'issue_id': dict_dict[row[1]]['issue_id'],
                'article_link': generate_article_link(dict_dict[row[1]]['issue_id'], dict_dict[row[1]]['article_id']),
                'newspaper': NEWSPAPER_NAMES[np_name],
                'date': row[8],
                'lang': dict_dict[row[1]]['lang'],
                'wikidata_link': row[2],
                'address': row[9],
                'geometry': row[11],
                'lat': get_coordinates(row[11])[0] if get_coordinates(row[11]) else '',
                'lon': get_coordinates(row[11])[1] if get_coordinates(row[11]) else ''
            }
            dict_list.append(mention_dict)
    return dict_list


def save_data(data_path):
    split_path = data_path.split('/')
    np_name = split_path[-1]
    np_year = split_path[-2]
    save_path = f'/Volumes/Untitled/DHH21/combined_data/combined_data_{np_name}_{np_year}.csv'
    csv_path = f'/Volumes/Untitled/DHH21/enriched_csvs/{np_name}_enriched/{np_name}_{np_year}_enriched.csv'
    infos_from_json = get_missing_info(data_path)
    combined_data = combine_data(csv_path, infos_from_json, np_name)
    pd.DataFrame.from_dict(combined_data).to_csv(save_path, index=False)


if __name__ == '__main__':
    print('running assembling_data.py...')
    start = timer()
    # TODO: change newspaper name
    newspaper_name = 'helsingin_sanomat'
    for year in ['1913', '1914', '1915', '1916', '1917', '1918', '1919', '1920']:
        # TODO: change paths
        file = Path(f'/Volumes/Untitled/DHH21/enriched_csvs/'
                    f'{newspaper_name}_enriched/{newspaper_name}_{year}_enriched.csv')
        if file.exists():
            save_data(data_path=f'/Volumes/Untitled/DHH21/export_hackathon/{year}/{newspaper_name}')
    end = timer()
    print('time elapsed:', math.ceil((end - start) / 60), 'minutes')

