import os
import numbers
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

credentials, project_id = default()
compute = discovery.build('compute', 'v1', credentials=credentials)

def sql_cte_return(cte_name):
    sql = f"""
    DECLARE start_date     DATE    DEFAULT  CURRENT_DATE-365;
    DECLARE end_date       DATE    DEFAULT  CURRENT_DATE;
    DECLARE milli_to_base  FLOAT64 DEFAULT  0.001;
    DECLARE base_to_mega   INT64   DEFAULT  1000000;
    DECLARE base_to_giga   INT64   DEFAULT  1000000000;

    WITH cte_jobs_base AS (
      SELECT
            creation_time
          , EXTRACT(DATE FROM creation_time)                   AS job_created_date
          , DATE_TRUNC(EXTRACT(DATE FROM creation_time),MONTH) AS job_created_month
          , project_id
          , user_email
          , job_id
          , start_time
          , end_time
          , job_type
          , statement_type
          , priority
          , cache_hit
          , TIMESTAMP_DIFF(end_time, start_time, MILLISECOND)  AS total_query_time_ms
          , total_slot_ms
          , total_bytes_processed
          , total_bytes_billed
      FROM `checkmate-453316`.`region-eu`.INFORMATION_SCHEMA.JOBS jbp
      WHERE
        EXTRACT(DATE FROM end_time) BETWEEN start_date AND end_date
    )

    , cte_user_level_aggregate AS (
      SELECT 
            project_id
          , job_created_date
          , user_email
          , COUNT(*)                                               AS number_of_queries
          , ROUND(SUM(total_query_time_ms) * milli_to_base   , 1)  AS total_query_time_seconds
          , ROUND(SUM(total_slot_ms) * milli_to_base         , 1)  AS total_slot_seconds
          , ROUND(SUM(total_bytes_processed) / base_to_mega  , 1)  AS total_megabytes_processed
          , ROUND(SUM(total_bytes_billed) / base_to_mega     , 1)  AS total_megabytes_billed
      FROM cte_jobs_base
      GROUP BY ALL
      ORDER BY job_created_date ASC
    )

    SELECT * FROM {cte_name};
    """
    return sql

# Prettifying Labels
def prettify_label(label):
    return label.replace("_", ' ').title()

# Get current month data boundaries
def get_current_month_boundaries():
    now = pd.Timestamp.now()
    current_month_start = now.replace(day=1)
    current_month_end = (current_month_start + pd.offsets.MonthEnd(1))
    return current_month_start, current_month_end


df_jobs = pd.read_gbq(sql_cte_return("cte_jobs_base"), project_id=project_id, dialect="standard", credentials=credentials)
df_user = pd.read_gbq(sql_cte_return("cte_user_level_aggregate"), project_id=project_id, dialect="standard", credentials=credentials)

# Fixing Datatypes
df_jobs["job_created_date"] = pd.to_datetime(df_jobs["job_created_date"])
df_jobs["job_created_month"] = pd.to_datetime(df_jobs["job_created_month"])
df_user["job_created_date"] = pd.to_datetime(df_user["job_created_date"])

app = Dash(__name__)
server = app.server

