import os
import math
import numbers
import pandas_gbq
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc

from datetime import date
from dash import Dash, html, dcc, callback, dash_table
from dash.dependencies import Output, Input, State

from googleapiclient import discovery
from google.oauth2 import service_account
from google.auth import default

from dateutil.relativedelta import relativedelta

def sql_get_distinct_dimensions(credentials):
    sql = f"""
                SELECT DISTINCT
                    time_class,
                    opening_archetype
                FROM `checkmate-453316.dev_aggregate.weekly_openings`
        """
    df = pd.read_gbq(sql, project_id=project_id, dialect="standard", credentials=credentials)

    dim_store = {
            "time_class"        :  generate_dropdown_list(df["time_class"].dropna().unique(), include_all=True),
            "opening_archetype" :  generate_dropdown_list(df["opening_archetype"].dropna().unique(), include_all=False)
    }

    return dim_store

def sql_get_base_data(credentials, start_date, end_date):
    sql = f"""
                SELECT * 
                FROM `checkmate-453316.dev_aggregate.weekly_openings`
                WHERE
                    week_start BETWEEN "{start_date}" AND "{end_date}"
        """
    print("Fetching data from BQ")
    df = pd.read_gbq(sql, project_id=project_id, dialect="standard", credentials=credentials)
    return df

def dim_load_first_fetch(dim_store_current):
    # Only load dimensional data for list filters on the first data fetch
    if not dim_store_current:
        print("Updating dimensional filtering data")
        dim_store = sql_get_distinct_dimensions(credentials)
    else:
        dim_store = dim_store_current # Query data according to dates supplied
    return dim_store

def dimension_filter(df, selected_time_class, selected_opening):
    if selected_opening:
        df = df[df['opening_archetype'].isin(selected_opening)]

    if selected_time_class and selected_time_class != 'all':
        if isinstance(selected_time_class, str):
            selected_time_class = [selected_time_class]
        df = df[df['time_class'].isin(selected_time_class)]
    return df

def aggregate_opening_data(df):
    # Aggregate data
    df_opening_agg = df.groupby("opening_archetype", as_index=False)[
        ["total_games", "white_games", "black_games", "white_win_count", "black_win_count"]
    ].sum()

    # Calculate win percentages
    df_opening_agg["white_win_pct"] = (df_opening_agg["white_win_count"] / df_opening_agg["white_games"]) * 100
    df_opening_agg["black_win_pct"] = (df_opening_agg["black_win_count"] / df_opening_agg["black_games"]) * 100

    # Format for table
    df_opening_agg["white_win_pct_str"] = df_opening_agg["white_win_pct"].apply(lambda x: f"{x:.1f}%")
    df_opening_agg["black_win_pct_str"] = df_opening_agg["black_win_pct"].apply(lambda x: f"{x:.1f}%")
    return df_opening_agg

def create_opening_table(df):
    # Top 10 by total games
    df = df.sort_values(by="total_games", ascending=False).head(10)

    # Create dash table component
    top_opening_table = dbc.Table(
        [html.Thead(html.Tr([
            html.Th("Opening"), html.Th("Total Games"), html.Th("White Win%"), html.Th("Black Win%")
        ]))] +
        [html.Tbody([
            html.Tr([
                html.Td(row['opening_archetype']),
                html.Td(row['total_games']),
                html.Td(row['white_win_pct_str']),
                html.Td(row['black_win_pct_str']),
            ])
            for _, row in df.iterrows()
        ])],
        bordered=True, striped=True, hover=True, responsive=True
    )
    return top_opening_table

