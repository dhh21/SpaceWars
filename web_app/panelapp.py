import panel as pn

import plotly.graph_objs as go
import plotly.express as px
import json
import pandas as pd
from sqlalchemy import create_engine
import tempfile
from datetime import datetime
from sqlalchemy.engine.url import URL
import re
from io import StringIO

css = ['https://cdn.datatables.net/1.10.24/css/jquery.dataTables.min.css',
       # Below: Needed for export buttons
       'https://cdn.datatables.net/buttons/1.7.0/css/buttons.dataTables.min.css',
       'static/css/style.css',
       'data/ajax.txt'
]
js = {
    '$': 'https://code.jquery.com/jquery-3.5.1.js',
    'DataTable': 'https://cdn.datatables.net/1.10.24/js/jquery.dataTables.min.js',
    # Below: Needed for export buttons
    'buttons': 'https://cdn.datatables.net/buttons/1.7.0/js/dataTables.buttons.min.js',
    'jszip': 'https://cdnjs.cloudflare.com/ajax/libs/jszip/3.1.3/jszip.min.js',
    'pdfmake': 'https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.1.53/pdfmake.min.js',
    'vfsfonts': 'https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.1.53/vfs_fonts.js',
    'html5buttons': 'https://cdn.datatables.net/buttons/1.7.0/js/buttons.html5.min.js',
    # 'static/scripts/scripts.js'
}

epsg = 4326
pn.extension()
pn.extension(css_files=css, js_files=js)
pn.extension("plotly")
# pn.config.sizing_mode = "stretch_width"

def get_battle_hover_text(battles):
    """
    Prepare column of text for hover
    """

    battles['txthover'] =   battles['label'].map(str) + '<br>' \
                           + "Start: " + battles['displaystart'].map(str) + '<br>' \
                           + "End: " + battles['displayend'].map(str)  +'<br>'\
                           + "Front:" + battles['Notes'].map(str) + '<br>'\
                           + "Duration:" + battles['Duration'].map(str)
    return battles

def get_borders_hover_text(borders):
    """
    Prepare column of text for hover
    """

    borders['txthover'] =   borders['cntry_name'].map(str) + '<br>' \
                           + "English frequency: " + borders['en_freq'].map(str) + '<br>' \
                           + "French frequency: " + borders['fr_freq'].map(str) + '<br>' \
                            + "German frequency: " + borders['de_freq'].map(str) + '<br>' \
                            + "Finnish frequency: " + borders['fi_freq'].map(str) + '<br>' \
                            + "Total frequency: " + borders['total_freq'].map(str) + '<br>'
    return borders

def get_entities_hover_text(entities):
    """
    Prepare column of text for hover
    """

    entities['txthover'] = "Entity: " + entities['mention'].map(str) + '<br>' \
                           + "Year: " + entities['year'].map(str) + '<br>' \
                           + "Frequency: " + entities['freq'].map(str)  +'<br>'\
                           + "Lat:" + entities['lat'].map(str) + '<br>'\
                           + "Lon:" + entities['lon'].map(str)

    return entities

dic_lg = {
    "German": 'de',
    "Finnish": 'fi',
    "French": 'fr'
}
reversed_lg = {
    'de': "German",
    'fi': "Finnish",
    'fr': 'French'
}

# TODO: USE VALUES IN DB ?
dic_news = {
    "Arbeiter Zeitung":'arbeiter_zeitung',
    "Helsingin Sanomat": 'helsingin_sanomat',
    "Illustrierte Kronen Zeitung": 'illustrierte_kronen_zeitung',
    "Le Matin": 'le_matin',
    "L'Œuvre": 'l_oeuvre',
    # "Neue Freie Presse": 'neue_freie_presse'
}

def get_window(text, window=5, left=True):
    """
    """
    if isinstance(text, str):
        l_text = text.split()
        if not len(l_text) < window:
            if left:
                l_text = l_text[-window:]
            else:
                l_text = l_text[:window]

        return " ".join(l_text)
    else:
        return ""

def convert(row, col, text):
    """
    Converts text into a tag with href
    """
    # print(text)
    data = row[col]
    if isinstance(data, str):
        return '<a href="{}" target="_blank">{}</a>'.format(data,  text)
    else:
        return 'No link available'

with open('config.json') as f:
    db_config = json.load(f)
    db_config = URL(**db_config)

def get_countryborders():
    borderjson = json.load(open('data/borders/countryborders.geojson'))
    bordersdf = pd.read_csv('data/borders/countryborders.csv')

    bordersdf['gwsdate'] = pd.to_datetime(bordersdf['gwsdate'])
    bordersdf['gwsdate'] = bordersdf['gwsdate'].dt.strftime("%Y-%m-%d")

    bordersdf['gwedate'] = pd.to_datetime(bordersdf['gwedate'])
    bordersdf['gwedate'] = bordersdf['gwedate'].dt.strftime("%Y-%m-%d")

    return borderjson, bordersdf


# engine = create_engine('postgresql://postgres:spacewars@localhost:5432/spacewars')
engine = create_engine(db_config, echo=True)


