import base64
import io
import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
from priorities import african_countries


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])



app.layout = dbc.Container([
    html.H2("Maid Prioritization Statistics"),
    dcc.Upload(
        id='breakdown-upload-data',
        children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
        style={
            'width': '100%', 'height': '60px', 'lineHeight': '60px',
            'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
            'textAlign': 'center', 'margin': '10px'
        }
    ),
    html.Div(id='breakdown-output-data-upload'),
    dash_table.DataTable(id='breakdown-stats-table', style_table={'overflowX': 'auto'}),
    dbc.Button("Download Table as Excel", id="breakdown-download-button", color="primary", className="mt-3"),
    dcc.Download(id="breakdown-download-excel")
], fluid=True)
layout = app.layout

def register_callbacks(app):
        
    def parse_and_filter_data(contents, filename, mv_urgency_days, last_day_in_country):
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        df = pd.read_excel(io.BytesIO(decoded), sheet_name='Combined')
        
        if df is None:
            return None, None
    
        # Define conditions with new property labels
        conditions = [
            ("MV", (df['Housemaid Type'] == 'MV')),
            ("CC landed in dubai", (df['Priority number'].isin([6, 7, 8, 10, 11, 14, 15]) & (df['Housemaid Type'] == 'CC'))),
            ("CC in exit Filipina", (df['Priority number'].isin([3, 5, 12, 17, 23]) &
                                    (df['Housemaid Nationality'] == 'Filipina') &
                                    (df['Housemaid Type'] == 'CC'))),
            ("CC in exit Ethiopian", (df['Priority number'].isin([5, 9, 19, 21, 23]) &
                                    (df['Housemaid Nationality'] == 'Ethiopian') &
                                    (df['Housemaid Type'] == 'CC'))),
            ("CC in exit African", (df['Priority number'].isin([5, 18, 20, 22, 23]) &
                                    (df['Housemaid Nationality'].isin(african_countries)) &
                                    (df['Housemaid Type'] == 'CC'))),
            ("CC in exit Other", (df['Priority number'].isin([5, 23]) &
                                    (~df['Housemaid Nationality'].isin(['Filipina', 'Ethiopian'] + african_countries)) &
                                    (df['Housemaid Type'] == 'CC'))),
            ("LAWP Ethiopian", (df['Priority number'] == 16) & (df['Housemaid Nationality'] == 'Ethiopian')),
            ("LAWP Indian", (df['Priority number'] == 16) & (df['Housemaid Nationality'] == 'Indian')),
            ("LAWP Other", (df['Priority number'] == 16) & (~df['Housemaid Nationality'].isin(['Ethiopian', 'Indian'])))
        ]

        # Assign "New Property" column based on conditions
        df['New Property'] = None  # Initialize column
        for label, condition in conditions:
            df.loc[condition, 'New Property'] = label

        # Count stats with Approved/Rejected split
        stats = {}
        for label, _ in conditions:
            approved_count = len(df[(df['New Property'] == label) & (df['Docs status'] == 'Approved')])
            rejected_count = len(df[(df['New Property'] == label) & (df['Docs status'] == 'Rejected')])
            total_count = approved_count + rejected_count
            stats[label] = {'Approved': approved_count, 'Rejected': rejected_count, 'Total': total_count}

        stats['Total'] = {
            'Approved': sum(item['Approved'] for item in stats.values()),
            'Rejected': sum(item['Rejected'] for item in stats.values()),
            'Total': sum(item['Total'] for item in stats.values())
        }
        return df, stats

    @app.callback(
        Output('breakdown-stats-table', 'data'),
        Output('breakdown-stats-table', 'columns'),
        Input('breakdown-upload-data', 'contents'),
        State('breakdown-upload-data', 'filename')
    )
    def update_output(contents, filename):
        if contents is None:
            return [], []

        mv_urgency_days = 7  # Example value for mv_urgency_days
        last_day_in_country = 10  # Example value for last_day_in_country
        
        df, stats = parse_and_filter_data(contents, filename, mv_urgency_days, last_day_in_country)
        if stats is None:
            return [], []

        # Prepare stats table data and columns with Approved/Rejected breakdown
        columns = [
            {"name": "Category", "id": "Category"},
            {"name": "Approved", "id": "Approved"},
            {"name": "Rejected", "id": "Rejected"},
            {"name": "Total", "id": "Total"}
        ]
        data = [{"Category": k, "Approved": v['Approved'], "Rejected": v['Rejected'], "Total": v['Total']} for k, v in stats.items()]
        
        return data, columns

    # Callback to download the displayed table as Excel
    @app.callback(
        Output("breakdown-download-excel", "data"),
        Input("breakdown-download-button", "n_clicks"),
        State('breakdown-upload-data', 'contents'),
        State('breakdown-upload-data', 'filename'),
        prevent_initial_call=True
    )
    def download_table_as_excel(n_clicks, contents, filename):
        if contents is None:
            return None

        mv_urgency_days = 7  # Example value for mv_urgency_days
        last_day_in_country = 10  # Example value for last_day_in_country
        
        df, stats = parse_and_filter_data(contents, filename, mv_urgency_days, last_day_in_country)
        if stats is None:
            return None

        # Convert stats to DataFrame for download
        stats_df = pd.DataFrame([
            {"Type": k, "Mohre": v['Approved'], "AIO": v['Rejected'], "Total": v['Total']}
            for k, v in stats.items()
        ])
        
        # Export the DataFrame to Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            stats_df.to_excel(writer, index=False, sheet_name="Statistics")
        output.seek(0)

        return dcc.send_bytes(output.getvalue(), "Prioritization_Statistics.xlsx")

    if __name__ == '__main__':
        app.run_server(debug=True)
