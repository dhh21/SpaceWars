import panel as pn
import param
import plotly.graph_objs as go
import json
import pandas as pd
# import streamlit as st
# from streamlit_plotly_events import plotly_events

import geopandas as gpd
import plotly.express as px
import numpy as np
from shapely import wkt
from glob import glob
from datetime import datetime

epsg = 4326
pn.extension()
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

# @st.cache(allow_output_mutation=True)
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

# @st.cache(allow_output_mutation=True)
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
        df['anim_date'] = df['date'].dt.strftime('%B-%Y')
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

# @st.cache(allow_output_mutation=True)
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
# st.title('DHH21 Space Wars')

dic_lg = {
    "German": 'de',
    "Finnish": 'fi',
    "French": 'fr'
}
dic_news = {
    "Arbeiter Zeitung":'arbeiter_zeitung',
    "Helsingin Sanomat": 'helsingin_sanomat',
    "Illustrierte Kronen Zeitung": 'illustrierte_kronen_zeitung',
    "Le Matin": 'le_matin',
    "L'Oeuvre": 'l_oeuvre',
    # "Neue Freie Presse": 'neue_freie_presse'
}
#
# filtered_files = all_files
# l_df = []
# for file in filtered_files:
#     df = open_file(file)
#     l_df.append(df)
# geo_df = pd.concat(l_df).reset_index()
# geo_df = get_entities_hover_text(geo_df)

def filter_files(all_files, lg_select, newspapers_select, year_select):
    print(lg_select)
    filter1 = []
    for lge in [dic_lg[lg] for lg in lg_select.value]:
        for file in all_files:
            if lge in file:
                filter1.append(file)

    filter2 = []
    print(newspapers_select)
    for news in [dic_news[news] for news in newspapers_select.value]:
        for file in filter1:
            if news in file:
                filter2.append(file)

    filter3 = []
    print(year_select)
    for year in year_select.value:
        for file in filter2:
            if year in file:
                filter3.append(file)
    print('Done')
    l_df = []
    for file in filter3:
        df = open_file(file)
        l_df.append(df)
    geo_df = pd.concat(l_df).reset_index()
    geo_df = get_entities_hover_text(geo_df)
    return geo_df




lg_select = pn.widgets.MultiSelect(name= 'Language Selection',
                                   value = ['French'],
                                   # list(dic_lg.keys()),
                                   # ['French'],
                                    options = list(dic_lg.keys()))

newspapers_select = pn.widgets.MultiSelect(name='Newspapers',
                                           value = ["Le Matin"],
                                           # ['Arbeiter Zeitung', 'Helsingin Sanomat', 'Le Matin'],
                                           # ['Le Matin'],

                                            options= list(dic_news.keys()))

year_select = pn.widgets.MultiSelect(name='Years',
                                     value= ["1914"], #['1914', '1915', '1916', '1917', '1918'],

                                     # ['1914'],
                                     options = ['1913', '1914', '1915', '1916', '1917', '1918', '1919', '1920'])

@param.depends('lg_select', 'newspapers_select', 'year_select')
def get_df(all_files):
    geo_df = filter_files(all_files, lg_select, newspapers_select, year_select)
    ## calculating frequency on the fly
    ## maps the value of the column geometry with their value counts
    ## then groups by geometry / data point
    geo_df['freq'] = geo_df['geometry'].map(geo_df['geometry'].value_counts())
    # print(geo_df)
    return geo_df


## TODO: FIND A WAY TO LOAD ALL DATA ONE AND THEN FILTER THEM WHEN PLOTTING
## TODO: MAYBE BY USING A DATABASE INSTEAD OF LOADING THE FILES IN MEMORY
map_df = get_df(all_files)


#
#
# filtered_df = geo_df[
#
#     (geo_df['date'] >= np.datetime64(start_date))
#     & (geo_df['date'] <= np.datetime64(end_date))
# ]
#
start_date = pn.widgets.DatePicker(name='Start Date',
                                   ## TODO: NEED THE DATA BEFORE IN ORDER TO LIMIT POSSIBLE DATES
                                   # enabled_dates = list(map_df['date'].values)
                                   )
end_date = pn.widgets.DatePicker(name='End Date',
                                   ## TODO: NEED THE DATA BEFORE IN ORDER TO LIMIT POSSIBLE DATES
                                   # enabled_dates = list(map_df['date'].values),
                                   )

min_freq = pn.widgets.TextInput(name='Mininum entity occurrence:', placeholder = 'Enter a value here ...',
                                value = '1'
                                )
## TODO: NEED THE DATA BEFORE IN ORDER TO GET THE MAXIMUM POSSIBLE FREQUENCY
max_freq = pn.widgets.TextInput(name='Maximum entity occurrence:', placeholder = 'Enter a value here ...',
                                value = map_df['freq'].max().astype('str')
                                )

@pn.depends(lg_select.param.value, newspapers_select.param.value, year_select.param.value)
def get_plot(lg_select, newspapers_select, year_select):

    fig = px.scatter_geo(map_df, lat='lat', lon='lon', #data and col. to use for plotting
                            hover_name = 'mention',
                            hover_data = ['txthover'],
                              size = 'freq', # sets the size of each points on the values in the frequencies col.
                            animation_frame = 'anim_date',
                            # center = dict(lat=53, lon=16), #centers the map on specific coordinates
                            # zoom = 3, # zooms on these coordinates
                            width=1000, height=700, # width and height of the plot
                            )
    plot_panel = pn.pane.Plotly(fig, config={"responsive": True}, sizing_mode="stretch_both")

    ## adds callback when clicking on that plot
    @pn.depends(plot_panel.param.click_data)
    def string_hello_world(click_data):
        return click_data

    return plot_panel

