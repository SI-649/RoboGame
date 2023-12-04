# load up the libraries
from asyncio.windows_events import NULL
from tkinter import S
from urllib import robotparser
import panel as pn
import pandas as pd
import altair as alt
from altair_transform import extract_data
import Robogame as rg
import time,json
import networkx as nx
import traceback

# we want to use bootstrap/template, tell Panel to load up what we need
pn.extension(design='bootstrap')
pn.extension('vega')

mode = ['Astrogation Buffer Length', 'InfoCore Size', 'AutoTerrain Tread Count',
        'Polarity Sinks', 'Cranial Uplink Bandwidth', 'Repulsorlift Motor HP',
        'Sonoreceptors', 'Arakyd Vocabulator Model', 'Axial Piston Model',
        'Nanochip Model']
mode_select = pn.widgets.Select(name='mode of interest', options=mode)
bot_select = pn.widgets.IntInput(name='bot of interest', value=0, start=0, end=100)
bets_id_input = pn.widgets.TextInput(name='Bet ids', placeholder='')
bets_val_input = pn.widgets.TextInput(name='Bet values', placeholder='')
bets_button = pn.widgets.Button(name='Place bets', button_type='primary')
bet_all_input = pn.widgets.TextInput(name='Bet all value', placeholder = '-1')
bet_all_button = pn.widgets.Button(name='Place bet for all', button_type='primary')

# load up the data
def getFrame():
    # load up the two datasets, one for Marvel and one for DC    
    return(pd.DataFrame())

default_username = "bob"
default_server = "127.0.0.1"
default_port = "5000"

username_input= pn.widgets.TextInput(name='Username:', placeholder=default_username)
servername_input= pn.widgets.TextInput(name='Server', placeholder='127.0.0.1')
port_input= pn.widgets.TextInput(name='Port', placeholder='5000')
go_button = pn.widgets.Button(name='Run', button_type='primary')
static_text = pn.widgets.StaticText(name='State', value='Hit go to start')
static_text2 = pn.widgets.StaticText(name='', value='')

change_button = pn.widgets.Button(name='change', button_type='success')

sidecol = pn.Column()
sidecol.append(static_text)
sidecol.append(static_text2)
sidecol.append(username_input)
sidecol.append(servername_input)
sidecol.append(port_input)
sidecol.append(go_button)

sidecol.append(bot_select)
sidecol.append(mode_select)
sidecol.append(change_button)
sidecol.append(bets_id_input)
sidecol.append(bets_val_input)
sidecol.append(bets_button)
sidecol.append(bet_all_input)
sidecol.append(bet_all_button)

network = None
tree = None
info = None
hints = None
game = None
bot = 0

def bets_clicked(event):
    try:
        global game
        bet_dict = {}
        for i, id_str in enumerate(bets_id_input.value.split(',')):
            id = int(id_str.strip())
            bet = int(bets_val_input.value.split(',')[i].strip())
            bet_dict[id] = bet
        game.setBets(bet_dict)
    except:
        return
def bet_all_clicked(event):
    try:
        global game
        bet_dict = {}
        for i in range(100):
            bet_dict[i] = int(bet_all_input.value)
        game.setBets(bet_dict)
    except:
        return

def create_chart1(data):
    return alt.Chart(data).mark_bar().encode(
        alt.X('Productivity:Q', bin=True),  # Assuming 'expire' is quantitative
        y='count()',
    )
def create_chart2(data):
    return alt.Chart(data).mark_point().encode(
    x='Productivity:Q',
    y='id:Q'
)

def create_chart3(data):
    return alt.Chart(data).mark_arc().encode(
    theta=alt.Theta(field='count', type='quantitative'),
    color=alt.Color(field='winningTeam', type='nominal')
).transform_aggregate(
    count='count()',
    groupby=['winningTeam']
)

def create_chart4_combined(data, gt=None):
    if gt is None or 'unitsleft' not in gt:
        # Return an empty plot if gt is not available
        empty_data = pd.DataFrame({'id': [], 'expires': []})
        return alt.Chart(empty_data).mark_bar().encode(
            y=alt.Y('id:O', sort='x'),
            x=alt.X('expires:Q', title="Adjusted Expires")
        )

    # Calculate the new x-axis value
    adjusted_x_formula = "datum.expires - (100 - {})".format(gt['unitsleft'])

    # Define the color category based on adjusted_x
    color_category_formula = (
        "(datum.adjusted_x <= 5 ? 'red' : "
        "(datum.adjusted_x > 5 && datum.adjusted_x <= 20 ? 'yellow' : 'green'))"
    )

    # Apply filters and calculations for the combined chart
    chart = alt.Chart(data).mark_bar().transform_filter(
        alt.datum.id < 100
    ).transform_calculate(
        adjusted_x=adjusted_x_formula,
        color_category=color_category_formula
    ).transform_filter(
        (alt.datum.adjusted_x > 0)
    ).transform_window(
        rank='rank()',
        sort=[alt.SortField('adjusted_x', order='ascending')]
    ).transform_filter(
        (alt.datum.rank <= 10)
    ).encode(
        y=alt.Y('id:O', sort='x'),
        x=alt.X('adjusted_x:Q', title="Adjusted Expires"),
        color=alt.Color('color_category:N', scale=alt.Scale(domain=['red', 'yellow', 'green'],
                                                            range=['red', 'yellow', 'green']),
                        legend=None)
    )

    return chart

