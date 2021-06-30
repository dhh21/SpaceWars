import param
import panel as pn
from bokeh.sampledata.autompg import autompg

import plotly.graph_objs as go
import json
import pandas as pd
import geopandas as gpd
import plotly.express as px
from shapely import wkt
from glob import glob
from sqlalchemy import create_engine
import tempfile
from datetime import datetime

css = ['https://cdn.datatables.net/1.10.24/css/jquery.dataTables.min.css',
       # Below: Needed for export buttons
       'https://cdn.datatables.net/buttons/1.7.0/css/buttons.dataTables.min.css'
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

# battles = open_battle_file('data/Wikibattles.csv')
# battles = prepare_dataset(battles)
# battles = get_battle_hover_text(battles)
#
# filtered_battles = battles

DATASET_PATH = 'data/DATASET'
all_files = glob(f'{DATASET_PATH}/**/*.csv', recursive=True)
## Preparing the data


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

# list_year = ['1913', '1914', '1915', '1916', '1917', '1918', '1919', '1920']

# def filter_files(all_files, lg_select, newspapers_select, year_select):
#     print(lg_select)
#     filter1 = []
#     for lge in [dic_lg[lg] for lg in lg_select.value]:
#         for file in all_files:
#             if lge in file:
#                 filter1.append(file)
#
#     filter2 = []
#     print(newspapers_select)
#     for news in [dic_news[news] for news in newspapers_select.value]:
#         for file in filter1:
#             if news in file:
#                 filter2.append(file)
#
#     filter3 = []
#     print(year_select)
#     for year in year_select.value:
#         for file in filter2:
#             if year in file:
#                 filter3.append(file)
#     print('Done')
#     l_df = []
#     for file in filter3:
#         df = open_file(file)
#         l_df.append(df)
#     geo_df = pd.concat(l_df).reset_index()
#     geo_df = get_entities_hover_text(geo_df)
#     return geo_df

script = """
<script>
if (document.readyState === "complete") {
  $('.example').DataTable();
} else {
  $(document).ready(function () {
    $('.example').DataTable();
  })
}
</script>
"""

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
        return '<a href="{}">{}</a>'.format(data,  text)
    else:
        return 'No link available'


engine = create_engine('postgresql://postgres:spacewars@localhost:5432/spacewars')

# battles = open_battle_file('data/Wikibattles.csv')
# battles = prepare_dataset(battles)
# battles = get_battle_hover_text(battles)
#
# filtered_battles = battles


# geo_df = get_df(all_files)
# groupby_data = geo_df.groupby('geometry')
# map_df = groupby_data.first()
# ## need to cast date column to str in order to use it with the animation frame
# map_df['anim_date'] = map_df['anim_date'].astype(str)
## TODO : NOT SO SURE ABOUT THAT ANYMORE

## TODO : FILTER BODERS ACCORDING TO DATE AND CORRECT ISSUE WITH CAPITALS
# bordersdf = pd.read_csv('data/borders/countryborders.csv')
# filtered_borders = json.load(open('data/borders/countryborders.geojson'))
# #
# df_page = map_df.reset_index()
# df_page = df_page[['left_context', 'mention', 'right_context']]
# #
#
# filtered_df = geo_df[
#
#     (geo_df['date'] >= np.datetime64(start_date))
#     & (geo_df['date'] <= np.datetime64(end_date))
# ]
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
                                   value = ['French', 'German', 'Finnish'],
                                   # list(dic_lg.keys()),
                                   # ['French'],
                                    options = list(dic_lg.keys()))

newspapers_select = pn.widgets.MultiSelect(name='Newspapers',
                                           value =
                                           ['Arbeiter Zeitung', 'Helsingin Sanomat', 'Le Matin'],
                                           # ['Le Matin'],

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

                                 # enabled_dates = list(map_df['date'].values),
                                   )

# filtered_df = filtered_df[
#     (filtered_df['freq'] >= int(min_freq))
#     & (filtered_df['freq'] <= int(max_freq))
# ]

## TODO: FREQUENCIES ON THE FLY, UPDATE WIDGET EACH TIME
# min_freq = pn.widgets.TextInput(name='Mininum entity occurrence:', placeholder = 'Enter a value here ...',
#                                 value = '1'
#                                 )
# ## TODO: NEED THE DATA BEFORE IN ORDER TO GET THE MAXIMUM POSSIBLE FREQUENCY
# max_freq = pn.widgets.TextInput(name='Maximum entity occurrence:', placeholder = 'Enter a value here ...',
#                                 value = map_df['freq'].max().astype('str')
#                                 )
# filtered_battles = battles[
#     (battles['displaydate'] >= np.datetime64(start_date))
#     & (battles['displaydate'] <= np.datetime64(end_date))
# ]

battle_duration = pn.widgets.IntSlider(name='Battle duration (days)', start=widget_values['durations'][0], end=widget_values['durations'][-1], step=1, value=4)
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

