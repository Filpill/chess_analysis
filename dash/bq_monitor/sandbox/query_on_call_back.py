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

    # Date Range block
    html.Div([
        html.H4("Date Range", style={'margin': '0', 'paddingRight': '8px'}),
        dcc.DatePickerRange(
            id='date-range-picker',
            start_date=date.today() - relativedelta(days=60),
            end_date=date.today(),
            min_date_allowed=date.today() - relativedelta(days=365), 
            max_date_allowed=date.today(),
            display_format='YYYY-MM-DD',
            style={
                "width": "100%",
            }
        )
    ]),

    html.Div([

        dash_table.DataTable(
                id='table-data',
                #columns=[{"name": prettify_label(i), "id": i} for i in table_columns],
                columns=[],
                data=[],
                page_size=10,
                page_action="native",
        ),

        html.Div([                                               
               html.Button("Download Table", id="download-btn"), 
               dcc.Download(id="download-component")             
        ])                                                       
    ], className="div-filler-outer"),
],
)


def load_data():                                                        
    credentials, project_id = default()                                 
    compute = discovery.build('compute', 'v1', credentials=credentials) 

    df_jobs = pd.read_gbq(sql_cte_return("cte_jobs_base"), project_id=project_id, dialect="standard", credentials=credentials)

    # Fixing Datatypes
    df_jobs["job_created_date"] = pd.to_datetime(df_jobs["job_created_date"])
    df_jobs["job_created_month"] = pd.to_datetime(df_jobs["job_created_month"])

    return df_jobs


def data_filters(df, start_date, end_date):

    # Applying filters
    df_filtered = df[
            (df['job_created_date'] >= pd.to_datetime(start_date)) &
            (df['job_created_date'] <= pd.to_datetime(end_date))
        ]

    return df_filtered

@callback(
    Output("table-data", "data"),
    Output("table-data", "columns"),
    [
     Input("date-range-picker", "start_date"),
     Input("date-range-picker", "end_date"),
     ]
)

def refresh_data(start_date, end_date):

    df_jobs = load_data()


    # Applying filters
    df_jobs_filtered = data_filters(df_jobs, start_date, end_date)


    # Creating Table
    table_data = df_jobs_filtered.to_dict("records")
    table_columns = [{"name": prettify_label(col), "id": col} for col in df_jobs_filtered.columns]

    #------------------------------------------------------------------------------------

    return table_data, table_columns


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