def create_chart4_green(data, gt=None):
    if gt is None or 'unitsleft' not in gt:
        # Return an empty plot if gt is not available
        empty_data = pd.DataFrame({'id': [], 'expires': []})
        return alt.Chart(empty_data).mark_bar().encode(
            y=alt.Y('id:O', sort='x'),
            x=alt.X('expires:Q', title="Adjusted Expires")
        )

    # Calculate the new x-axis value
    adjusted_x_formula = "datum.expires - (100 - {})".format(gt['unitsleft'])

    # Define the color category based on adjusted_x
    color_category_formula = (
        "(datum.adjusted_x <= 5 ? 'red' : "
        "(datum.adjusted_x > 5 && datum.adjusted_x <= 20 ? 'yellow' : 'green'))"
    )

    # Calculate rank of adjusted_x where it is greater than 20
    rank_formula = "rank()"

    chart1 = alt.Chart(data).mark_bar().transform_filter(
        alt.datum.id < 100
    ).transform_calculate(
        adjusted_x=adjusted_x_formula,
        color_category=color_category_formula
    ).transform_filter(
        alt.datum.adjusted_x > 20
    ).transform_window(
        rank='rank()',
        sort=[alt.SortField('adjusted_x', order='descending')]
    ).transform_filter(
        (alt.datum.rank <= 10)
    ).encode(
        y=alt.Y('id:O', sort='-x'),
        x=alt.X('adjusted_x:Q', title="Adjusted Expires"),
        color=alt.Color('color_category:N', scale=alt.Scale(domain=['green'],
                                                            range=['green']),
                        legend=None)
    )
    return chart1

def create_chart4_yellow(data, gt=None):
    if gt is None or 'unitsleft' not in gt:
        # Return an empty plot if gt is not available
        empty_data = pd.DataFrame({'id': [], 'expires': []})
        return alt.Chart(empty_data).mark_bar().encode(
            y=alt.Y('id:O', sort='x'),
            x=alt.X('expires:Q', title="Adjusted Expires")
        )

    # Calculate the new x-axis value
    adjusted_x_formula = "datum.expires - (100 - {})".format(gt['unitsleft'])

    # Define the color category based on adjusted_x
    color_category_formula = (
        "(datum.adjusted_x <= 5 ? 'red' : "
        "(datum.adjusted_x > 5 && datum.adjusted_x <= 20 ? 'yellow' : 'green'))"
    )

    rank_formula = "rank()"

    chart2 = alt.Chart(data).mark_bar().transform_filter(
        alt.datum.id < 100
    ).transform_calculate(
        adjusted_x=adjusted_x_formula,
        color_category=color_category_formula
    ).transform_filter(
        (alt.datum.adjusted_x > 5) & (alt.datum.adjusted_x <= 20)
    ).transform_window(
        rank='rank()',
        sort=[alt.SortField('adjusted_x', order='descending')]
    ).transform_filter(
        (alt.datum.rank <= 10)
    ).encode(
        y=alt.Y('id:O', sort='x'),
        x=alt.X('adjusted_x:Q', title="Adjusted Expires"),
        color=alt.Color('color_category:N', scale=alt.Scale(domain=['red', 'yellow', 'green'],
                                                            range=['red', 'yellow', 'green']),
                        legend=None)
    )
    return chart2

def create_chart4_red(data, gt=None):
    if gt is None or 'unitsleft' not in gt:
        # Return an empty plot if gt is not available
        empty_data = pd.DataFrame({'id': [], 'expires': []})
        return alt.Chart(empty_data).mark_bar().encode(
            y=alt.Y('id:O', sort='x'),
            x=alt.X('expires:Q', title="Adjusted Expires")
        )

    # Calculate the new x-axis value
    adjusted_x_formula = "datum.expires - (100 - {})".format(gt['unitsleft'])

    # Define the color category based on adjusted_x
    color_category_formula = (
        "(datum.adjusted_x <= 5 ? 'red' : "
        "(datum.adjusted_x > 5 && datum.adjusted_x <= 20 ? 'yellow' : 'green'))"
    )
    chart3 = alt.Chart(data).mark_bar().transform_filter(
        alt.datum.id < 100
    ).transform_calculate(
        adjusted_x=adjusted_x_formula,
        color_category=color_category_formula
    ).transform_filter(
        (alt.datum.adjusted_x > 0) & (alt.datum.adjusted_x <= 5)
    ).encode(
        y=alt.Y('id:O', sort='x'),
        x=alt.X('adjusted_x:Q', title="Adjusted Expires"),
        color=alt.Color('color_category:N', scale=alt.Scale(domain=['red', 'yellow', 'green'],
                                                            range=['red', 'yellow', 'green']),
                        legend=None)
    )
    return chart3


