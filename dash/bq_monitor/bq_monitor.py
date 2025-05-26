import os
import math
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

def sql_cte_return(PROJECT_ID, REGION, cte_name):
    sql = f"""
    DECLARE start_date      DATE     DEFAULT  CURRENT_DATE-365;
    DECLARE end_date        DATE     DEFAULT  CURRENT_DATE;
    DECLARE milli_to_base   FLOAT64  DEFAULT  0.001;
    DECLARE base_to_mega    INT64    DEFAULT  1000000;
    DECLARE base_to_giga    INT64    DEFAULT  1000000000;
    DECLARE base_to_tera    INT64    DEFAULT  1000000000000;
    DECLARE dollars_per_TB  FLOAT64  DEFAULT  6.25;

    WITH cte_jobs_base AS (
      SELECT
            creation_time                                      AS job_creation_dt
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

          , TIMESTAMP_DIFF(end_time, start_time, MILLISECOND)                  AS total_query_ms
          , TIMESTAMP_DIFF(end_time, start_time, MILLISECOND) * milli_to_base  AS total_query_seconds

          , total_slot_ms
          , total_slot_ms * milli_to_base                                      AS total_slot_seconds

          , total_bytes_processed
          , total_bytes_processed / base_to_mega                               AS total_megabytes_processed
          , total_bytes_processed / base_to_giga                               AS total_gigabytes_processed

          , total_bytes_billed
          , total_bytes_billed / base_to_mega                                  AS total_megabytes_billed
          , total_bytes_billed / base_to_giga                                  AS total_gigabytes_billed

          , total_bytes_billed / base_to_tera * dollars_per_TB                 AS query_cost_usd

      FROM `{PROJECT_ID}`.`{REGION}`.INFORMATION_SCHEMA.JOBS jbp
      WHERE
        EXTRACT(DATE FROM end_time) BETWEEN start_date AND end_date
    )

    , cte_user_level_aggregate AS (
      SELECT 
            project_id
          , job_created_date
          , user_email
          , COUNT(*)                        AS number_of_queries
          , SUM(total_query_seconds)        AS total_query_seconds
          , SUM(total_slot_seconds)         AS total_slot_seconds
          , SUM(total_gigabytes_processed)  AS total_gigabytes_processed
          , SUM(total_gigabytes_billed)     AS total_gigabytes_billed
          , SUM(query_cost_usd)             AS total_query_cost_usd
      FROM cte_jobs_base
      GROUP BY ALL
      ORDER BY job_created_date ASC
    )

    SELECT * FROM {cte_name};
    """
    return sql

def data_filters(df, start_date, end_date, fixed_range_flag=False, selected_user_email=None): 
                                                                                                
    # Applying filters                                                                          
    df_filtered = df[                                                                           
            (df['job_created_date'] >= pd.to_datetime(start_date)) &                            
            (df['job_created_date'] <= pd.to_datetime(end_date))                                
        ]                                                                                       
                                                                                                
    if fixed_range_flag is False and selected_user_email:                                     
        df_filtered = df_filtered[df_filtered['user_email'].isin(selected_user_email)]          
                                                                                                
    return df_filtered                                                                          

# Prettifying Labels
def prettify_label(label):
    return label.replace("_", ' ').title()

# Get current month data boundaries
def get_month_boundaries():
    now = pd.Timestamp.now()
    current_month_start = now.replace(day=1)

    date_boundary_dict = {
        "current_month_start" :  current_month_start,
        "current_month_end" :    current_month_start + pd.offsets.MonthEnd(1),
        "previous_month_start" : current_month_start - pd.offsets.MonthBegin(1),
        "previous_month_end" :   current_month_start - pd.Timedelta(days=1),
    }

    return date_boundary_dict

def format_kpi_value(key,value):                                                    
    # Format display value based on metric type                                     
    if "current_month" in key.lower():                                              
        display_value = f"{value:.2f}%"   # 2 decimal places + % symbol             
    elif "data" in key.lower():                                                     
        display_value = f"{value:,.3f} GB"                                          
    elif "usd" in key.lower():                                                  
        display_value = f"${value:,.2f}"                                           
    elif isinstance(value, numbers.Number):                                         
        display_value = f"{value:,}" if isinstance(value, int) else f"{value:,.2f}" 
    else:                                                                           
        display_value = str(value)                                                  
    return display_value                                                            

def generate_dropdown_options(option_list):
    return [{'label': prettify_label(item), 'value': item} for item in sorted(option_list)]