borderjson, bordersdf = get_countryborders()

#
def execute_query(query, con):
    return con.execute(query)

def get_widget_values():
    """
    Query the database to get default values for widgets
    ie: range of dates, range of battle duration and warfronts
    ## TODO: DO THAT FOR NEWSPAPERS NAME AND LANGUAGE ?
    """
    with engine.connect() as con:
        q = 'SELECT DISTINCT "date" FROM entities;'
        dates = [x[0] for x in execute_query(q, con).all()]
        dates = [datetime.strptime(x, "%Y-%m-%d") for x in dates]
        dates = [x.date() for x in dates]
        dates.sort()
        # print(dates)

        q = 'SELECT DISTINCT "Duration" FROM battles;'
        durations = [x[0] for x in execute_query(q, con).all()]
        durations.sort()

        q = 'SELECT DISTINCT "Notes" FROM battles;'
        fronts = [x[0] for x in execute_query(q, con).all()]

        return {
            "dates": dates,
            "durations": durations,
            "fronts": fronts
        }

widget_values = get_widget_values()

lg_select = pn.widgets.MultiSelect(name= 'Language Selection',
                                   value =
                                   # ['French', 'German', 'Finnish'],
                                   # list(dic_lg.keys()),
                                   ['French'],
                                    options = list(dic_lg.keys()))

newspapers_select = pn.widgets.MultiSelect(name='Newspapers',
                                           value =
                                           # ['Arbeiter Zeitung', 'Helsingin Sanomat', 'Le Matin'],
                                           ['Le Matin'],

                                            options= list(dic_news.keys()))


# print(widget_values['dates'])
start_date = pn.widgets.DatePicker(name='Start Date',
                                   enabled_dates = widget_values['dates'],
                                   value=widget_values['dates'][0]
                                   )
end_date = pn.widgets.DatePicker(name='End Date',
                                 enabled_dates=widget_values['dates'],
                                 # todo: SET DEFAULT END VALUE TO 1915
                                 value=widget_values['dates'][100]
                                 # value=widget_values['dates'][1000]

                                 # enabled_dates = list(map_df['date'].values),
                                   )

min_duration = pn.widgets.TextInput(name='Mininum battle duration (days):', placeholder = 'Enter a value here ...',
                                value = str(widget_values['durations'][0])
                                )

max_duration = pn.widgets.TextInput(name='Maximum battle duration (days):', placeholder = 'Enter a value here ...',
                                value = str(widget_values['durations'][-1])
                                )

front_selection = pn.widgets.MultiSelect(name='Select battle front(s)',
                                     value= widget_values['fronts'],
                                     options = widget_values['fronts']
                                         )

# empty at first, display data about entity when clicked on it
## TODO: DISPLAY DATA ABOUT CAPITALS AND BATTLES AS WELL ?
# entity_display = pn.pane.Markdown("",)
# entity_display = pn.pane.HTML()


context_window = pn.widgets.TextInput(name='Window of word:', placeholder = 'Enter a value here ...',
                                value = str(5)
                                )
def read_sql_tmpfile(query, db_engine, arg=None):
    with tempfile.TemporaryFile() as tmpfile:
        conn = db_engine.raw_connection()
        cur = conn.cursor()
        # needed to escape raw SQL query
        if arg:
            query = cur.mogrify(query, arg).decode('utf-8')
            print(query)

        copy_sql = "COPY ({query}) TO STDOUT WITH CSV {head}".format(
            query=query, head="HEADER"
        )
        cur.copy_expert(copy_sql, tmpfile)
        tmpfile.seek(0)
        df = pd.read_csv(tmpfile)
        return df

def get_battle_df(start_date, end_date, min_duration, max_duration, front_selection):
    """
     Collect the data from the database according the values of
    the widgets
    """
    start_date = str(start_date.value)
    end_date = str(end_date.value)
    min_duration = str(min_duration.value)
    max_duration = str(max_duration.value)
    front = tuple([f"{x}" for x in front_selection.value])

    args = (start_date, end_date, min_duration, max_duration, front)
    q = '''SELECT * from battles
    WHERE "displaydate" BETWEEN %s AND %s
    AND "Duration" BETWEEN %s AND %s
    AND "Notes" IN %s
    '''
    df_battles = read_sql_tmpfile(q, engine, args)
    df_battles = get_battle_hover_text(df_battles)
    return df_battles

def filter_country_borders(start_date, end_date, list_country):
    """
     Collect the data from the database according the values of
    the widgets
    """
    start_date = str(start_date.value)
    end_date = str(end_date.value)

    filtered_borders = bordersdf[
        (bordersdf['gwsdate'] <= end_date)
    ]

    filtered_borders = filtered_borders[
        filtered_borders['cntry_name'].isin(list_country)
    ]
    return filtered_borders
    # return bordersdf[bordersdf['cntry_name'] == 'France']