@param.depends('lg_select', 'newspapers_select', 'year_select')
def plot(self):
    return self.get_plot()

# def create_app():
#     return pn.Row(self.param, self.plot)

row = pn.Row(
    pn.Column(lg_select, newspapers_select, year_select,
              start_date, end_date,
              min_freq, max_freq),
    get_plot
)



row.servable()



# filtered_battles = battles[
#     (battles['displaydate'] >= np.datetime64(start_date))
#     & (battles['displaydate'] <= np.datetime64(end_date))
# ]


#
#

# filtered_df = filtered_df[
#     (filtered_df['freq'] >= int(min_freq))
#     & (filtered_df['freq'] <= int(max_freq))
# ]
# if not filtered_battles.empty:
#     duration_slider = st.sidebar.slider('Battle duration:',
#                                         int(filtered_battles['Duration'].min()),
#                                         int(filtered_battles['Duration'].max()),
#                                         (
#                                             int(filtered_battles['Duration'].min()),
#                                             int(filtered_battles['Duration'].max()),
#
#                                         )
#
#                                         )
#
#     filtered_battles = filtered_battles[
#         (filtered_battles['Duration'] >= duration_slider[0])
#         & (filtered_battles['Duration'] <= duration_slider[1])
#
#     ]
#
#     front_selection = st.sidebar.multiselect('Select battle front(s):',
#                                              filtered_battles['Notes'].unique().tolist(),
#                                              filtered_battles['Notes'].unique().tolist(),
#
#                                              )
#
#     filtered_battles = filtered_battles[filtered_battles['Notes'].isin(front_selection)]

#
# groupby_data = filtered_df.groupby('geometry')
# map_df = groupby_data.first()
#
# # borders = open_borders('data/borders/borders.shp')
#
# bordersdf = pd.read_csv('data/borders/countryborders.csv')
# filtered_borders = json.load(open('data/testshape.geojson'))

# filtered_borders = borders[
#
#     # end date of border must be below start date filter
#     # (borders['edate'] >= np.datetime64(start_date))
#     (borders['gwsdate'] <= np.datetime64(end_date))
# ]

# filtered_borders = filtered_borders.groupby('cntry_name').first().reset_index()
# filtered_borders = filtered_borders.set_index('cntry_name')
# filtered_borders = filtered_borders.iloc[:10]
# fig = px.choropleth(filtered_borders, geojson=filtered_borders['geometry'],
#                     locations=filtered_borders.index,
#                     color=filtered_borders.index,
#                     width=1000, height=700, # width and height of the plot
#
#                     )

#
#
# ##  Plotting
# st.header('War map')
# ## need to cast date column to str in order to use it with the animation frame
# map_df['anim_date'] = map_df['anim_date'].astype(str)
#
# fig = px.scatter_geo(map_df, lat='lat', lon='lon', #data and col. to use for plotting
#                         hover_name = 'mention',
#                         hover_data = ['txthover'],
#                           size = 'freq', # sets the size of each points on the values in the frequencies col.
#                         animation_frame = 'anim_date',
#                         # center = dict(lat=53, lon=16), #centers the map on specific coordinates
#                         # zoom = 3, # zooms on these coordinates
#                         width=1000, height=700, # width and height of the plot
#                         )

#
#
# fig['data'][0]['showlegend']=True
# fig['data'][0]['name']='Named Entity frequencies'
# fig['data'][0]['legendgroup']= 'Frequencies'
#
#
# # ## Adds capital on the map
# fig.add_scattergeo(
#         lat=bordersdf['caplat'],
#         lon=bordersdf['caplong'],
#         mode='markers',
#         hovertext = bordersdf['capname'],
#         marker_symbol = 'hexagon',
#         marker=go.scattergeo.Marker(
#             size = 10
#         #     size=map_df['freq'],
#         #     sizemode='area',
#         #     sizeref=map_df['freq'].max() / 15 ** 2
#         #     # color='rgb(255, 0, 0)',
#         #     # color= filtered_battles['Duration'],
#         #     # showscale = True,
#         #     # colorscale='Blackbody',
#         #     # opacity=0.7
#         ),
#         hoverinfo='text'
#     )
#
# # fig.add_choropleth(
# #     geojson=filtered_borders,
# #     featureidkey='properties.cntry_name',
# #     locationmode='geojson-id',
# #     locations=bordersdf['cntry_name'],
# #     z = bordersdf['area'],
# #     showscale=False
# # )
# # fig['data'][1]['name'] = 'Capitals'
#
#
# # fig.add_scattergeo(
# #         lat=map_df['lat'],
# #         lon=map_df['lon'],
# #         mode='markers',
# #         hovertext = map_df['txthover'],
# #         marker=go.scattergeo.Marker(
# #             size=map_df['freq'],
# #             sizemode='area',
# #             sizeref=map_df['freq'].max() / 15 ** 2
# #             # color='rgb(255, 0, 0)',
# #             # color= filtered_battles['Duration'],
# #             # showscale = True,
# #             # colorscale='Blackbody',
# #             # opacity=0.7
# #         ),
# #         hoverinfo='text'
# #     )
#
# # Adding battle points
# fig.add_scattergeo(
#         lat=filtered_battles['lat'],
#         lon=filtered_battles['lon'],
#         mode='markers',
#         hovertext = filtered_battles['txthover'],
#         marker_symbol = 'star',
#         marker=go.scattergeo.Marker(
#             size=13,
#             # color='rgb(255, 0, 0)',
#             color= filtered_battles['Duration'],
#             showscale = True,
#             colorscale='Blackbody',
#             opacity=0.7
#         ),
#         hoverinfo='text'
#     )
# fig['data'][2]['name'] = 'Battle duration'

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