def create_kpi_tiles(df_user_filtered, df_user_current_month):                                                     
    free_tier_limit_gb = 10**3                                                                                     
    distinct_bigquery_users       = df_user_filtered["user_email"].nunique()                                       
    total_number_of_queries       = int(df_user_filtered["number_of_queries"].sum())                               
    average_data_bill_per_query   = df_user_filtered["total_gigabytes_billed"].sum()/total_number_of_queries       
    average_usd_cost_per_query    = df_user_filtered["total_query_cost_usd"].sum()/total_number_of_queries         
    percentage_free_tier_used     = df_user_current_month["total_gigabytes_billed"].sum()/free_tier_limit_gb * 100 
                                                                                                                   
    # Putting metrics and KPI's into dict to do packaged return                                                    
    metric_dict = {                                                                                                
        "total_number_of_queries" : total_number_of_queries,                                                       
        "average_USD_cost_per_query" : average_usd_cost_per_query,                                                 
        "average_data_bill_per_query" : average_data_bill_per_query,                                               
        "current_month_free_tier_used" : percentage_free_tier_used,                                                
    }                                                                                                              
                                                                                                                   
    # Now create KPI tiles dynamically                                                                             
    kpi_tiles = []                                                                                                 
    for key, value in metric_dict.items():                                                                         
                                                                                                                   
        display_value = format_kpi_value(key,value)                                                                
                                                                                                                   
        kpi_tiles.append(                                                                                          
            html.Div([                                                                                             
                html.H4(prettify_label(key), style={"color": "#ebedf0", "fontSize": "16px", "margin": "0"}),       
                html.H2(display_value, style={"color": "white", "fontSize": "32px", "margin": "0"})                
            ], className="kpi-tile")                                                                               
        )                                                                                                          
    return kpi_tiles                                                                                               

def load_data(PROJECT_ID, REGION, cte_name, date_col_list):                                                        
    credentials, project_id = default()                                 
    compute = discovery.build('compute', 'v1', credentials=credentials) 
    df= pd.read_gbq(sql_cte_return(PROJECT_ID, REGION, cte_name), project_id=project_id, dialect="standard", credentials=credentials)

    # Fixing Datatypes
    for col in date_col_list:
        df[col] = pd.to_datetime(df[col])

    return df

# Targeting project we want to be observing
PROJECT_ID = "checkmate-453316"
REGION = "region-eu"

df_jobs = load_data(PROJECT_ID, REGION, "cte_jobs_base", ["job_created_date", "job_created_month"])  
df_user = load_data(PROJECT_ID, REGION, "cte_user_level_aggregate", ["job_created_date"])            

app = Dash(__name__)
server = app.server

