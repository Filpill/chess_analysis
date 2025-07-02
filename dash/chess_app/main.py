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
            "time_class"        :  generate_dropdown_list(df["time_class"].dropna().unique()),
            "opening_archetype" :  generate_dropdown_list(df["opening_archetype"].dropna().unique())
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

    if selected_time_class:
        df = df[df['time_class'].isin(selected_time_class)]
    return df

def create_bar_chart(df, x_axis, y_axis):
    df_chart = df.groupby([x_axis], as_index=False)[y_axis].sum()
    bar_chart_fig = px.bar(
        df_chart,
        x=x_axis,
        y=y_axis,
        color_discrete_sequence=["#4285f4"]
    )
    return bar_chart_fig

def prettify_label(label):
    return label.replace("_", ' ').title()

def generate_dropdown_list(option_list):
    return [{'label': prettify_label(item), 'value': item} for item in sorted(option_list)]

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
start_date = "2025-03-01"
end_date = "2025-03-01"

app = Dash(
    __name__, external_stylesheets=[dbc.themes.DARKLY]
)
server = app.server

app.layout = dbc.Container([

    dcc.Store(id="dim-store"),
    dcc.Store(id="df-store"),

    html.Div([
        html.H1(["Chess Analysis Application"], style={
            "margin": "0"
        })
    ], style={"flex": "1"}),

    html.Div([
        html.Img(
            src="/assets/img/chess_logo.png",
            style={"width": "175px", "height": "auto"}
        )
    ], style={
        "display": "flex",
        "alignItems": "center",
        "justifyContent": "flex-end"
    }),

    dcc.DatePickerRange(
        id='date-range-picker',
        start_date=start_date,
        end_date=end_date,
        display_format='YYYY-MM-DD',
        style={"marginLeft": "12px"}
    ),

    dbc.Button("Fetch Data", id="fetch-button", n_clicks=0),

    html.Div([
        dcc.Dropdown(
            id='time-class-dropdown',
            multi=True,
            placeholder="Select Time Classes",
            style={"color": "black"},
        ),
        dcc.Dropdown(
            id='opening-dropdown',
            multi=True,
            placeholder="Select Opening Archetypes",
            style={"color": "black"},
        ),
    ], style={"marginTop": "20px"}),

    dcc.Graph(id="bar-chart-fig"), 
]),
style={"maxWidth": "800px"},
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
    Input("df-store", "data"),
    Input("time-class-dropdown", "value"),
    Input("opening-dropdown", "value"),
    prevent_initial_call=True
)
def update_chart_from_filters(df_data, selected_time_class, selected_opening):
    if not df_data:
        return go.Figure()  # Empty graph if no data

    df = pd.DataFrame(df_data)
    df_filtered = dimension_filter(df, selected_time_class, selected_opening)

    return create_bar_chart(df_filtered, "week_start", "total_games")

@callback(
    Output("df-store", "data"),
    Output("dim-store", "data"),
    Output("bar-chart-fig", "figure"),
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

    # Create bar graph of the selected metric
    bar_chart_fig = create_bar_chart(df, "week_start", "total_games")

    return df.to_dict("records"), dim_store, bar_chart_fig

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