def create_kpi_tiles(df):

    if df.empty:
        return html.Div([
            html.H5("No data available for the selected filters.")
        ])

    # KPI extraction with values
    most_played_row  = df.loc[df["total_games"].idxmax()]
    least_played_row = df.loc[df["total_games"].idxmin()]
    best_white_row   = df.loc[df["white_win_pct"].idxmax()]
    best_black_row   = df.loc[df["black_win_pct"].idxmax()]
    worst_white_row   = df.loc[df["white_win_pct"].idxmin()]
    worst_black_row   = df.loc[df["black_win_pct"].idxmin()]

    kpis = {
        "most_played_opening": {
            "opening": most_played_row["opening_archetype"],
            "value": int(most_played_row["total_games"])
        },
        "least_played_opening": {
            "opening": least_played_row["opening_archetype"],
            "value": int(least_played_row["total_games"])
        },
        "highest_win_pct_as_white": {
            "opening": best_white_row["opening_archetype"],
            "value": best_white_row["white_win_pct_str"],
        },
        "highest_win_pct_as_black": {
            "opening": best_black_row["opening_archetype"],
            "value": best_black_row["black_win_pct_str"],
        },
        "lowest_win_pct_as_white": {
            "opening": worst_white_row["opening_archetype"],
            "value": worst_white_row["white_win_pct_str"],
        },
        "lowest_win_pct_as_black": {
            "opening": worst_black_row["opening_archetype"],
            "value": worst_black_row["white_win_pct_str"],
        },
    }

    kpi_display = html.Div([
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.Div("Most Played", className="card-title", style={'font-weight': 'bold'}),
                    html.Div(f"{kpis['most_played_opening']['opening']}", style={'font-size': '1rem'}),
                    html.Div(f"{kpis['most_played_opening']['value']:,} games", style={'font-size': '1.25rem', 'font-weight': 'bold'})
                ])
            ], color="primary", inverse=True), width=3),

            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.Div("Least Played", className="card-title", style={'font-weight': 'bold'}),
                    html.Div(f"{kpis['least_played_opening']['opening']}", style={'font-size': '1rem'}),
                    html.Div(f"{kpis['least_played_opening']['value']:,} games", style={'font-size': '1.25rem', 'font-weight': 'bold'})
                ])
            ], color="info", inverse=True), width=3),

            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.Div("Best Winrate as White", className="card-title", style={'font-weight': 'bold'}),
                    html.Div([
                        html.Img(src="/assets/img/wk.png", style={'height': '30px', 'margin-right': '10px'}),
                        html.Span(f"{kpis['highest_win_pct_as_white']['opening']}", style={'font-size': '1rem'})
                    ], style={'display': 'flex', 'align-items': 'center'}),
                    html.Div(f"{kpis['highest_win_pct_as_white']['value']}", style={'font-size': '1.25rem', 'font-weight': 'bold'})
                ])
            ], color="light", inverse=False), width=3),  # White card

            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.Div("Best Winrate as Black", className="card-title", style={'font-weight': 'bold'}),
                    html.Div([
                        html.Img(src="/assets/img/bk.png", style={'height': '30px', 'margin-right': '10px'}),
                        html.Span(f"{kpis['highest_win_pct_as_black']['opening']}", style={'font-size': '1rem'})
                    ], style={'display': 'flex', 'align-items': 'center'}),
                    html.Div(f"{kpis['highest_win_pct_as_black']['value']}", style={'font-size': '1.25rem', 'font-weight': 'bold'})
                ])
            ], color="dark", inverse=True), width=3),  # Black card
        ], className="g-3", justify="evenly")
    ])

    return kpi_display

def create_bar_chart(df, x_axis, y_axis):
    df_chart = df.groupby([x_axis], as_index=False)[y_axis].sum()
    bar_chart_fig = px.bar(
        df_chart,
        x=x_axis,
        y=y_axis,
        color_discrete_sequence=["#518c5a"],
        template="plotly_dark"
    )
    return bar_chart_fig

def prettify_label(label):
    return label.replace("_", ' ').title()

def generate_dropdown_list(option_list, include_all):
    options = [{'label': prettify_label(item), 'value': item} for item in sorted(option_list)] 
    if include_all:
        options.insert(0, {'label': 'All', 'value': 'all'})
    return options

def get_month_boundaries():
    now = pd.Timestamp.now()
    current_month_start = now.replace(day=1)

    date_boundary_dict = {
        "current_month" :  current_month_start,
        "previous_month" : current_month_start - pd.offsets.MonthBegin(1),
    }
    return date_boundary_dict

# Retrieve service account credentials for executing BigQuery queries
credentials, project_id = default()

# Default dates setting prepared on application interface
start_date = "2025-05-01"
end_date = "2025-05-31"

app = Dash(
    __name__, external_stylesheets=[dbc.themes.DARKLY]
)
server = app.server