app.layout = html.Div([

    html.Div([
        html.Div([
                html.Div([
                    html.H1([f"BigQuery Data Processing Monitor"], style={
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
    ], className="filter-outer-div",  style={"width": "45%", "marginRight": "2%"}),

    # User Email block
    html.Div([
        html.H4("User Email", style={'margin': '0', 'paddingRight': '8px'}),
        dcc.Dropdown(
            id='user-email-dropdown',
            options=generate_dropdown_options(df_user['user_email'].dropna().unique()),
            multi=True,
            placeholder="Select Users",
            className="select-value",
            style={"width": "94%"}
        )
    ], className="filter-outer-div",  style={"flex": 1, "marginRight": "2%"}),

    # Metric block
    html.Div([
        html.H4("Metric", style={'margin': '0', 'paddingRight': '8px'}),
        dcc.Dropdown(
            id='metric-dropdown',
            options=generate_dropdown_options(df_user.select_dtypes(include=['number']).columns.tolist()),
            multi=False,
            placeholder="Select Metric",
            className="select-value",
            style={"width": "94%"}
        )
    ], className="filter-outer-div",  style={"flex": 1, "marginRight": "2%"}),

], style={'display': 'flex', 'width': '100%'})  

    ], className="div-filler-outer"),
    html.Br(),


    html.Div([
        html.Div(id="kpi-tiles", 
        style={
            "display": "flex", 
            "flexWrap": "wrap", 
            "justifyContent": "center", 
            "gap": "10px", 
            "marginBottom": "10px"}
        ),

        dcc.Graph(id="interactive-figure"),
    ], className="div-filler-outer"),

    html.Br(),

    html.Div([

        html.Div([
            html.Div([
                html.H3("Query Jobs Processing Over", style={"padding": "0rem 0rem", "marginLeft": "20px"}),  
                html.H3(id="output-box-data-processed",  style={"padding": "0rem 0rem", "marginLeft": "10px"}),
                html.H3("GB", style={"padding": "0rem 0rem"}),  
            ], style={"display": "flex", "alignItems": "center"}),
                    
            html.Div([
                dcc.Input(id="input-box-data-processed", type="number", placeholder="Enter processing filter (in GB)", style={"marginRight": "10px"}),
                html.Button("Download Table", id="download-btn", style={"marginRight": "10px"}),
                dcc.Download(id="download-component")
            ], style={"display": "flex", "alignItems": "center"})
        ], className="filter-outer-div", style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"}),


        dash_table.DataTable(
            id='interactive-filter-table',
            columns=[{"name": prettify_label(i), "id": i} for i in df_jobs.columns],
            page_size=10,
            page_action="native",
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
        ),
    ], className="div-filler-outer"),

],
)

@callback(
    Output("interactive-figure", "figure"),
    Output("interactive-filter-table", "data"),
    Output("interactive-filter-table", "columns"),
    Output("kpi-tiles", "children"),
    Output("output-box-data-processed", "children"),
    [
     Input("date-range-picker", "start_date"),
     Input("date-range-picker", "end_date"),
     Input("user-email-dropdown", "value"),
     Input("metric-dropdown", "value"),
     Input("input-box-data-processed", "value"),
     ]
)

def refresh_data(start_date, end_date, selected_user_email, selected_metric, data_input_filter):

    #------------------------------------------------------------------------------------
    # Get Date Boundaries for current month and previous month
    date_boundary_dict = get_month_boundaries()
    #------------------------------------------------------------------------------------

    # Current Month Fixed Period
    df_user_current_month = data_filters(
        df_user, 
        date_boundary_dict.get("current_month_start"), 
        date_boundary_dict.get("current_month_end"), 
        True, 
        selected_user_email
    )

    # Previous Month Fixed Period
    df_user_previous_month = data_filters(
        df_user,
        date_boundary_dict.get("previous_month_start"),
        date_boundary_dict.get("previous_month_end"),
        True,
        selected_user_email
    )

    # Dataframes filtering according to DatePicker Selection inside Dash Application
    df_user_filtered = data_filters(df_user, start_date, end_date, False, selected_user_email)
    df_jobs_filtered = data_filters(df_jobs, start_date, end_date, False, selected_user_email).sort_values(by=["job_creation_dt"], ascending=False) 

    # Filtering jobs table according to input box value
    if data_input_filter is not None:
        df_jobs_filtered = df_jobs_filtered[df_jobs_filtered["total_gigabytes_billed"] >= data_input_filter]

    # Defaults values when Dash Application Opens
    if selected_metric is None:
        selected_metric = "total_gigabytes_billed"

    # Updating KPI Tiles
    kpi_tiles = create_kpi_tiles(df_user_filtered, df_user_current_month)

    #------------------------------------------------------------------------------------

    # Creating Interactive Chart To Respond to Dropdown Filters
    df_interactive_aggregate = df_user_filtered.groupby(["job_created_date"], as_index=False)[selected_metric].sum()

    interactive_fig = px.bar(
        df_interactive_aggregate,
        x="job_created_date",
        y=selected_metric,
        color_discrete_sequence=["#4285f4"]
    )

    interactive_layout = {
        "height": 250,
        "plot_bgcolor": "white",
        "paper_bgcolor": "white",
        "font": {
            "family":"trebuc",           
            "color": "black"
        },
        "xaxis": {
            "title": None ,
            "color": "black",
            "gridcolor": "#d9dbdb",
        },
        "yaxis": {
            "title": f"{prettify_label(selected_metric)}",  
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
            "text": f"{prettify_label(selected_metric)}",  
            "x": 0.075,
            "xanchor": "left",
            "yanchor": "top",
            "y": 0.95,
            "font": {"size": 20, "color": "black"}
        },
        "margin": {
            "l": 60,
            "r": 50,
            "t": 50,
            "b": 50
        },
    }

    interactive_fig.update_layout(transition_duration=300)
    interactive_fig.update_layout(**interactive_layout)

    #------------------------------------------------------------------------------------

    # Creating Filterable Table Containing Detailed Job Data
    df_jobs_present = df_jobs_filtered[
            ["job_creation_dt",
            "project_id",
            "user_email",
            "job_id",
            "job_type",
            "statement_type",
            "priority",
            "cache_hit",
            "total_slot_seconds",
            "total_gigabytes_billed",
            "query_cost_usd",]
    ]
    job_table_data = df_jobs_present.to_dict("records")
    job_table_columns = [{"name": prettify_label(col), "id": col} for col in df_jobs_present.columns]

    #------------------------------------------------------------------------------------

    return interactive_fig, job_table_data, job_table_columns, kpi_tiles, data_input_filter

@callback(
    Output("download-component", "data"),
    Input("download-btn", "n_clicks"),
    State("interactive-filter-table", "data"),
    prevent_initial_call=True
)
def download_table(n_clicks, table_data):
    df_download = pd.DataFrame(table_data)
    return dcc.send_data_frame(df_download.to_csv, filename="bq_resource_usage.csv", index=False)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