def get_map_df(lg, newspaper, start_date, end_date, context_window):
    """
    Collect the data from the database according the values of
    the widgets
    """
    lg = [f"{dic_lg[x]}" for x in lg.value]
    lg = tuple(lg)
    newspaper = tuple([f"{x}" for x in newspaper.value])

    start_date = str(start_date.value)
    end_date = str(end_date.value)

    args = ( start_date, end_date, lg, newspaper)
    q = '''select ent.geometry, ent.mention, ent.lon, ent.lat
        from entities2 as ent
        WHERE ent.index IN (
            select ent.index
            from entities2 as ent
            INNER JOIN entities_date
            ON ent.index = entities_date.id_geo
            INNER JOIN dates
            ON entities_date.id_date = dates.index
            WHERE dates.date BETWEEN %s AND %s
        )
        AND ent.index IN (
            select ent.index
            from entities2 as ent
            INNER JOIN entities_newspapers
            ON ent.index = entities_newspapers.id_geo
            INNER JOIN newspapers
            ON entities_newspapers.id_newspaper = newspapers.index
            WHERE newspapers.lang IN %s
            AND newspapers.newspaper IN %s        )
            '''
    # ent_context =

    args = (lg, newspaper, start_date, end_date)
    q = '''SELECT * from entities
    WHERE "lang" IN %s
    AND "newspaper" IN %s
    AND "date" BETWEEN %s AND %s
    '''
    map_df = read_sql_tmpfile(q, engine, args)

    map_df['date'] = pd.to_datetime(map_df['date'], format="%Y-%m-%d")
    # map_df['anim_date'] = map_df['date'].dt.strftime('%B-%Y')
    map_df['year'] = pd.DatetimeIndex(map_df['date']).year
    map_df['year'] = map_df['year'].astype(str)
    map_df['freq'] = map_df['geometry'].map(map_df['geometry'].value_counts())
    context_window = int(context_window.value)
    map_df['article_link'] = map_df.apply(convert, args=('article_link', 'View Article'), axis=1)
    map_df['wikidata_link'] = map_df.apply(convert, args=('wikidata_link', 'View Wikidata'), axis=1)

    # geo_df['date'] = pd.DatetimeIndex(geo_df['date']).strftime("%Y-%m-%d")
    map_df['context_word_window'] = context_window
    map_df['window_left_context'] = map_df['left_context'].apply(lambda x: get_window(x, context_window))
    map_df['window_right_context'] = map_df['right_context'].apply(lambda x: get_window(x, context_window, left=False))
    map_df['lang'] = map_df['lang'].apply(lambda x: reversed_lg[x])
    map_df = get_entities_hover_text(map_df)

    return map_df

def get_country_freq(map_df, borders_df):
    """

    Calculates the frequency of each country's name
    across languages in the selected dataset
    """

    borders_df['en_freq'] = borders_df['en_cntry_name'].map(map_df['mention'].value_counts()).fillna(0)
    borders_df['fr_freq'] = borders_df['fr_cntry_name'].map(map_df['mention'].value_counts()).fillna(0)
    borders_df['de_freq'] = borders_df['de_cntry_name'].map(map_df['mention'].value_counts()).fillna(0)
    borders_df['fi_freq'] = borders_df['fi_cntry_name'].map(map_df['mention'].value_counts()).fillna(0)
    borders_df['total_freq'] = borders_df['en_freq'] + borders_df['fr_freq'] + borders_df['de_freq'] + borders_df['fi_freq']

    return borders_df

token = open(".mapbox_token").read() # you will need your own token

