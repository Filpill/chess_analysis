import pandas_gbq
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


from datetime import date
from dash import Dash, html, dcc, callback, dash_table
from dash.dependencies import Output, Input, State

from googleapiclient import discovery
from google.oauth2 import service_account
from google.auth import default

from dateutil.relativedelta import relativedelta

# Background URL: https://images.chesscomfiles.com/chess-themes/backgrounds/originals/large/game_room.png

credentials, project_id = default()
compute = discovery.build('compute', 'v1', credentials=credentials)

script_setting = "dev"
sql_start_date = '2025-01-01'
sql_end_date   = '2025-01-31'

#----Production Query----
if script_setting == "prod":
    game_sql = f"""
        SELECT  
              game_date
            , COUNT(*) AS opening_count
        FROM `checkmate-453316.chess_data.games` 
        WHERE 
            game_date BETWEEN '{sql_start_date}' AND '{sql_end_date}' 
        AND opening NOT IN ('ECO Not Found', 'Undefined')
        GROUP BY ALL
        ORDER BY 
            opening_count DESC
    """
    df = pd.read_gbq(game_sql, project_id=project_id, dialect="standard", credentials=credentials)

#----Extraction To Local Query----#
if script_setting == "extract":
    sql = """
        SELECT  
            *
        FROM `checkmate-453316.chess_data_aggregated.opening_agg` 
    """
    df = pd.read_gbq(sql, project_id=project_id, dialect="standard", credentials=credentials)

    #Save to CSV
    filename = "all_data.csv"
    df.to_csv(filename)

#-----------------------------------------------------------#
#-----------------------------------------------------------#
#-----------------------------------------------------------#
#----Development - Read Files----#
if script_setting == "dev":
    filename = "all_data.csv"
    df = pd.read_csv(filename, index_col=0)

# Fix data types for source data
df["game_date"] = pd.to_datetime(df["game_date"])

app = Dash(__name__)

app.layout = html.Div([

    html.Div([
        html.Div([
                # Left side: H1 only
                html.Div([
                    html.H1([
                        html.Span("", className="bigger-nf-icon", style={"marginRight": "8px"}),
                        "Chess Analysis Application"
                    ], style={
                        "margin": "0"
                    })
                ], style={"flex": "1"}),

                # Right side: image
                html.Div([
                    html.Img(
                        src="/assets/img/chess_logo.png",
                        style={"width": "175px", "height": "auto"}
                    )
                ], style={
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "flex-end"
                })
            ], style={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center"
            })
    ], className="div-filler-outer"),
    html.Br(),

    html.Div([
        html.H2([
            html.Span("󰈲", className="bigger-nf-icon"),
            " Filters"
        ]),
        html.Br(),

        html.Div([
            html.Div([
                html.Div([
                    html.Span("󰃰", className="bigger-nf-icon", style={"marginLeft": "15px"})
                ], style={"display": "flex", "alignItems": "", "marginRight": "0px"}),

                html.H3("Date Range"),

                dcc.DatePickerRange(
                    id='date-range-picker',
                    start_date=df['game_date'].max().date() - relativedelta(days=14),
                    end_date=df['game_date'].max().date(),
                    min_date_allowed=df['game_date'].min().date(),
                    max_date_allowed=df['game_date'].max().date(),
                    display_format='YYYY-MM-DD',
                    style={"marginLeft": "12px"}
                )
            ], style={
                'display': 'flex',
                'alignItems': 'center',
                'width': '30%',
                'paddingRight': '2%',
                'whiteSpace': 'nowrap'
            }),
        ]),


        html.Div([

             html.Div([
               html.H3([
                   html.Span("", className="bigger-nf-icon"),
                   " Rated"
               ]),

               dcc.Dropdown(
                   id='rated-dropdown',
                   options=[
                        {"label": "Unrated", "value": False},
                        {"label": "Rated", "value": True}
                   ],
                   multi=True,
                   placeholder="Select one or more",
                   className="select-value"
               )
            ], style={'width': '20%', 'display': 'inline-block', 'paddingRight': '2%', "color": "grey"}),

            html.Div([
               html.H3([
                   html.Span("󱚊", className="bigger-nf-icon"),
                   " Game Rules"
               ]),

               dcc.Dropdown(
                   id='rules-dropdown',
                   options=[{'label': rules, 'value': rules} for rules in sorted(df['rules'].dropna().unique())],
                   multi=True,
                   placeholder="Select one or more",
                   className="select-value"
               )
            ], style={'width': '20%', 'display': 'inline-block', 'paddingRight': '2%', "color": "grey"}),

            html.Div([
                html.H3([
                    html.Span("", className="bigger-nf-icon"),
                    " Time Class"
                ]),
                dcc.Dropdown(
                    id='time-class-dropdown',
                    options=[{'label': time_class, 'value': time_class} for time_class in sorted(df['time_class'].dropna().unique())],
                    multi=True,
                    placeholder="Select one or more",
                    className="select-value"
                )
            ], style={'width': '20%', 'display': 'inline-block', 'paddingRight': '2%', "color": "grey"}),


            html.Div([
                html.H3([
                    html.Span("", className="bigger-nf-icon"),
                    " Opening"
                ]),

                dcc.Dropdown(
                    id='opening-dropdown',
                    options=[{'label': opening, 'value': opening} for opening in sorted(df['opening'].dropna().unique())],
                    multi=True,
                    placeholder="Select one or more",
                    className="select-value"
                )
            ], style={'width': '20%', 'display': 'inline-block', "color": "grey"}),
        ]),
    ], className="div-filler-outer"),
    html.Br(),


    html.Div([
        html.H3([
            html.Span("󰄨", className="bigger-nf-icon"),
            " Figure of Chess Games Played Data"
        ]),
        dcc.Graph(id="figure-game-count"),

        html.Br(),
        html.H3([
            html.Span("󱂔", className="bigger-nf-icon"),
            " Table of Chess Games Played Data"
        ]),

        dash_table.DataTable(
            id='table-game-count',
            columns=[{"name": i, "id": i} for i in df.columns],
            page_size=10,
            page_action="native",

            style_table={
                'overflowX': 'auto'
                },

            style_header={
                'backgroundColor': '#314236',
                "color": "white",
                'fontWeight': 'bold'
            },

            style_data_conditional=[
                {
                    "if": {"row_index": "odd"},
                    "backgroundColor": "#476350"
                },

                {
                    "if": {"state": "selected"},
                    "backgroundColor": "#758279",
                    "color": "white"
                },

                {
                    "if": {"state": "active"},
                    "backgroundColor": "#758279",
                    "color": "white"
                }
            ],

            style_cell={
                "backgroundColor": "#34523c",
                "color": "white",
                "border": "1px solid #444",
                "padding": "10px"
            },

        )
    ], className="div-filler-outer"),
],
)

