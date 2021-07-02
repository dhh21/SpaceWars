import panel as pn

import plotly.graph_objs as go
import json
import pandas as pd
from sqlalchemy import create_engine
import tempfile
from datetime import datetime

css = ['https://cdn.datatables.net/1.10.24/css/jquery.dataTables.min.css',
       # Below: Needed for export buttons
       'https://cdn.datatables.net/buttons/1.7.0/css/buttons.dataTables.min.css',
       'static/css/style.css'
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

script = """
<script>
function renderTable(){
  $('.example').DataTable( {
    dom: 'Bfrtip',
    buttons: [
        'copyHtml5',
        'excelHtml5',
        'csvHtml5',
        'pdfHtml5'
    ]
} );
}

if (document.readyState === "complete") {
  renderTable()
} else {
  $(document).ready(renderTable);
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
        return '<a href="{}" target="_blank">{}</a>'.format(data,  text)
    else:
        return 'No link available'


engine = create_engine('postgresql://postgres:spacewars@localhost:5432/spacewars')


# ## need to cast date column to str in order to use it with the animation frame
# map_df['anim_date'] = map_df['anim_date'].astype(str)
## TODO : NOT SO SURE ABOUT THAT ANYMORE

## TODO : FILTER BODERS ACCORDING TO DATE AND CORRECT ISSUE WITH CAPITALS
borderjson = json.load(open('data/borders/countryborders.geojson'))
# #

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
                                 value=widget_values['dates'][500]

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
entity_display = pn.pane.Markdown("",)

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

def get_country_borders(start_date, end_date):
    """
     Collect the data from the database according the values of
    the widgets
    """
    start_date = str(start_date.value)
    end_date = str(end_date.value)
    # end_date = f"{end_date}::date"
    # args = (start_date, end_date)
    # q = '''SELECT * from battles
    # WHERE "displaydate" BETWEEN %s AND %s'''
    args = (end_date,)
    q = '''SELECT * from countryborders
    WHERE "gwsdate"::date <= %s::date'''
    bordersdf = read_sql_tmpfile(q, engine, args)
    bordersdf = bordersdf.groupby('cntry_name')
    bordersdf = bordersdf.first().reset_index()
    bordersdf.rename(columns={'cntry_name':'cntry_name'}, inplace=True)
    # print("borderdf ", bordersdf)
    return bordersdf



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

    args = (lg, newspaper, start_date, end_date)
    q = '''SELECT * from entities_2
    WHERE "lang" IN %s
    AND "newspaper" IN %s
    AND "date" BETWEEN %s AND %s
    '''
    map_df = read_sql_tmpfile(q, engine, args)

    map_df['date'] = pd.to_datetime(map_df['date'], format="%Y-%m-%d")
    map_df['anim_date'] = map_df['date'].dt.strftime('%B-%Y')
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

    # groups point by their geometry, so that a point only appear once
    # in the data.
    groupby_data = map_df.groupby('geometry')
    map_df = groupby_data.first()
    map_df = get_entities_hover_text(map_df)

    return map_df

def get_map_plot():


    map_df = get_map_df(lg_select, newspapers_select, start_date, end_date, context_window)
    df_battles = get_battle_df(start_date, end_date, min_duration, max_duration, front_selection)
    bordersdf = get_country_borders(start_date, end_date)
    bordersdf['zero'] = 0
    fig = go.Figure()

    fig.add_choropleth(
        geojson=borderjson,
        featureidkey='properties.cntry_name',
        locationmode='geojson-id',
        locations=bordersdf['cntry_name'],
        hovertext=bordersdf['cntry_name'],
        hoverinfo='text',
        z=bordersdf['zero'],
        showscale=False
    )
    #
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

    # ## Adds capital on the map
    fig.add_scattergeo(
            lat=bordersdf['caplat'],
            lon=bordersdf['caplong'],
            mode='markers',
            hovertext = bordersdf['capname'],
            marker_symbol = 'hexagon',
            marker=go.scattergeo.Marker(
            size = 10
            ),
            hoverinfo='text'
        )
    # fig['data'][2]['name'] = 'Capitals'

    # Adding battle points
    fig.add_scattergeo(
            lat=df_battles['lat'],
            lon=df_battles['lon'],
            mode='markers',
            hovertext = df_battles['txthover'],
            marker_symbol = 'star',
            marker=go.scattergeo.Marker(
                size=13,
                # color='rgb(255, 0, 0)',
                color= df_battles['Duration'],
                showscale = True,
                colorscale='Blackbody',
                opacity=0.7
            ),
            hoverinfo='text'
        )
    # fig['data'][3]['name'] = 'Battles'
    fig.update_geos(
        # resolution=50,
        scope='world',
        showcoastlines=True, coastlinecolor="RebeccaPurple",
        # showland=True, landcolor="LightGreen",
        showocean=True, oceancolor="LightBlue",
        showlakes=True, lakecolor="Blue",
        showrivers=True, rivercolor="Blue"
    )
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
        x=0.01),
    dragmode='drawopenpath',
    newshape_line_color='cyan',

    # title_text='Draw a path to separate versicolor and virginica',


    )
    fig.update_yaxes(automargin=True)
    fig.update_xaxes(automargin=True)

    # TODO: GET ALL ENTITES NOT JUST THE FIRST ONES
    # df_page = pd.DataFrame.from_dict(
    #     {"left_context":['aaaaaaa', 'iiiiiiiii'],
    #         "window_left_context": ['aaa', 'iii'],
    #      "mention": ['aaaa', 'ooo'],
    #      "right_context": ['aaaaaaaaaaaa', 'ooooooooo'],
    #      "window_right_context": ['aaaa', 'ooo']
    #      }
    # )
    df_page = map_df.reset_index()
    df_page = df_page[['window_left_context', 'mention', 'window_right_context']]
    #
    # html = df_page.to_html(classes=['example', 'panel-df'])
    # table = pn.pane.HTML(html + script)

    # return fig, table
    return fig, map_df, df_page

def update_entities_plot(event):
    new_df = get_map_df(lg_select, newspapers_select, start_date, end_date, context_window)
    # todo: CHANGER INDEX QUAND LES AUTRES MAPS SERONT AJOUTEES
    entities = warmap['data'][1]
    entities['lat'] = new_df['lat']
    entities['lon'] = new_df['lon']
    entities['hovertext'] = new_df['txthover']
    entities['marker']['size'] = new_df['freq']

    df_page = new_df.reset_index()
    df_page = df_page[['window_left_context', 'mention', 'window_right_context']]

    html = df_page.to_html(classes=['example', 'panel-df'])
    html = html.replace('<table', '<table style="width:80%"')

    table.object = html + script

def update_battle_plot(event):

    df_battles = get_battle_df(start_date, end_date, min_duration, max_duration, front_selection)
    battle_map = warmap['data'][3]
    battle_map['lat'] = df_battles['lat']
    battle_map['lon'] = df_battles['lon']
    battle_map['txthover'] = df_battles['txthover']
    battle_map['marker']['size'] = df_battles['Duration']

def update_context_window(event):
    """

    """
    new_window = int(context_window.value)

    df_page['context_word_window'] = new_window
    df_page['window_left_context'] = df_page['left_context'].apply(lambda x: get_window(x, new_window))
    df_page['window_right_context'] = df_page['right_context'].apply(lambda x: get_window(x, new_window, left=False))

    filtered_page = df_page[['window_left_context', 'mention', 'window_right_context']]
    html = filtered_page.to_html(classes=['example', 'panel-df'])
    html = html.replace('<table', '<table style="width:80%"')
    html = html + script
    table.object = html

# TODO: IF CAN BORDERS BY BACKGROUND IMAGE
def update_country_borders(event):
    """

    """
    bordersdf = get_country_borders(start_date, end_date)
    bordersmap = warmap['data'][0]
    # bordersmap['location'] = bordersdf['location']
    # print("BORDERS:", bordersmap.keys())

# plot_panel = pn.pane.Plotly(fig, config={"responsive": True})
# pn.pane.Plotly(fig, config={"responsive": True}, sizing_mode="stretch_both")
## adds callback when clicking on that plot


# warmap, table = get_map_plot()
warmap, map_df, df_page = get_map_plot()

## TODO: FREQUENCIES ON THE FLY, UPDATE WIDGET EACH TIME
min_freq = pn.widgets.TextInput(name='Mininum entity occurrence:', placeholder = 'Enter a value here ...',
                                value = '1'
                                )
# ## TODO: NEED THE DATA BEFORE IN ORDER TO GET THE MAXIMUM POSSIBLE FREQUENCY
max_freq = pn.widgets.TextInput(name='Maximum entity occurrence:', placeholder = 'Enter a value here ...',
                                value = map_df['freq'].max().astype('str')
                                )

def update_frequency_plot(event):
    new_df = map_df[
        map_df['freq'] <= int( min_freq.value)
        & map_df['freq'] >= int(max_freq.value)
    ]
    entities = warmap['data'][1]
    entities['lat'] = new_df['lat']
    entities['lon'] = new_df['lon']
    entities['hovertext'] = new_df['txthover']
    entities['marker']['size'] = new_df['freq']

    df_page = new_df.reset_index()
    df_page = df_page[['window_left_context', 'mention', 'window_right_context']]

    html = df_page.to_html(classes=['example', 'panel-df'])
    html = html.replace('<table', '<table style="width:80%"')

    table.object = html + script





# adding callbacks to update entities points and table
lg_select.param.watch(update_entities_plot, 'value')
newspapers_select.param.watch(update_entities_plot, 'value')
# start_date.param.watch(update_entities_plot, 'value')
# end_date.param.watch(update_entities_plot, 'value')

# adding callbacks to update battle points
min_duration.param.watch(update_battle_plot, 'value')
max_duration.param.watch(update_battle_plot, 'value')
# start_date.param.watch(update_battle_plot, 'value')
# end_date.param.watch(update_battle_plot, 'value')
front_selection.param.watch(update_battle_plot, 'value')

# adding callbacks to update country borders
start_date.param.watch(update_country_borders, 'value')
end_date.param.watch(update_country_borders, 'value')

# adding callbacks to update context window
context_window.param.watch(update_context_window, 'value')

# adding callbacks to update frequencies on plot
min_freq.param.watch(update_entities_plot, 'value')
max_freq.param.watch(update_entities_plot, 'value')

setting_col = pn.WidgetBox('### Options',
            lg_select, newspapers_select,
                        # calendar,
              start_date, end_date,
              # min_freq, max_freq,
            min_duration, max_duration,
            front_selection)

setting_row = pn.Row('### Options',
            pn.Column(lg_select, newspapers_select),
            pn.Column(start_date, end_date, min_freq, max_freq),
            pn.Column(front_selection, min_duration, max_duration),
            context_window,
            entity_display
            )

plot_config = {
    "responsive": True,
    "displaylogo": False,
    "displayModeBar": True,
    'toImageButtonOptions': {'height': None, 'width': None, },
    ## TODO: ADD DRAWING TOOLS BUT DOESNT SEEM TO WORK ON MAPS
    # 'modeBarButtonsToAdd':['drawline',
    #                         'drawopenpath',
    #                         'drawclosedpath',
    #                         'drawcircle',
    #                         'drawrect',
    #                         'eraseshape'
    #                                    ]
}

map_panel = pn.pane.Plotly(warmap, config=plot_config)

filtered_page = df_page[['window_left_context', 'mention', 'window_right_context']]

html = filtered_page.to_html(classes=['example', 'panel-df'])
# TODO: SOLUTION FOR NOW, MAYBE USE BREAKPOINTS IN CSS TO MAKE IT RESPONSIVE
html = html.replace('<table', '<table style="width:80%"')
# print("HTML ", type(html))

table = pn.pane.HTML(html + script, sizing_mode='stretch_width')
tabs = pn.Tabs(
    ('Warmap', map_panel),
    ('Concordancer', table),
    tabs_location='left'
)

@pn.depends(map_panel.param.click_data, watch=True)
def update_on_click(click_data):
    point = click_data['points'][0]
    print(point)
    pointindex = point['pointIndex']
    entity_data = map_df.iloc[pointindex]

    md_template = f"""<b>Entity</b>:{entity_data['mention']}<br>
    <b>Newspaper</b>: {entity_data['newspaper']}<br>
    <b>Language</b>: {entity_data['lang']}<br>
    <b>Date</b>: {entity_data['date'].strftime("%d %B %Y")}<br>
    <b>NewsEye link</b>: {entity_data['article_link']}<br>
    <b>Wikidata link</b>: {entity_data['wikidata_link']}<br>
    <b>Latittude - Longitude</b>: {entity_data['lat']} {entity_data['lon']}<br>"""

    entity_display.object = md_template
    # html = df_page.to_html(classes=['example', 'panel-df']) + script

    # new_html = df_page.iloc[point['pointIndex']:]
    new_html = df_page[df_page['mention'] == entity_data['mention']]
    new_html = new_html.to_html(classes=['example', 'panel-df'])
    new_html = new_html.replace('<table', '<table style="width:80%"')

    table.object = new_html + script

# bootstrap = pn.template.BootstrapTemplate(title='WEBAPP')
# bootstrap.sidebar.append(setting_col)
# bootstrap.main.append(war_col)
# bootstrap.main.append(tabs)

# bootstrap.servable()

template = """

{% extends base %}

{% block contents %}

{{ app_title }}

<div id="mySidebar" class="sidebar">
    <a href="javascript:void(0)" class="closebtn" onclick="closeNav()">&times;</a>
    {{ embed(roots.setting_col)}}
</div>

<button class="openbtn" onclick="openNav()">&#9776; Open Sidebar</button>
{{ embed(roots.setting_row)}}

{{ embed(roots.tabs)}}


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

</script>
{% endblock %}
"""

# div = plotly.io.to_html(warmap, full_html=False, include_plotlyjs=True)
# div = div.replace('<div>', '<div id="warmap" class="tabcontent">')
tmpl = pn.Template(template)
tmpl.add_variable('app_title', '<h1>SpaceWars</h1>')
tmpl.add_panel('tabs', tabs)
tmpl.add_panel('setting_col', setting_col)
tmpl.add_panel('setting_row', setting_row)

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
tmpl.servable()
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