def plot_usability(df):
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_point()

    df_filtered = df[df['id'] <= 100].copy()
    df_filtered['teamOrWinner'] = df_filtered.apply(
        lambda row: 'Unassigned' if row['winner'] == -2 else row['winningTeam'], axis=1
    )
    df_filtered['matrix_x'] = (df_filtered['id'] - 1) % 10 + 1
    df_filtered['matrix_y'] = (df_filtered['id'] - 1) // 10
    unique_teams = sorted(df_filtered['teamOrWinner'].unique())
    if 'Unassigned' in unique_teams:
        unique_teams.remove('Unassigned')
        unique_teams = ['Unassigned'] + unique_teams

    color_scale = alt.Scale(
        domain=unique_teams,
        range=['green'] + ['red', 'purple', 'orange', 'pink', 'blue', 'yellow']  # More colors for variability
    )
    color_condition = alt.Color('teamOrWinner:N', scale=color_scale)
    chart = alt.Chart(df_filtered).mark_point(filled=True, size=100).encode(
        x=alt.X('matrix_x:O', axis=alt.Axis(labelAngle=0, title='')),
        y=alt.Y('matrix_y:O', axis=alt.Axis(title='')),
        color=color_condition,
        tooltip=['id', 'winner', 'winningTeam']
    ).properties(
        width=600,
        height=400
    )
    return chart

def read_hint(data):
    predhints_df = pd.read_json(json.dumps(data),orient='records')
    return predhints_df

def create_chart5(data, input,line):
    chart1= alt.Chart(data).transform_filter(alt.datum.id == input).mark_point().encode(
    x='time:Q',
    y='value:Q')
    chart2 = alt.Chart(line).transform_filter(alt.datum.id == input).mark_rule(color='red').encode(
    x='expires:Q')
    return chart1+ chart2

def create_chart6(data):
    return alt.Chart(data).mark_point().encode(
    x='time:Q',
    y='mean(value):Q'
)

def create_chart7(data):
    return alt.Chart(data).mark_bar().encode(
    y=alt.Y(field='Total_Productivity', type='quantitative'),
    color=alt.Color(field='winningTeam', type='nominal'),
    x=alt.X('winningTeam:N')
).transform_aggregate(
    Total_Productivity='sum(Productivity)',
    groupby=['winningTeam']
)

def create_chart8(data, input):
    return alt.Chart(data).transform_filter(alt.datum.column == input).mark_bar().encode(
        y = alt.Y('id:N', sort = alt.SortField(field='value', order='descending')),
        x = alt.X('value:Q').title(input)
        )

def create_chart9(data1, data2, input):
    result_df = pd.merge(data1, data2, on='id', how='left')
    columns  = list(result_df['column'].unique())
    columns.sort()
    dropdown = alt.binding_select(options = columns, name ='Select Parts:  ')
    select = alt.selection_point(
                                    fields = ['column'],
                                    value = [{"column":columns[0]}],
                                    bind = dropdown,
                                    on="keyup",
                                    clear="false"
                                )
    return alt.Chart(result_df).transform_filter(alt.datum.column == input).mark_circle().encode(
                                                x = alt.X('value:Q').title(input),
                                                y = alt.Y('Productivity:Q')
                                                )

def update():
    try:
        global game, static_text, network_view, tree_view, info_view, hints_view, vega_pane1, vega_pane2, vega_pane3
        gt = game.getGameTime()
        network_view.object = game.getNetwork()
        tree_view.object = game.getTree()
        info_view.object = game.getRobotInfo()[game.getRobotInfo().id < 100].sort_values('expires')
        hints_view.object = game.getHints()
        vega_pane1.object = create_chart1(game.getRobotInfo())
        vega_pane2.object = create_chart2(game.getRobotInfo())
        vega_pane3.object = create_chart3(game.getRobotInfo())
        vega_pane4_red.object = create_chart4_red(game.getRobotInfo(), gt)
        vega_pane4_yellow.object = create_chart4_yellow(game.getRobotInfo(), gt)
        vega_pane4_green.object = create_chart4_green(game.getRobotInfo(), gt)
        vega_pane4_combined.object = create_chart4_combined(game.getRobotInfo(), gt)
        vega_pane5.object = plot_usability(game.getRobotInfo())
        data4 = read_hint(game.getAllPredictionHints())
        vega_pane6.object = create_chart5(data4, bot, game.getRobotInfo())
        vega_pane7.object = create_chart6(data4)
        vega_pane8.object = create_chart7(game.getRobotInfo())
        data5 = read_hint(game.getAllPartHints())
        vega_pane9.object = create_chart8(data5, mode)
        vega_pane10.object = create_chart9(data5, game.getRobotInfo(), mode)
        static_text.value = "Time left: " + str(gt['unitsleft'])
        static_text2.value = 'Current time: ' + str(gt['curtime'])
    except:
        print(traceback.format_exc())

