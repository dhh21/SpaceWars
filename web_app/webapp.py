import pandas as pd
import streamlit as st
import geopandas as gpd
import plotly.graph_objs as go
import plotly.express as px
import numpy as np
from shapely import wkt
# import contextily as ctx
from glob import glob
from datetime import datetime

epsg = 4326

def get_battle_hover_text(battles):
    """
    Prepare column of text for hover
    """
 #   subject, label, coordinates, LOClabel, location, country, displaydate, displaystart, displayend, Duration, Notes
 #    list_hover = []
 #    for index, line in battles.iterrows():
 #        label = line['label']
 #        start, end = line['displaystart'], line['displayend']
 #        duration = line['Duration']
 #        front = line['Notes']
 #        txt = f"{label}<br>{start} - {end}<br>Duration (days): {duration}<br>Warfront : {front}"
 #        list_hover.append(txt)
 #    battles['txthover'] = list_hover
    battles['txthover'] =   battles['label'].map(str) + '<br>' \
                           + "Start: " + battles['displaystart'].map(str) + '<br>' \
                           + "End: " + battles['displayend'].map(str)  +'<br>'\
                           + "Front:" + battles['Notes'].map(str) + '<br>'\
                           + "Duration:" + battles['Duration'].map(str)
    return battles

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

@st.cache(allow_output_mutation=True)
def prepare_dataset(geodf):
    """
    Adds a lat and a lon column to the GeoDF to be used
    with the mapping
    """
    geodf = geodf.dropna()
    list_lat, list_long = [], []
    for point in geodf['geometry']:
        lat = point.centroid.y
        long = point.centroid.x
        list_lat.append(lat)
        list_long.append(long)
    geodf['lat'] = list_lat
    geodf['lon'] = list_long
    return geodf

@st.cache(allow_output_mutation=True)
def open_file(filepath):
    """
    If filepath direct ot GeoJSON file, just opens and reads it
    If its a CSV file, opens it and converts it to GeoJSON. The CSV
    needs to have a least a geometry column with Point(x,y) as values
    """
    if filepath.endswith('csv'):
        df = pd.read_csv(filepath)
        for col in df.columns:
            if col.startswith('Unnamed'):
                del df[col]
        df['date'] = pd.to_datetime(df['date'], format="%Y-%m-%d")
        df['year'] = pd.DatetimeIndex(df['date']).year
        df['year'] = df['year'].astype(str)

        # geo_df = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)
        crs = {'init': f'epsg:{epsg}'}  # http://www.spatialreference.org/ref/epsg/2263/
        geo_df = gpd.GeoDataFrame(df, crs=crs)

    else:
        geo_df = gpd.read_file(filepath)
        geo_df.set_crs(epsg=epsg)

    return geo_df

def open_borders(filepath):
    """

    """
    # df = pd.read_csv(filepath)
    df = gpd.read_file(filepath)
    # print(df)
    df['gwsdate'] = pd.to_datetime(df['gwsdate']).dt.date
    df['gwedate'] = pd.to_datetime(df['gwedate']).dt.date
    df['gwsdate'] = pd.to_datetime(df['gwsdate'], format="%Y-%m-%d")
    df['gwedate'] = pd.to_datetime(df['gwedate'], format="%Y-%m-%d")
    return df

@st.cache(allow_output_mutation=True)
def open_battle_file(filepath):
    """
    Specific function to open DataFrame containing battle related data
    """
    df = pd.read_csv(filepath)
    for col in df.columns:
        if col.startswith('Unnamed'):
            del df[col]
    df['displaydate'] = pd.to_datetime(df['displaydate'], format="%Y-%m-%d")
    df['displaystart'] = pd.to_datetime(df['displaystart'], format="%Y-%m-%d")
    df['displayend'] = pd.to_datetime(df['displayend'], format="%Y-%m-%d")
    df['year'] = pd.DatetimeIndex(df['displaydate']).year
    df['year'] = df['year'].astype(str)

    df['coordinates'] = df['coordinates'].str.replace('\(\(', '(')
    df['coordinates'] = df['coordinates'].str.replace('\)\)', ')')

    ## "entity" in the URL is automatically converted to "wiki" when searching the URL in a browser
    ## like in the wikidata links from NewsEye
    ## I'll just change the URL so they can both match
    df['subject'] = df['subject'].str.replace('entity', 'wiki')
    df['location'] = df['location'].str.replace('entity', 'wiki')
    df['is_in_radius'] = False

    geometry = []
    for x in df['coordinates']:
        if isinstance(x, str):
            geometry.append(wkt.loads(x))
        else:
            geometry.append(None)
    # 2263
    crs = {'init': f'epsg:{epsg}'}  # http://www.spatialreference.org/ref/epsg/2263/
    geo_df = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)
    del geo_df['coordinates']
    return geo_df