# filtered_borders = borders[
#
#     # end date of border must be below start date filter
#     # (borders['edate'] >= np.datetime64(start_date))
#     (borders['gwsdate'] <= np.datetime64(end_date))
# ]
front_selection = pn.widgets.MultiSelect(name='Select battle front(s)',
                                     value= widget_values['fronts'],
                                     options = widget_values['fronts']
                                         )

# empty at first, display data about entity when clicked on it
## TODO: DISPLAY DATA ABOUT CAPITALS AND BATTLES AS WELL ?
entity_display = pn.pane.Markdown("",)

def read_sql_tmpfile(query, db_engine, arg=None):
    with tempfile.TemporaryFile() as tmpfile:
        conn = db_engine.raw_connection()
        cur = conn.cursor()
        # needed to escape raw SQL query
        if arg:
            query = cur.mogrify(query, arg).decode('utf-8')

        copy_sql = "COPY ({query}) TO STDOUT WITH CSV {head}".format(
            query=query, head="HEADER"
        )
        cur.copy_expert(copy_sql, tmpfile)
        tmpfile.seek(0)
        df = pd.read_csv(tmpfile)
        return df

def get_map_df(lg, newspaper, start_date, end_date):
    """
    Collect the data from the database according the values of
    the widgets
    """
    lg = [f"{dic_lg[x]}" for x in lg.value]
    lg = tuple(lg)
    newspaper = tuple([f"{x}" for x in newspaper.value])

    start_date = str(start_date.value)
    end_date = str(end_date.value)

    args = (lg, newspaper, start_date, end_date)
    q = '''SELECT * from entities
    WHERE "lang" IN %s
    AND "newspaper" IN %s
    AND "date" BETWEEN %s AND %s
    '''
    map_df = read_sql_tmpfile(q, engine, args)

    # geo_df = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)
    # crs = {'init': f'epsg:{epsg}'}  # http://www.spatialreference.org/ref/epsg/2263/
    # map_df = gpd.GeoDataFrame(map_df, crs=crs)

    map_df['date'] = pd.to_datetime(map_df['date'], format="%Y-%m-%d")
    map_df['anim_date'] = map_df['date'].dt.strftime('%B-%Y')
    map_df['year'] = pd.DatetimeIndex(map_df['date']).year
    map_df['year'] = map_df['year'].astype(str)
    map_df['txthover'] = get_entities_hover_text(map_df)

    map_df['freq'] = map_df['geometry'].map(map_df['geometry'].value_counts())
    window_slider = 5  ## TODO: ADD WINDOW SLIDER WIDGET
    map_df['article_link'] = map_df.apply(convert, args=('article_link', 'View Article'), axis=1)
    map_df['wikidata_link'] = map_df.apply(convert, args=('wikidata_link', 'View Wikidata'), axis=1)
    # geo_df['date'] = pd.DatetimeIndex(geo_df['date']).strftime("%Y-%m-%d")
    map_df['context_word_window'] = window_slider
    map_df['left_context'] = map_df['left_context'].apply(lambda x: get_window(x, window_slider))
    map_df['right_context'] = map_df['right_context'].apply(lambda x: get_window(x, window_slider, left=False))
    map_df['lang'] = map_df['lang'].apply(lambda x: reversed_lg[x])

    # groups point by their geometry, so that a point only appear once
    # in the data.
    groupby_data = map_df.groupby('geometry')
    map_df = groupby_data.first()
    return map_df