def get_map_plot():

    map_df = get_map_df(lg_select, newspapers_select, start_date, end_date, context_window)
    df_battles = get_battle_df(start_date, end_date, min_duration, max_duration, front_selection)
    bordersdf = filter_country_borders(start_date, end_date, map_df['mention'].unique())

    bordersdf = get_country_freq(map_df, bordersdf)
    bordersdf = get_borders_hover_text(bordersdf)
    bordersdf = bordersdf.groupby('cntry_name')
    bordersdf = bordersdf.first().reset_index()
    bordersdf.rename(columns={'index':'cntry_name'}, inplace=True)

    df_page = map_df[['window_left_context', 'mention', 'window_right_context']]

    groupby_data = map_df.groupby('geometry')
    grp_map_df = groupby_data.first()
    grp_map_df = grp_map_df.reset_index()

    bordersdf['zero'] = 0
    fig = go.Figure()

    fig.add_scattermapbox(
            lat=bordersdf['caplat'],
            lon=bordersdf['caplong'],
            mode='markers',
            hovertext = bordersdf['capname'],
            # marker_symbol = 'hexagon',
            marker=go.scattermapbox.Marker(
                size = 15
            ),
            hoverinfo='text'
        )

    fig['data'][0]['name'] = 'Capitals'

    fig.add_scattermapbox(
            lat=grp_map_df['lat'],
            lon=grp_map_df['lon'],
            mode='markers',
            hovertext = grp_map_df['txthover'],
            marker=go.scattermapbox.Marker(
                size=grp_map_df['freq'],
                sizemin = grp_map_df['freq'].min() * 2,
                sizemode='area',
                sizeref=grp_map_df['freq'].max() / 15 ** 2

            ),
            hoverinfo='text'
        )
    fig['data'][1]['showlegend']=True
    fig['data'][1]['name']='Named Entity frequencies'
    fig['data'][1]['legendgroup']= 'Frequencies'

    fig.add_scattermapbox(
            lat=df_battles['lat'],
            lon=df_battles['lon'],
            mode='markers',
            hovertext = df_battles['txthover'],
            # marker_symbol = 'star-stroked',
            marker=go.scattermapbox.Marker(
                size=15,
                # color='rgb(255, 0, 0)',
                color= df_battles['Duration'],
                showscale = True,
                colorscale='Blackbody_r',
                opacity=0.7
            ),
            hoverinfo='text'
        )

    fig['data'][2]['name'] = 'Battles'

    fig.update_layout(
        autosize=True,
        hovermode='closest',
        legend=dict(
            bgcolor='ivory',
            bordercolor='lightgray',
            borderwidth=1,
            font = dict(color='black'),
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        mapbox_accesstoken=token,
        mapbox={
            'style': 'mapbox://styles/gutyh/ckqwa99n501hx17qocmwr03ei',
            'center': {'lon': 2.2137, 'lat': 46.2276},
            'zoom': 3,
            # 'layers': [{
            #     'source':
            #     borderjson,
            #
            #     'type': "fill", 'below': "traces", 'color': "royalblue"}]
        },
        margin={'l': 0, 'r': 0, 'b': 0, 't': 0},
        updatemenus=[
            dict(
                type='buttons',
                active=0,
                buttons=[
                    dict(label='Clear annotations',
                         method='update',
                         args=[
                             {'visible':[True, True, False, False]},
                             {'annotations':[]}
                         ]
                         # args=['annotations', []]
                         )
                ],
                xanchor='left',
                yanchor='top',
                x=0,
                y=1.05
            )
        ]

    )
    #
    # fig.add_choroplethmapbox(
    #     bordersdf,
    #     geojson=borderjson,
    #     featureidkey='properties.cntry_name',
    #     locationmode='geojson-id',
    #     # geojson=borderjson,
    #     locations='cntry_name',
    #     # featureidkey='properties.cntry_name',
    #     # color='cntry_name',
    #     # color_continuous_scale="Viridis",
    # )


    # print(borderjson['objects']['countryborders'].keys())
    # fig.add_choropleth(
    #     geojson=borderjson,
    #     featureidkey='properties.cntry_name',
    #     locationmode='geojson-id',
    #     locations=bordersdf['cntry_name'],
    #     hovertext=bordersdf['txthover'],
    #     hoverinfo='text',
    #     # z=bordersdf['zero'],
    #     z = bordersdf['total_freq'],
    #     showscale=False
    # )


    return fig, map_df, grp_map_df, df_page

def update_entities_plot(event):
    new_map_df = get_map_df(lg_select, newspapers_select, start_date, end_date, context_window)

    ## updates map_df to new values
    map_df.loc[:,:] = new_map_df

    groupby_data = new_map_df.groupby('geometry')
    new_grp_map_df = groupby_data.first()
    new_grp_map_df = new_grp_map_df.reset_index()
    grp_map_df.iloc[:, :] = new_grp_map_df

    # todo: CHANGER INDEX QUAND LES AUTRES MAPS SERONT AJOUTEES
    entities = warmap['data'][1]
    entities['lat'] = grp_map_df['lat']
    entities['lon'] = grp_map_df['lon']
    entities['hovertext'] = grp_map_df['txthover']
    entities['marker']['size'] = grp_map_df['freq']

    # new_df_page = new_df.reset_index()
    new_df_page = new_map_df[['window_left_context', 'mention', 'window_right_context']]
    df_page.iloc[:,:] = new_df_page
    table.value = new_df_page

    freq_input_value = freq_input.value.replace(' ', '')
    if freq_input_value[-1] == ',':
        freq_input_value = freq_input_value[:-1]
    list_keywords = freq_input_value.split(',')

    df_freq = map_df.groupby(['mention', x_axis_select.value]).size().reset_index(name='frequency')
    df_freq = df_freq[df_freq['mention'].isin(list_keywords)]
    if x_axis_select.value != 'date':
        new_freq_fig = px.bar(df_freq, x=x_axis_select.value, y='frequency', color='mention', barmode='group')
    else:
        new_freq_fig = px.area(df_freq, x=x_axis_select.value, y='frequency', color='mention', line_group='mention')
    freqplot.object = new_freq_fig

def update_frequency_plot(event):
    new_df = map_df[
        (map_df['freq'] >= int(min_freq.value))
        & (map_df['freq'] <= int(max_freq.value))
    ]
    groupby_data = new_df.groupby('geometry')
    new_grp_map_df = groupby_data.first()
    new_grp_map_df = new_grp_map_df.reset_index()
    grp_map_df.iloc[:, :] = new_grp_map_df


    entities = warmap['data'][1]
    entities['lat'] = grp_map_df['lat']
    entities['lon'] = grp_map_df['lon']
    entities['hovertext'] = grp_map_df['txthover']
    entities['marker']['size'] = grp_map_df['freq']

    new_df_page = new_df[['window_left_context', 'mention', 'window_right_context']]
    df_page.iloc[:,:] = new_df_page
    table.value = new_df_page

    freq_input_value = freq_input.value.replace(' ', '')
    if freq_input_value[-1] == ',':
        freq_input_value = freq_input_value[:-1]
    list_keywords = freq_input_value.split(',')

    df_freq = map_df.groupby(['mention', x_axis_select.value]).size().reset_index(name='frequency')
    df_freq = df_freq[df_freq['mention'].isin(list_keywords)]
    if x_axis_select.value != 'date':
        new_freq_fig = px.bar(df_freq, x=x_axis_select.value, y='frequency', color='mention', barmode='group')
    else:
        new_freq_fig = px.area(df_freq, x=x_axis_select.value, y='frequency', color='mention', line_group='mention')
    freqplot.object = new_freq_fig


def update_battle_plot(event):

    df_battles = get_battle_df(start_date, end_date, min_duration, max_duration, front_selection)
    battle_map = warmap['data'][3]
    battle_map['lat'] = df_battles['lat']
    battle_map['lon'] = df_battles['lon']
    battle_map['txthover'] = df_battles['txthover']
    battle_map['marker']['size'] = df_battles['Duration']


# TODO: IF CAN BORDERS BY BACKGROUND IMAGE
# TODO: COUNTRY FREQUENCIES WHILE UPDATING
def update_country_borders(event):
    """

    """
    bordersdf = filter_country_borders(start_date, end_date)
    bordersmap = warmap['data'][0]
    bordersmap['locations'] = bordersdf['cntry_name']
    bordersmap['hovertext'] = bordersdf['txthover']
    bordersmap['z'] = bordersdf['total_freq']
    #
    # z = bordersdf['total_freq'],
    #
    # # bordersmap['location'] = bordersdf['location']
    # # print("BORDERS:", bordersmap.keys())
    #
    # entities['lat'] = grp_map_df['lat']
    # entities['lon'] = grp_map_df['lon']
    # entities['hovertext'] = grp_map_df['txthover']
    # entities['marker']['size'] = grp_map_df['freq']

def update_context_window(event):
    """

    """

    new_window = int(context_window.value)

    new_df = map_df[['left_context', 'mention', 'right_context']]

    new_df['context_word_window'] = new_window
    new_df['window_left_context'] = map_df['left_context'].apply(lambda x: get_window(x, new_window))
    new_df['window_right_context'] = map_df['right_context'].apply(lambda x: get_window(x, new_window, left=False))
    df_page.iloc[:]['window_left_context'] = new_df['window_left_context']
    df_page.iloc[:]['window_right_context'] = new_df['window_right_context']
    # table.stream(df_page, follow=False)
    table.value = df_page

def search_entity(event):
    """
    Search exact entity in column
    """

    pattern = search_bar.value
    if case_checkbox.value:
        pattern = re.compile(f"{pattern}", re.IGNORECASE)
    new_search_df = df_page[df_page['mention'].str.contains(pattern)]

    table.value = new_search_df
    table.value = table.value.dropna()


def clear_concordancer(event):
    """
    Clear selection in concordancer and returns full data
    """

    search_bar.value = ''
    # entity_display.object = ''
    table.value = df_page

warmap, map_df, grp_map_df, df_page = get_map_plot()
min_freq = pn.widgets.TextInput(name='Mininum entity occurrence:', placeholder = 'Enter a value here ...',
                                value = '100'
                                )
max_freq = pn.widgets.TextInput(name='Maximum entity occurrence:', placeholder = 'Enter a value here ...',
                                value = map_df['freq'].max().astype('str')
                                )

# adding callbacks to update entities points and table
lg_select.param.watch(update_entities_plot, 'value')
newspapers_select.param.watch(update_entities_plot, 'value')
start_date.param.watch(update_entities_plot, 'value')
end_date.param.watch(update_entities_plot, 'value')

# adding callbacks to update battle points
min_duration.param.watch(update_battle_plot, 'value')
max_duration.param.watch(update_battle_plot, 'value')
start_date.param.watch(update_battle_plot, 'value')
end_date.param.watch(update_battle_plot, 'value')
front_selection.param.watch(update_battle_plot, 'value')

# adding callbacks to update country borders
start_date.param.watch(update_country_borders, 'value')
end_date.param.watch(update_country_borders, 'value')

# adding callbacks to update context window
context_window.param.watch(update_context_window, 'value')

# adding callbacks to update frequencies on plot
min_freq.param.watch(update_frequency_plot, 'value')
max_freq.param.watch(update_frequency_plot, 'value')


search_bar = pn.widgets.TextInput(name='Search:')
search_bar.param.watch(search_entity, 'value')

clear_button = pn.widgets.Button(name='Clear concordancer', button_type='primary')
clear_button.param.watch(clear_concordancer, 'value')

case_checkbox = pn.widgets.Checkbox(name='Case insensitive search')


setting_col = pn.WidgetBox('### Options',
            lg_select, newspapers_select,
              start_date, end_date,
              min_freq, max_freq,
            min_duration, max_duration,
            front_selection,
           search_bar)

setting_row = pn.Row('### Options',
            pn.Column(lg_select, newspapers_select),
            pn.Column(start_date, end_date, min_freq, max_freq),
            pn.Column(front_selection, min_duration, max_duration),
            pn.Column(context_window, search_bar, clear_button, case_checkbox),
            # entity_display,
            )

plot_config = {
    # 'topojsonURL':'http://127.0.0.1:5000/data/',
    "responsive": True,
    "displaylogo": False,
    "displayModeBar": True,
    'toImageButtonOptions': {'height': None, 'width': None, },
    ## TODO: ADD DRAWING TOOLS BUT DOESNT SEEM TO WORK ON MAPS

}

map_panel = pn.pane.Plotly(warmap,
                           config=plot_config,
                           )

@pn.depends(map_panel.param.click_data, watch=True)
def update_on_click(click_data):
    point = click_data['points'][0]
    print(point)
    pointindex = point['pointIndex']
    entity_data = grp_map_df.iloc[pointindex]


    md_template = f"""     <b>Entity</b>: {entity_data['mention']}<br>
    <b>Newspaper</b>: {entity_data['newspaper']}<br>
    <b>Language</b>: {entity_data['lang']}<br>
    <b>Date</b>: {entity_data['date'].strftime("%d %B %Y")}<br>
    <b>NewsEye link</b>: {entity_data['article_link']}<br>
    <b>Wikidata link</b>: {entity_data['wikidata_link']}<br>
    <b>Latittude - Longitude</b>: {entity_data['lat']} {entity_data['lon']}<br>"""

    #clears previous annotations
    warmap['layout']['annotations'] = ()

    warmap.add_annotation(
        text = md_template,
        yanchor="top",
        y=0.85,
        xanchor="left",
        x=0.01,
        align='left',
        showarrow=True,
        bgcolor = 'ivory',
        bordercolor = 'lightgray',
        borderwidth = 1,
        font = dict(color='black'),

    )


    # search_bar.value = entity_data['mention']

def update_table(df, pattern):

    return df


table = pn.widgets.Tabulator(df_page, layout='fit_data_table', selectable='checkbox',
                             pagination='remote', page_size=10,
                             configuration={'responsiveLayout': 'hide'}
                             )

def download_as_csv():
    sio = StringIO()
    table.value.to_csv(sio)
    sio.seek(0)
    return sio

csv_download = pn.widgets.FileDownload(callback=download_as_csv, filename='concordancer.csv',
                                       button_type='success', name='Download concordancer to CSV')

def download_as_xlsx():
    sio = StringIO()
    table.value.to_excel(sio)
    sio.seek(0)
    return sio

xlsx_download = pn.widgets.FileDownload(callback=download_as_xlsx, filename='concordancer.xlsx',
                                       button_type='success', name='Download concordancer to Excel')

def download_as_json():
    sio = StringIO()
    json_table = table.value.to_json()
    json.dump(json_table, sio)
    sio.seek(0)
    return sio

json_download = pn.widgets.FileDownload(callback=download_as_json, filename='concordancer.json',
                                       button_type='primary', name='Download concordancer to JSON')


table.add_filter(pn.bind(update_table, pattern=lg_select))
table.add_filter(pn.bind(update_table, pattern=newspapers_select))
table.add_filter(pn.bind(update_table, pattern=start_date))
table.add_filter(pn.bind(update_table, pattern=end_date))
table.add_filter(pn.bind(update_table, pattern=min_freq))
table.add_filter(pn.bind(update_table, pattern=max_freq))
table.add_filter(pn.bind(update_table, pattern=context_window))
table.add_filter(pn.bind(update_table, pattern=search_bar))
table.add_filter(pn.bind(update_table, pattern=clear_button))


def update_freq_plot(event):
    """
    Updates entities frequency plot
    """
    freq_input_value = freq_input.value.replace(' ', '')
    if freq_input_value[-1] == ',':
        freq_input_value = freq_input_value[:-1]
    list_keywords = freq_input_value.split(',')

    df_freq = map_df.groupby(['mention', x_axis_select.value]).size().reset_index(name='frequency')
    df_freq = df_freq[df_freq['mention'].isin(list_keywords)]
    if x_axis_select.value != 'date':
        new_freq_fig = px.bar(df_freq, x=x_axis_select.value, y='frequency', color='mention', barmode='group')
    else:
        new_freq_fig = px.area(df_freq, x=x_axis_select.value, y='frequency', color='mention', line_group='mention')
    freqplot.object = new_freq_fig


freq_input = pn.widgets.TextInput(name = 'Keyword(s):', value='France,Deutschland,Suomi')

x_axis_select = pn.widgets.Select(name='Select', options=['date', 'newspaper', 'lang'], value='date')

freq_button = pn.widgets.Button(name= 'Search')

freq_button.param.watch(update_freq_plot, 'value')

freq_input_value = freq_input.value.replace(' ', '')
if freq_input_value[-1] == ',':
    freq_input_value = freq_input_value[:-1]
list_keywords = freq_input_value.split(',')

df_freq = map_df.groupby(['mention', x_axis_select.value]).size().reset_index(name='frequency')
df_freq = df_freq[df_freq['mention'].isin(list_keywords)]

freq_fig = px.area(df_freq, x=x_axis_select.value, y='frequency', color='mention', line_group='mention')

freqplot = pn.pane.Plotly(freq_fig)

row_concordancer = pn.Row(table, pn.Column(csv_download, xlsx_download, json_download))
row_freq = pn.Row(freqplot, pn.Column(freq_input, x_axis_select, freq_button))

tabs = pn.Tabs(
    ('Warmap', map_panel),
    ('Concordancer', pn.Row(pn.Column(table, freqplot), pn.Column(csv_download, xlsx_download, json_download,
                                                                  freq_input,
                                                                  x_axis_select,
                                                                  freq_button) )),
    # tabs_location='left',
    # dynamic=True
)



# template = """
#
# {% extends base %}
#
# {% block contents %}
#
# {{ app_title }}
#
# <div id="mySidebar" class="sidebar">
#     <a href="javascript:void(0)" class="closebtn" onclick="closeNav()">&times;</a>
#     {{ embed(roots.setting_col)}}
# </div>
#
# <button class="openbtn" onclick="openNav()">&#9776; Open Sidebar</button>
# {{ embed(roots.setting_row)}}
#
# {{ embed(roots.tabs)}}
#
#
# <script>
# /* Set the width of the sidebar to 250px and the left margin of the page content to 250px */
# function openNav() {
#   document.getElementById("mySidebar").style.width = "25em";
#   document.getElementById("main").style.marginLeft = "25em";
# }
#
# /* Set the width of the sidebar to 0 and the left margin of the page content to 0 */
# function closeNav() {
#   document.getElementById("mySidebar").style.width = "0";
#   document.getElementById("main").style.marginLeft = "0";
# }
#
# </script>
# {% endblock %}
# """

template = """

{% extends base %}

{% block postamble %}
<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css">
{% endblock %}

{% block contents %}


<div class="fixed_div">
    <button class="headernav"">SpaceWars</button>
    <button class="tablink" onclick="openPage('Warmap', this, 'red')" id="defaultOpen">Warmap</button>
    <button class="tablink" onclick="openPage('Concordancer', this, 'green')">Concordancer</button>
    <button class="tablink" onclick="openPage('Metadata', this, 'blue')">Metadata</button>
    <button class="tablink" onclick="openPage('Tutorial', this, 'orange')">Tutorial</button>
    <button class="tablink" onclick="openPage('Data', this, 'orange')">Data</button>

</div>
<div id="mySidebar" class="sidebar">
    <a href="javascript:void(0)" class="closebtn" onclick="closeNav()">&times;</a>
    {{ embed(roots.setting_col)}}
</div>
<button class="openbtn" onclick="openNav()">&#9776; Open Sidebar</button>
<div id="Warmap" class="tabcontent">

    {{ embed(roots.warmap)}}

</div>

<div id="Concordancer" class="tabcontent">

 <div class="row">
  <div class="table_col">
        {{ embed(roots.row_table)}}
  
  </div>
  <div class="column">
        {{ embed(roots.row_freq)}}
  
  </div>
</div> 

<div class="container-fluid">
  <div class="row">
    <div class="col-lg-7">
        {{ embed(roots.row_table)}}
    </div>
    <div class="col-lg-5">
        {{ embed(roots.row_freq)}}
    </div>
  </div>
</div>


</div>

<div id="Metadata" class="tabcontent">
  <h3>Metadata</h3>
  <p>Get in touch, or swing by for a cup of coffee.</p>
</div>

<div id="Tutorial" class="tabcontent">
ADD VIDEOS 
</div>

<div id="Data" class="tabcontent">
        {{ embed(roots.settings)}}
</div> 


<script>
/* Set the width of the sidebar to 250px and the left margin of the page content to 250px */
function openNav() {
  document.getElementById("mySidebar").style.width = "25em";
  document.getElementById("main").style.marginLeft = "25em";
}

/* Set the width of the sidebar to 0 and the left margin of the page content to 0 */
function closeNav() {
  document.getElementById("mySidebar").style.width = "0";
  document.getElementById("main").style.marginLeft = "0";
}

function openPage(pageName, elmnt, color) {
  // Hide all elements with class="tabcontent" by default */
  var i, tabcontent, tablinks;
  tabcontent = document.getElementsByClassName("tabcontent");
  for (i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }

  // Remove the background color of all tablinks/buttons
  tablinks = document.getElementsByClassName("tablink");
  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].style.backgroundColor = "";
  }

  // Show the specific tab content
  document.getElementById(pageName).style.display = "block";


}

// Get the element with id="defaultOpen" and click on it
document.getElementById("defaultOpen").click(); 


</script>
{% endblock %}
"""
# {{ embed(roots.tabs)}}

tmpl = pn.Template(template)
# tmpl.add_variable('app_title', '<h1>SpaceWars</h1>')
tmpl.add_panel('warmap', map_panel)
tmpl.add_panel('row_table', table)
tmpl.add_panel('row_freq', freqplot)

# tmpl.add_panel('row_table', row_concordancer)
# tmpl.add_panel('row_freq', row_freq)
# tmpl.add_panel('entities', entity_display)


# tmpl.add_panel('tabs', tabs)
tmpl.add_panel('setting_col', setting_col)
tmpl.add_panel('settings', setting_row)
tmpl.servable()



# df_freq = map_df[['mention', 'date']]
# df_freq['year-month'] = pd.to_datetime(df_freq['date']).dt.to_period('M')
# df_freq = df_freq.groupby(['mention', 'date']).size().reset_index(name='frequency')
# # df_freq['timefreq'] = df_freq['mention'].map(map_df['mention'].value_counts()).fillna(0)
# print(df_freq)
# fig = px.area(df_freq[df_freq['mention'] == 'France'], x='date', y='frequency', color='mention', line_group='mention')
# timeplot = pn.pane.Plotly(fig)
# timeplot.servable()

# pn.Row(
#     start_date,
#     end_date,
#     map_panel
# ).servable()

# pn.Tabs(
#     ('test', table),
#     tabs_location='left'
#
# ).servable()
# tabs.servable()
# with open('test.html', 'w') as f:
#     f.write(div)
# print(plotly.io.to_html(warmap, full_html=False, include_plotlyjs=False))

# print(type(div))

# template = """
# {% extends base %}
#
# <!-- goes in body -->
# {% block postamble %}
# <!-- CSS only -->
# <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">
#
# {% endblock %}
#
# <!-- goes in body -->
# {% block contents %}
# {{ app_title }}""" + div + """
# {% endblock %}
# """


# tmpl.add_panel('A', div)
# tmpl.add_panel('A', pn.pane.Plotly(warmap, config={"responsive": True, 'displayModeBar': False}))
# tmpl.add_panel('B', table)
# tmpl.servable()

# from jinja2 import Environment, FileSystemLoader
#
# env = Environment(loader=FileSystemLoader('.'))
# jinja = env.get_template('base.html')

# tmpl = pn.Template(jinja)


# tmpl.add_variable('app_title', '<h1>Custom Template App</h1>')
# tmpl.add_variable('map', div)

# tmpl.servable()
# ## TODO: MAKE SURE DATE ARE IN ORDER FOR THE SLIDER TO GO PROPERLY
# player = pn.widgets.DiscretePlayer(name='ANIMATION SLIDER', options=list(map_df.iloc[:15]['date'].values))
# # print(int(map_df['index'].min()), int(map_df['index'].max()))
# print(list(map_df.iloc[:15]['date'].values))
#
# @pn.depends(frame = player.param.value)
# def timeslider(frame):
#     print("Player", frame)
#     warmap.synchronize()
#
# def callback_clear_display(target, event):
#     target.object = ''
#     html = df_page.to_html(classes=['example', 'panel-df']) + script
#     table.object = html
#
#
# clear_button = pn.widgets.Button(name='Clear selection', button_type='primary')
# clear_button.link(entity_display, callbacks={'value': callback_clear_display})
#
#
# template = pn.template.MaterialTemplate(title='WEBAPP')
# for widget in [lg_select, newspapers_select, year_select,
#               start_date, end_date,
#               min_freq, max_freq,
#               battle_duration, front_selection]:
#     template.sidebar.append(widget)
#
# template.main.append(
#     pn.Row(
#         pn.Column(
#             warmap,
#             player,
#             table
#         ),
#         pn.Column(
#             clear_button,
#             entity_display
#         )
#     )
# )
# template.servable()

# row = pn.Row(
#     pn.Column(pn.pane.Markdown('### Options'),
#             lg_select, newspapers_select, year_select,
#               start_date, end_date,
#               min_freq, max_freq,
#               battle_duration, front_selection),
#     pn.Column(pn.pane.Markdown('#WEBAPP TITLE'),
#         pn.pane.Markdown('## War Map'),
#         warmap,
#               table),
#     entity_display
#
#
# )
# row.servable()
## TODO: USE GRID SPEC // BOOTSTRAP TO LAYOUT EVERYTHING AND MAKE IT RESPONSIVE

# fig = px.scatter_geo(map_df, lat='lat', lon='lon', #data and col. to use for plotting
#                         hover_name = 'mention',
#                         hover_data = ['txthover'],
#                           size = 'freq', # sets the size of each points on the values in the frequencies col.
#                         animation_frame = 'anim_date',
#                         # center = dict(lat=53, lon=16), #centers the map on specific coordinates
#                         # zoom = 3, # zooms on these coordinates
#                         width=1000, height=700, # width and height of the plot
#                         )
# fig = px.choropleth(filtered_borders, geojson=filtered_borders['geometry'],
#                     locations=filtered_borders.index,
#                     color=filtered_borders.index,
#                     width=1000, height=700, # width and height of the plot
#
#                     )