battles = open_battle_file('data/Wikibattles.csv')
battles = prepare_dataset(battles)
battles = get_battle_hover_text(battles)

# DATASET_PATH = 'data/combined_data_csvs'
DATASET_PATH = 'data/DATASET'
all_files = glob(f'{DATASET_PATH}/**/*.csv', recursive=True)
## Preparing the data
# geo_df = prepare_dataset(geo_df)

## Layout
st.title('DHH21 Space Wars')

dic_lg = {
    "German": 'de',
    "Finnish": 'fi',
    "French": 'fr'
}

st.sidebar.title('Options')
lg_select = st.sidebar.multiselect('Select language(s):',
                                   # ['de', 'fi', 'fr'],
                                   #  ['de', 'fi', 'fr']
                                    list(dic_lg.keys()),
                                   list(dic_lg.keys())

                                   )


dic_news = {
    "Arbeiter Zeitung":'arbeiter_zeitung',
    "Helsingin Sanomat": 'helsingin_sanomat',
    "Illustrierte Kronen Zeitung": 'illustrierte_kronen_zeitung',
    "Le Matin": 'le_matin',
    "L'Oeuvre": 'l_oeuvre',
    # "Neue Freie Presse": 'neue_freie_presse'
}
## TODO: Make sure that if we select fr, only the French newspapers appear, and vice-versa
newspapers_select = st.sidebar.multiselect('Select newspaper(s):',
                                         # ['arbeiter_zeitung', 'helsingin_sanomat', 'illustrierte_kronen_zeitung', 'le_matin', 'l_oeuvre', 'neue_freie_presse'],
                                         # ['arbeiter_zeitung', 'helsingin_sanomat', 'le_matin', ],
                                           list(dic_news.keys()),
                                           ['Arbeiter Zeitung', 'Helsingin Sanomat', 'Le Matin']
                                           # list(dic_news.keys())

                                         )

year_select = st.sidebar.multiselect('Select year(s):',
                                         ['1913', '1914', '1915', '1916', '1917', '1918', '1919', '1920'],
                                         ['1914', '1915', '1916', '1917', '1918'],

                                         )

@st.cache
def filter_files(all_files):
    filter1 = []
    for lge in [dic_lg[lg] for lg in lg_select]:
        for file in all_files:
            if lge in file:
                filter1.append(file)

    filter2 = []
    for news in [dic_news[news] for news in newspapers_select]:
        for file in filter1:
            if news in file:
                filter2.append(file)

    filter3 = []
    for year in year_select:
        for file in filter2:
            if year in file:
                filter3.append(file)

    return filter3

filtered_files = filter_files(all_files)

l_df = []
for file in filtered_files:
    df = open_file(file)
    l_df.append(df)
geo_df = pd.concat(l_df).reset_index()
geo_df = get_entities_hover_text(geo_df)

# print(geo_df)
start_date = st.sidebar.date_input('Start date', geo_df['date'].min(),
                           # min_value = geo_df['date'].iloc[0],
                           # max_value = geo_df['date'].iloc[-1]
                                   min_value=geo_df['date'].min(),
                                   max_value=geo_df['date'].max()
                                   )

end_date = st.sidebar.date_input('End date', geo_df['date'].max(),
                           min_value = geo_df['date'].min(),
                           max_value = geo_df['date'].max()
                                 )


filtered_df = geo_df[

    (geo_df['date'] >= np.datetime64(start_date))
    & (geo_df['date'] <= np.datetime64(end_date))
]

filtered_battles = battles[
    (battles['displaydate'] >= np.datetime64(start_date))
    & (battles['displaydate'] <= np.datetime64(end_date))
]

## calculating frequency on the fly
## maps the value of the column geometry with their value counts
## then groups by geometry / data point
filtered_df['freq'] = filtered_df['geometry'].map(filtered_df['geometry'].value_counts())