app.layout = dbc.Container([

    dcc.Store(id="dim-store"),
    dcc.Store(id="df-store"),

    html.Div([
        html.H1("Chess Analysis Application", style={
            "margin": 0,
            "flex": 1  # let it take up remaining space
        }),
        html.Img(
            src="/assets/img/chess_logo.png",
            style={"width": "200px", "height": "auto"}
        )
    ], style={
        "display": "flex",
        "alignItems": "center",
        "justifyContent": "space-between",
        "margin-bottom": "20px"
    }),

    html.Div([
        html.Span("Date Filter:", style={'margin-right': '15px', 'font-weight': 'bold'}),
        dcc.DatePickerRange(
            id='date-range-picker',
            start_date=start_date,
            end_date=end_date,
            display_format='YYYY-MM-DD',
            style={"marginLeft": "0px"}
        ),
        dbc.Button("Fetch Data", id="fetch-button", n_clicks=0),
    ], style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '10px'}),

    html.Div([

        # Time Classification row
        html.Div([
            html.Div("Time Classification:", style={'margin-right': '15px', 'font-weight': 'bold'}),
            dcc.RadioItems(
                id='time-class-dropdown',
                labelStyle={'display': 'inline-block', 'margin-right': '25px'}
            )
        ], style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '15px'}),

        # Opening Archetypes row
        html.Div([
            html.Div("Opening Archetypes:", style={'margin-right': '15px', 'font-weight': 'bold'}),
            dcc.Dropdown(
                id='opening-dropdown',
                multi=True,
                placeholder="Select Opening Archetypes",
                style={"color": "black", 'flexGrow': 1,}
            )
        ], style={'flexGrow': 1, 'align-items': 'center', 'margin-bottom': '15px'}),

    ], style={'display': 'flex', 'flexDirection': 'column', 'marginTop': '20px'}),

    html.Div(
        id="open-kpi-data"
    ),

    dcc.Loading(
        id="loading-spinner",
        type="circle",
        fullscreen=False,
        children=[
            dcc.Graph(id="bar-chart-fig")
        ]
    ),

    html.Div(id="open-leader-table")
]),
style={"maxWidth": "1000px"},
fluid=True

@callback(
    Output("time-class-dropdown", "options"),
    Output("opening-dropdown", "options"),
    Input("dim-store", "data"),
    prevent_initial_call=True
)
def update_dimension_dropdowns(dim_store):
    if not dim_store:
        return [], []

    time_class_options = dim_store.get("time_class", [])
    opening_options = dim_store.get("opening_archetype", [])

    return time_class_options, opening_options

@callback(
    Output("bar-chart-fig", "figure", allow_duplicate=True),
    Output("open-leader-table", "children", allow_duplicate=True),
    Output("open-kpi-data", "children", allow_duplicate=True),
    Input("df-store", "data"),
    Input("time-class-dropdown", "value"),
    Input("opening-dropdown", "value"),
    prevent_initial_call=True
)
def update_chart_from_filters(dict_data, selected_time_class, selected_opening):
    if not dict_data:
        return go.Figure()  # Empty graph if no data

    # Pull in cached dataFrame and apply filters
    df = pd.DataFrame(dict_data)
    df = dimension_filter(df, selected_time_class, selected_opening)

    # Update Visualations
    bar_chart_fig = create_bar_chart(df, "week_start", "total_games")
    df_agg = aggregate_opening_data(df)
    top_opening_table = create_opening_table(df_agg)
    kpi_display = create_kpi_tiles(df_agg)

    return bar_chart_fig, top_opening_table, kpi_display

@callback(
    Output("df-store", "data"),
    Output("dim-store", "data"),
    Output("bar-chart-fig", "figure"),
    Output("open-leader-table", "children"),
    Output("open-kpi-data", "children"),
    Input("fetch-button", "n_clicks"),
    State("date-range-picker", "start_date"),
    State("date-range-picker", "end_date"),
    State("time-class-dropdown", "value"),
    State("opening-dropdown", "value"),
    State("dim-store", "data"),
    prevent_initial_call=True
)
def query_data_from_bigquery(n_clicks, start_date, end_date, selected_time_class, selected_opening, dim_store_current):

    # Query BigQuery and apply dimensional filters
    dim_store = dim_load_first_fetch(dim_store_current)
    df = sql_get_base_data(credentials, start_date, end_date)
    df = dimension_filter(df, selected_time_class, selected_opening)
    dict_data = df.to_dict("records") # For sending to the update callback query

    # Create initial visualations
    bar_chart_fig = create_bar_chart(df, "week_start", "total_games")
    df_agg = aggregate_opening_data(df)
    top_opening_table = create_opening_table(df_agg)
    kpi_display = create_kpi_tiles(df_agg)

    return dict_data, dim_store, bar_chart_fig, top_opening_table, kpi_display

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