# @pn.depends(lg_select.param.value, newspapers_select.param.value, start_date.param.value, end_date.param.value)
# @pn.depends(lg_select, newspapers_select, start_date, end_date)
# def get_map_plot(lg_select, newspapers_select, start_date, end_date):
def get_map_plot():

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
    fig = go.Figure()

    # fig.add_choropleth(
    #     geojson=filtered_borders,
    #     featureidkey='properties.cntry_name',
    #     locationmode='geojson-id',
    #     locations=bordersdf['cntry_name'],
    #     z = bordersdf['area'],
    #     showscale=False
    # )
    map_df = get_map_df(lg_select, newspapers_select, start_date, end_date)
    fig.add_scattergeo(
            lat=map_df['lat'],
            lon=map_df['lon'],
            mode='markers',
            hovertext = map_df['txthover'],
            marker=go.scattergeo.Marker(
                size=map_df['freq'],
                sizemode='area',
                sizeref=map_df['freq'].max() / 15 ** 2

            ),
            hoverinfo='text'
        )

    # fig['data'][1]['showlegend']=True
    # fig['data'][1]['name']='Named Entity frequencies'
    # fig['data'][1]['legendgroup']= 'Frequencies'

    # # ## Adds capital on the map
    # fig.add_scattergeo(
    #         lat=bordersdf['caplat'],
    #         lon=bordersdf['caplong'],
    #         mode='markers',
    #         hovertext = bordersdf['capname'],
    #         marker_symbol = 'hexagon',
    #         marker=go.scattergeo.Marker(
    #         size = 10
    #         ),
    #         hoverinfo='text'
    #     )
    # fig['data'][2]['name'] = 'Capitals'

    # Adding battle points
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
    # fig['data'][3]['name'] = 'Battles'


    fig.update_layout(

        legend=dict(
        bgcolor='ivory',
        bordercolor='lightgray',
        borderwidth=1,
        font = dict(color='black'),
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01)
    )

        # df_page[['newspaper', 'date', 'lang', 'context_word_window', 'left_context', 'mention', 'right_context',
        #                'article_link', 'wikidata_link']]
    # df_page = df_page[['newspaper', 'date']]

    # TODO: GET ALL ENTITES NOT JUST THE FIRST ONES
    df_page = map_df.reset_index()
    df_page = df_page[['left_context', 'mention', 'right_context']]

    html = df_page.to_html(classes=['example', 'panel-df'])
    # table = pn.pane.HTML(html + script)

    # plot_panel = pn.pane.Plotly(fig, config={"responsive": True})
    # pn.pane.Plotly(fig, config={"responsive": True}, sizing_mode="stretch_both")
    ## adds callback when clicking on that plot
    # @pn.depends(plot_panel.param.click_data, watch=True)
    # def update_on_click(click_data):
    #     point = click_data['points'][0]
    #     pointindex = point['pointIndex']
    #     entity_data = map_df.iloc[pointindex]
    #     print(entity_data)
    #
    #     md_template = f"""<b>Entity</b>:{entity_data['mention']}<br>
    #     <b>Newspaper</b>: {entity_data['newspaper']}<br>
    #     <b>Language</b>: {entity_data['lang']}<br>
    #     <b>Date</b>: {entity_data['date'].strftime("%d %B %Y")}<br>
    #     <b>NewsEye link</b>: {entity_data['article_link']}<br>
    #     <b>Wikidata link</b>: {entity_data['wikidata_link']}<br>
    #     <b>Latittude - Longitude</b>: {entity_data['lat']} {entity_data['lon']}<br>"""
    #
    #     entity_display.object = md_template
    #     # html = df_page.to_html(classes=['example', 'panel-df']) + script
    #
    #     new_html = df_page.iloc[point['pointIndex']:]
    #     # new_html = df_page[df_page['mention'] == entity_data['mention']] ## TODO: BUG HERE TO DISPLAY THE TABLE
    #     new_html.to_html(classes=['example', 'panel-df']) + script
    #     print(new_html)
    #     table.object = new_html
    #

    # @pn.depends(plot_panel.param.click_data, watch=True)
    # def print_hello_world(click_data):
    #     print("hello world", click_data)

    # return plot_panel, table
    return fig, html
# table = pn.pane.HTML(html+script, sizing_mode='stretch_width')

def update_entities_plot(event):
    new_df = get_map_df(lg_select, newspapers_select, start_date, end_date)
    warmap['data'][0]['lat'] = new_df['lat']
    warmap['data'][0]['lon'] = new_df['lon']
    warmap['data'][0]['hovertext'] = new_df['txthover']
    warmap['data'][0]['marker']['size'] = new_df['freq']

def update_battle_plot(event):
    print("BAAAATTTTLES")





warmap, table = get_map_plot()
lg_select.param.watch(update_entities_plot, 'value')
lg_select.param.watch(update_battle_plot, 'value')

newspapers_select.param.watch(update_entities_plot, 'value')


setting_col = pn.Column(pn.pane.Markdown('### Options'),
            lg_select, newspapers_select,
              # start_date, end_date, # TODO: CORRECT BUG
              # min_freq, max_freq,
              battle_duration, front_selection)

war_col = pn.Column(pn.pane.Markdown('#WEBAPP TITLE'),
        pn.pane.Markdown('## War Map'),
        pn.pane.Plotly(warmap, config={"responsive": True}),
        pn.pane.HTML(table + script)
        # warmap,
        # table
                    )

bootstrap = pn.template.BootstrapTemplate(title='WEBAPP')
bootstrap.sidebar.append(setting_col)
bootstrap.main.append(war_col)

bootstrap.servable()

template = """
{% extends base %}

<!-- goes in body -->
{% block postamble %}
<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css">
{% endblock %}

<!-- goes in body -->
{% block contents %}
{{ app_title }}
<p>This is a Panel app with a custom template allowing us to compose multiple Panel objects into a single HTML document.</p>
<br>
<div class="container">
  <div class="row">
    <div class="col-lg-12">
      {{ embed(roots.A) }}
    </div>
  </div>
</div>
{% endblock %}
"""

# nb_template = """
# {% extends base %}
#
# {% block contents %}
# {{ app_title }}
# <p>This is a Panel app with a custom template allowing us to compose multiple Panel objects into a single HTML document.</p>
# <br>
# <div style="display:table; width: 100%">
#   <div style="display:table-cell; margin: auto">
#     {{ embed(roots.A) }}
#   </div>
#   <div style="display:table-cell; margin: auto">
#     {{ embed(roots.B) }}
#   </div>
# </div>
# {% endblock %}
# """

# tmpl = pn.Template(template, nb_template=nb_template)
# tmpl = pn.Template(template)
# tmpl.add_variable('app_title', '<h1>Custom Template App</h1>')
#
# tmpl.add_panel('A', warmap)
# tmpl.add_panel('B', table)
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