min_freq = st.sidebar.text_input('Mininum entity occurrence:', 1)
max_freq = st.sidebar.text_input('Maximum entity occurrence:', int(filtered_df['freq'].max()))

filtered_df = filtered_df[
    (filtered_df['freq'] >= int(min_freq))
    & (filtered_df['freq'] <= int(max_freq))
]
if not filtered_battles.empty:
    duration_slider = st.sidebar.slider('Battle duration:',
                                        int(filtered_battles['Duration'].min()),
                                        int(filtered_battles['Duration'].max()),
                                        (
                                            int(filtered_battles['Duration'].min()),
                                            int(filtered_battles['Duration'].max()),

                                        )

                                        )

    filtered_battles = filtered_battles[
        (filtered_battles['Duration'] >= duration_slider[0])
        & (filtered_battles['Duration'] <= duration_slider[1])

    ]

    front_selection = st.sidebar.multiselect('Select battle front(s):',
                                             filtered_battles['Notes'].unique().tolist(),
                                             filtered_battles['Notes'].unique().tolist(),

                                             )

    filtered_battles = filtered_battles[filtered_battles['Notes'].isin(front_selection)]


groupby_data = filtered_df.groupby('geometry')
map_df = groupby_data.first()

borders = open_borders('data/borders/borders.shp')

filtered_borders = borders[

    # end date of border must be below start date filter
    # (borders['edate'] >= np.datetime64(start_date))
    (borders['gwsdate'] <= np.datetime64(end_date))
]

# geojson = geojson.groupby('NAME').first().reset_index()
# geojson = geojson.set_index('NAME')
filtered_borders = filtered_borders.groupby('cntry_name').first().reset_index()
filtered_borders = filtered_borders.set_index('cntry_name')
filtered_borders = filtered_borders.iloc[:10]
fig = px.choropleth(filtered_borders, geojson=filtered_borders['geometry'],
                    locations=filtered_borders.index,
                    color=filtered_borders.index,
                    width=1000, height=700, # width and height of the plot

                    )

##  Plotting
# fig = px.scatter_mapbox(map_df, lat='lat', lon='lon', #data and col. to use for plotting
#                         hover_name = 'mention',
#                         hover_data = ['freq'],
#                           size = 'freq', # sets the size of each points on the values in the frequencies col.
#                         # animation_frame = 'year',
#                         center = dict(lat=53, lon=16), #centers the map on specific coordinates
#                         zoom = 3, # zooms on these coordinates
#                         width=1000, height=700, # width and height of the plot
#                         )

## Adds capital on the map
fig.add_scattergeo(
        lat=filtered_borders['caplat'],
        lon=filtered_borders['caplong'],
        mode='markers',
        hovertext = filtered_borders['capname'],
        marker_symbol = 'hexagon',
        marker=go.scattergeo.Marker(
            size = 10
        #     size=map_df['freq'],
        #     sizemode='area',
        #     sizeref=map_df['freq'].max() / 15 ** 2
        #     # color='rgb(255, 0, 0)',
        #     # color= filtered_battles['Duration'],
        #     # showscale = True,
        #     # colorscale='Blackbody',
        #     # opacity=0.7
        ),
        hoverinfo='text'
    )

# fig['data'][0]['showlegend']=True
# fig['data'][0]['name']='Named Entity frequencies'
# fig['data'][0]['legendgroup']= 'Frequencies'
fig.add_scattergeo(
        lat=map_df['lat'],
        lon=map_df['lon'],
        mode='markers',
        hovertext = map_df['txthover'],
        marker=go.scattergeo.Marker(
            size=map_df['freq'],
            sizemode='area',
            sizeref=map_df['freq'].max() / 15 ** 2
            # color='rgb(255, 0, 0)',
            # color= filtered_battles['Duration'],
            # showscale = True,
            # colorscale='Blackbody',
            # opacity=0.7
        ),
        hoverinfo='text'
    )

## Adding battle points
fig.add_scattergeo(
        lat=filtered_battles['lat'],
        lon=filtered_battles['lon'],
        mode='markers',
        hovertext = filtered_battles['txthover'],
        marker_symbol = 'star',
        marker=go.scattergeo.Marker(
            size=13,
            # color='rgb(255, 0, 0)',
            color= filtered_battles['Duration'],
            showscale = True,
            colorscale='Blackbody',
            opacity=0.7
        ),
        hoverinfo='text'
    )