app.layout = html.Div([

    html.Div([
        html.Div([
                html.Div([
                    html.H1(["BigQuery Data Processing Monitor"], style={
                        "margin": "8px"
                    })
                ], style={"flex": "1"}),

                html.Div([
                    html.Img(
                        src="/assets/img/bigquery.svg",
                        style={"width": "100px", "height": "auto"}
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

html.Div([
    # Date Range block
    html.Div([
        html.H4("Date Range", style={'margin': '0', 'paddingRight': '8px'}),
        dcc.DatePickerRange(
            id='date-range-picker',
            start_date=df_user['job_created_date'].max().date() - relativedelta(days=60),
            end_date=df_user['job_created_date'].max().date(),
            min_date_allowed=df_user['job_created_date'].min().date(),
            max_date_allowed=df_user['job_created_date'].max().date(),
            display_format='YYYY-MM-DD',
            style={
                "width": "100%",
            }
        )
    ], style={
        'width': '40%',
        'display': 'flex',
        'borderRadius': '3px',
        'alignItems': 'center',
        'backgroundColor': "#606878",
        'marginRight': '2%',
        "color": "grey"
    }),

    # User Email block
    html.Div([
        html.H4("User Email", style={'margin': '0', 'paddingRight': '8px'}),
        dcc.Dropdown(
            id='user-email-dropdown',
            options=[{'label': user_email, 'value': user_email} for user_email in sorted(df_user['user_email'].dropna().unique())],
            multi=True,
            placeholder="Select Users",
            className="select-value",
            style={"width": "94%"}
        )
    ], style={
        'display': 'flex',
        'borderRadius': '3px',
        'alignItems': 'center',
        'backgroundColor': "#606878",
        'flex': 1,
        'marginRight': '2%',
        "color": "grey"
    }),

    # Metric block
    html.Div([
        html.H4("Metric", style={'margin': '0', 'paddingRight': '8px'}),
        dcc.Dropdown(
            id='metric-dropdown',
            options=[{'label': prettify_label(metric), 'value': metric} for metric in sorted(df_user.select_dtypes(include=['number']).columns.tolist())],
            multi=False,
            placeholder="Select Metric",
            className="select-value",
            style={"width": "94%"}
        )
    ], style={
        'display': 'flex',
        'borderRadius': '3px',
        'alignItems': 'center',
        'backgroundColor': "#606878",
        'flex': 1,
        "color": "grey"
    }),
], style={'display': 'flex', 'width': '100%'})  # OUTERMOST container is flex



    ], className="div-filler-outer"),
    html.Br(),


    html.Div([
        html.Div(id="kpi-tiles", style={"display": "flex", "flexWrap": "wrap", "justifyContent": "center", "gap": "10px", "marginBottom": "20px"}),
    ], className="div-filler-outer"),

    html.Br(),

    html.Div([
        dcc.Graph(id="figure-count"),

        html.Br(),


        dash_table.DataTable(
            id='table-data',
            columns=[{"name": prettify_label(i), "id": i} for i in df_jobs.columns],
            page_size=10,
            page_action="native",

            style_table={
                'overflowX': 'auto',
                'backgroundColor': '#2f2f2f'  # Darker background outside the table itself (optional)
            },

            style_header={
                'backgroundColor': '#212b3b',  # Dark header
                "color": "white",
                'fontWeight': 'bold',
                'fontFamily': 'trebuc',          # <-- use your custom font
                "padding": "5px",
                "fontSize": "11px"
            },

            style_data={
                "backgroundColor": "#2f3642",   # Default background for all rows
                "color": "white",
                "border": "1px solid #444",
                "fontFamily": "trebuc",          # <-- use your custom font
                "padding": "10px",
                "fontSize": "10px"
            },

            style_data_conditional=[
                {
                    "if": {"row_index": "odd"},
                    "backgroundColor": "#4e5663"  # Alternate row color
                },
                {
                    "if": {"state": "selected"},
                    "backgroundColor": "#7991b8",
                    "color": "white",
                    "border": "2px solid #ffffff"
                },
                {
                    "if": {"state": "active"},
                    "backgroundColor": "#7991b8",
                    "color": "white",
                    "border": "2px solid #ffffff"
                }
            ],

            style_cell={
                "textAlign": "left",           # Make text aligned left nicely
                "whiteSpace": "normal",
                "height": "auto",
            },
        ),

        html.Div([                                               
               html.Button("Download Table", id="download-btn"), 
               dcc.Download(id="download-component")             
        ])                                                       
    ], className="div-filler-outer"),
],
)

def data_filters(df, start_date, end_date, current_month_flag=False, selected_user_email=None):

    # Applying filters
    df_filtered = df[
            (df['job_created_date'] >= pd.to_datetime(start_date)) &
            (df['job_created_date'] <= pd.to_datetime(end_date))
        ]

    if current_month_flag is False and selected_user_email:
        df_filtered = df_filtered[df_filtered['user_email'].isin(selected_user_email)]

    return df_filtered

@callback(
    Output("figure-count", "figure"),
    Output("table-data", "data"),
    Output("table-data", "columns"),
    Output("kpi-tiles", "children"),
    [
     Input("date-range-picker", "start_date"),
     Input("date-range-picker", "end_date"),
     Input("user-email-dropdown", "value"),
     Input("metric-dropdown", "value"),
     ]
)

def refresh_data(start_date, end_date, selected_user_email, selected_metric="total_megabytes_billed"):

    #------------------------------------------------------------------------------------
    # Current Month Setting
    current_month_start, current_month_end = get_current_month_boundaries()
    #------------------------------------------------------------------------------------

    # Applying filters
    df_user_current_month_fixed = data_filters(df_user, current_month_start, current_month_end, True, selected_user_email)
    df_user_filtered = data_filters(df_user, start_date, end_date, False, selected_user_email)
    df_jobs_filtered = data_filters(df_jobs, start_date, end_date, False, selected_user_email)

    if selected_metric is None:
        selected_metric = "total_megabytes_billed"

    #------------------------------------------------------------------------------------

    # Creating Metrics
    distinct_bigquery_users   = df_user_filtered["user_email"].nunique()
    total_number_of_queries   = int(df_user_filtered["number_of_queries"].sum())
    average_data_processed    = round(df_user_filtered["total_megabytes_processed"].sum()/total_number_of_queries, 2)
    average_data_billed       = round(df_user_filtered["total_megabytes_billed"].sum()/total_number_of_queries, 2)

    # Creating KPI
    free_tier_limit_mb = 1000000
    percentage_free_tier_used = round(df_user_current_month_fixed["total_megabytes_billed"].sum()/free_tier_limit_mb * 100, 2)

    # Putting metrics and KPI's into dict to do packaged return
    metric_dict = {
        "distinct_bigquery_users" : distinct_bigquery_users,
        "total_number_of_queries" : total_number_of_queries,
        "average_data_processed" : average_data_processed,
        "average_data_billed" : average_data_billed,
        "current_month_free_tier_used" : percentage_free_tier_used,
    }

    # Now create KPI tiles dynamically
    kpi_tiles = []
    for key, value in metric_dict.items():

        # Format display value based on metric type
        if "current_month" in key.lower():
            display_value = f"{value:.2f}%"   # 2 decimal places + % symbol
        elif "data" in key.lower(): 
            display_value = f"{value:,.1f} MB"
        elif isinstance(value, numbers.Number):
            display_value = f"{value:,}" if isinstance(value, int) else f"{value:,.2f}"
        else:
            display_value = str(value)

        kpi_tiles.append(
            html.Div([
                html.H4(prettify_label(key), style={"color": "#ebedf0", "fontSize": "16px", "margin": "0"}),
                html.H2(display_value, style={"color": "white", "fontSize": "32px", "margin": "0"})
            ], className="kpi-tile")
        )

    #------------------------------------------------------------------------------------

    # Creating Chart
    df_aggregate = df_user_filtered.groupby(["job_created_date"], as_index=False)[selected_metric].sum()


    x_axis_label = prettify_label("job_created_date")
    y_axis_label = prettify_label(selected_metric)

    fig = px.bar(
        df_aggregate,
        x="job_created_date",
        y=selected_metric,
        color_discrete_sequence=["#4285f4"]
    )

    layout = {
        "plot_bgcolor": "white",
        "paper_bgcolor": "white",
        "font": {"color": "black"},
        "xaxis": {
            "title": x_axis_label,  # <-- pretty x-axis title
            "color": "black",
            "gridcolor": "#d9dbdb",
        },
        "yaxis": {
            "title": y_axis_label,  # <-- pretty y-axis title
            "color": "black",
            "gridcolor": "#d9dbdb",
        },
        "legend": {
            "font": {"color": "white"}
        },
        "hoverlabel": {
            "font": {"color": "white"},
            "bgcolor": "#55698a",
            "bordercolor": "white"
        },
        "title": {
            "text": f"{y_axis_label}",  # use prettified label in chart title too!
            "x": 0.075,
            "xanchor": "left",
            "yanchor": "top",
            "y": 0.95,
            "font": {"size": 20, "color": "black"}
        }
    }

    fig.update_layout(
        font=dict(
            family="trebuc",           # EXACT same name from the CSS
            color="black"
        )
    )
    fig.update_layout(transition_duration=1000)
    fig.update_layout(**layout)

    #------------------------------------------------------------------------------------

    # Creating Table
    table_data = df_jobs_filtered.to_dict("records")
    table_columns = [{"name": prettify_label(col), "id": col} for col in df_jobs_filtered.columns]

    #------------------------------------------------------------------------------------

    return fig, table_data, table_columns, kpi_tiles


@callback(
    Output("download-component", "data"),
    Input("download-btn", "n_clicks"),
    State("table-data", "data"),
    prevent_initial_call=True
)
def download_table(n_clicks, table_data):
    df_download = pd.DataFrame(table_data)
    return dcc.send_data_frame(df_download.to_csv, filename="bq_resource_usage.csv", index=False)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