def data_filters(df, start_date, end_date, selected_rating=None, selected_rules=None, selected_time_class=None, selected_opening=None):

    # Applying filters
    df_filtered = df[
            (df['game_date'] >= pd.to_datetime(start_date)) &
            (df['game_date'] <= pd.to_datetime(end_date))
        ]

    if selected_rating:
        df_filtered = df_filtered[df_filtered['rated'].isin(selected_rating)]

    if selected_rules:
        df_filtered = df_filtered[df_filtered['rules'].isin(selected_rules)]

    if selected_time_class:
        df_filtered = df_filtered[df_filtered['time_class'].isin(selected_time_class)]

    if selected_opening:
        df_filtered = df_filtered[df_filtered['opening'].isin(selected_opening)]

    return df_filtered

@callback(
    Output("figure-game-count", "figure"),
    Output("table-game-count", "data"),
    Output("table-game-count", "columns"),
    [Input("date-range-picker", "start_date"),
     Input("date-range-picker", "end_date"),
     Input("rated-dropdown", "value"),
     Input("rules-dropdown", "value"),
     Input("time-class-dropdown", "value"),
     Input("opening-dropdown", "value")]
)
def data_opening_count(start_date, end_date, selected_rating, selected_rules, selected_time_class, selected_opening):

    # Applying filters
    df_filtered = data_filters(df, start_date, end_date, selected_rating, selected_rules, selected_time_class, selected_opening)

    # Creating Chart
    df_agg_open_count = df_filtered.groupby("game_date", as_index=False)["row_count"].sum()
    fig = px.bar(
        df_agg_open_count,
        x="game_date",
        y="row_count",
        color_discrete_sequence=["#609b69"]  # all bars same color
    )
    layout={
        "plot_bgcolor": "#0d2611",     # chart area
        "paper_bgcolor": "#0d2611",    # outer area
        "font": {"color": "blue"},
        "xaxis": {"color": "white", "gridcolor": "#444"},
        "yaxis": {"color": "white", "gridcolor": "#444"},
        "hoverlabel" : {
            "font" : {"color" : "white"},     # Text color
            "bgcolor" : "#314236",            # Background color (optional)
            "bordercolor" :"white"            # Border color (optional)
        },
    }
    fig.update_xaxes(tickformat="%b %d", dtick="D1")
    fig.update_layout(transition_duration=1000)
    fig.update_layout(**layout)

    # Creating Table
    table_data = df_filtered.to_dict("records")
    table_columns = [{"name": i, "id": i} for i in df_filtered.columns]

    return fig, table_data, table_columns

if __name__ == "__main__":
    app.run(debug=True)