# st.header('War map')
# map_style = st.selectbox('Choose a map style:',
#                                  # these a free maps that do not require a mapbox token
#                          ["open-street-map", "carto-positron", "carto-darkmatter", "stamen-terrain",
#                           "stamen-toner", "stamen-watercolor",
#                           # 'white-bg'
#                           ])
#
#
# fig.update_layout(
#     margin = dict(l=0),
#     # mapbox_style = map_style,
#     legend=dict(
#     bgcolor='ivory',
#     bordercolor='lightgray',
#     borderwidth=1,
#     font = dict(color='black'),
#     yanchor="top",
#     y=0.99,
#     xanchor="left",
#     x=0.01)
# )
# fig['data'][1]['name'] = 'Battle duration'
# fig.update_layout(
#
#         mapbox_layers=[
#         {
#             "below": 'traces',
#             "sourcetype": "raster",
#             "source": [
#                 # 'https://www.runningreality.org/?highlight=177#05/https://www.runningreality.org/?highlight=177#05/01/58BC&47.23783,6.02405&zoom=9'
#                 # "http://tile.runningreality.org/wikipedia/{z}/{x}/{y}.png"
#                 # "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"
#                 # "https://tile.opentopomap.org/{z}/{x}/{y}.png"
#                 "https://tile.openhistoricalmap.org/{z}/{x}/{y}.png"
#
#                 # "http://tile.stamen.com/terrain/{z}/{y}/{x}.png"
#
#             ]
#         }
#       ]
# )


# )
# fig.update_layout()

st.plotly_chart(fig)


##################### PAGE LAYOUT #################
def get_window(text, window, left=True):
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

st.header('Context visualizer')
page_slider = st.slider(
    'Select entities mention',
    0, len(filtered_df), 50
)
window_slider = st.slider('Select context window', 1, 10, 5)

df_page = filtered_df.iloc[page_slider:page_slider + 50]

def convert(row, col, text):
    # print(text)
    data = row[col]
    if isinstance(data, str):
        return '<a href="{}">{}</a>'.format(data,  text)
    else:
        return 'No link available'

df_page['article_link'] = df_page.apply(convert, args=('article_link', 'View Article'), axis=1)
df_page['wikidata_link'] = df_page.apply(convert, args=('wikidata_link', 'View Wikidata'), axis=1)
df_page['date'] = pd.DatetimeIndex(df_page['date']).strftime("%Y-%m-%d")
df_page['context_word_window'] = window_slider
df_page['left_context'] = df_page['left_context'].apply(lambda x: get_window(x, window_slider))
df_page['right_context'] = df_page['right_context'].apply(lambda x: get_window(x, window_slider, left=False))

reversed_lg = {
    'de': "German",
    'fi': "Finnish",
    'fr': 'French'
}
df_page['lang'] = df_page['lang'].apply(lambda x: reversed_lg[x])
# df_page = df_page.fillna('No Data Available')
df_page = df_page[['newspaper', 'date', 'lang', 'context_word_window','left_context', 'mention', 'right_context',
            'article_link', 'wikidata_link']]

header_values = df_page.columns
cell_values = [df_page['newspaper'], df_page['date'], df_page['lang'], df_page['context_word_window'], df_page['left_context'], df_page['mention'],
                          df_page['right_context'], df_page['article_link'], df_page['wikidata_link']]


table = go.Figure(
    data=[
        go.Table(
            columnwidth=[80, 60, 40, 100, 100, 100, 100, 80, 80] ,
            header = dict(
                values= df_page.columns,
                # fill_color="paleturquoise",
                align="left",
                font=dict(color='black')
            ),
            cells = dict(
                values = cell_values,
                font=dict(color='black'),
                align="left"
            )
        )
    ],
    # layout = dict(autosize=True)
)
table.update_layout(
    autosize=False,
    width=1100,
    height=1000,
    margin=dict(l=0, r=0),

)
# title=['Hi Dash','Hello World']
# link=[html.A(html.P('Link'),href="yahoo.com"),html.A(html.P('Link'),href="google.com")]
#
# dictionary={"title":title,"link":link}
# df=pd.DataFrame(dictionary)
# table=dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True)
# table
st.plotly_chart(table)
# st.plotly_chart(df_page.to_dict('records'))r