def go_clicked(event):
    try:
        global game, network, tree, info, hints
        uname = username_input.value
        if (uname == ""):
            uname = default_username
        server = servername_input.value
        if (server == ""):
            server = default_server
        port = port_input.value
        if (port == ""):
            port = default_port

        print(uname, server, port)
        game = rg.Robogame("bob",server=server,port=int(port))
        game.setReady()
        

        while(True):
            gametime = game.getGameTime()
            
            if ('Error' in gametime):
                static_text.value = "Error: "+str(gametime)
                break

            timetogo = gametime['gamestarttime_secs'] - gametime['servertime_secs']
            if (timetogo <= 0):
                static_text.value = "Let's go!"
                break
            static_text.value = "waiting to launch... game will start in " + str(int(timetogo))
            time.sleep(1) # sleep 1 second at a time, wait for the game to start

        # run a check every 5 seconds
        cb = pn.state.add_periodic_callback(update, 1000, timeout=600000)
    except:
        #print(traceback.format_exc())
        return
    
def change_clicked(event):
    try:
        global bot, mode
        bot = bot_select.value
        if (bot == ""):
            bot = 0
        mode = mode_select.value
        print(bot)
        if bot == 0:
            game.setRobotInterest([])
        else:
            game.setRobotInterest([bot])
    except:
        print(traceback.format_exc())
        return
    
go_button.on_click(go_clicked)
change_button.on_click(change_clicked)
bets_button.on_click(bets_clicked)
bet_all_button.on_click(bet_all_clicked)

template = pn.template.BootstrapTemplate(
    title='Robogames Demo',
    sidebar=sidecol,
)

network_view = pn.pane.JSON({"message":"waiting for game to start"})
tree_view = pn.pane.JSON({"message":"waiting for game to start"})
info_view = pn.pane.DataFrame()
hints_view = pn.pane.JSON({"message":"waiting for game to start"})
vega_pane1 = pn.pane.Vega(create_chart1(pd.DataFrame()), debounce=20)
vega_pane2 = pn.pane.Vega(create_chart2(pd.DataFrame()), debounce=20)
vega_pane3 = pn.pane.Vega(create_chart3(pd.DataFrame()), debounce=20)
vega_pane4_red = pn.pane.Vega(create_chart4_red(pd.DataFrame()), debounce=20)
vega_pane4_yellow = pn.pane.Vega(create_chart4_yellow(pd.DataFrame()), debounce=20)
vega_pane4_green = pn.pane.Vega(create_chart4_green(pd.DataFrame()), debounce=20)
vega_pane4_combined = pn.pane.Vega(create_chart4_combined(pd.DataFrame()), debounce=20)
vega_pane5 = pn.pane.Vega(plot_usability(pd.DataFrame()), debounce=20)
vega_pane6 = pn.pane.Vega(create_chart5(pd.DataFrame(), input = 0, line= pd.DataFrame()), debounce=20)
vega_pane7 = pn.pane.Vega(create_chart6(pd.DataFrame()), debounce=20)
vega_pane8 = pn.pane.Vega(create_chart7(pd.DataFrame()), debounce=20)
vega_pane9= pn.pane.Vega(create_chart8(pd.DataFrame(), input = ' '), debounce=20)
vega_pane10 = pn.pane.Vega(create_chart9(pd.DataFrame({'id': [1,2,3,4,5,6,7,8,9,10], 'column': mode}), pd.DataFrame({'id': [1]}),input = mode), debounce=20)



grid = pn.GridBox(ncols=2,nrows=4)
# grid.append(network_view)
# grid.append(tree_view)
# grid.append(hints_view)
# grid.append(vega_pane1)
# grid.append(vega_pane2)
# grid.append(vega_pane3)
grid.append(vega_pane4_combined)
grid.append(vega_pane5)
# grid.append(vega_pane4_red)
# grid.append(vega_pane4_yellow)
# grid.append(vega_pane4_green)

grid.append(vega_pane9)
grid.append(vega_pane10)

grid.append(vega_pane6)
grid.append(vega_pane7)
grid.append(vega_pane8)
grid.append(info_view)


template.main.append(grid)



template.servable()