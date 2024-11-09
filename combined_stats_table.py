import base64
import io
import dash
from dash import dcc, html, Input, Output, State, dash_table, callback_context
import dash_bootstrap_components as dbc
import pandas as pd
from priorities import african_countries

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    html.H2("Maid Prioritization Statistics"),
    
    # Quota input field
    dbc.Row([
        dbc.Col(html.Label("Quota We Have"), width="auto"),
        dbc.Col(dcc.Input(id="quota-input", type="number", value=100, style={"width": "100px"}), width="auto"),
    ], className="mb-3"),

    dcc.Upload(
        id='breakdown-upload-data',
        children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
        style={
            'width': '100%', 'height': '60px', 'lineHeight': '60px',
            'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
            'textAlign': 'center', 'margin': '10px'
        }
    ),
    html.Div(id='breakdown-upload-message'),
    
    # Checklist for filtering table categories
    dcc.Checklist(id="category-checklist", inline=False, style={'textAlign': 'left'}),
    html.Div(id="remaining-quota", style={"fontWeight": "bold", "margin-top": "5px", "margin-bottom": "5px"}),
    
    # Store to hold the original table data for filtering
    dcc.Store(id='original-table-data'),
    
    dash_table.DataTable(
        id='breakdown-stats-table', 
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '10px'},
        style_header={
            'backgroundColor': 'lightgrey',
            'fontWeight': 'bold'
        }
    ),
    
    # Download button with margin below
    dbc.Button("Download Table as Excel", id="breakdown-download-button", color="primary", className="mt-3", style={"margin-bottom": "50px"}),
    dcc.Download(id="breakdown-download-excel"),
    
    # Display remaining quota below the table
    
], fluid=True)
layout = app.layout

def register_callbacks(app):
    def parse_and_filter_data(contents, filename, mv_urgency_days, last_day_in_country):
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        try:
            df = pd.read_excel(io.BytesIO(decoded), sheet_name='Combined')
        except ValueError:
            df = pd.read_excel(io.BytesIO(decoded), sheet_name=0)

        if df is None:
            return None, None

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

        df['New Property'] = None
        for label, condition in conditions:
            df.loc[condition, 'New Property'] = label

        stats = {}
        for label, _ in conditions:
            approved_count = len(df[(df['New Property'] == label) & (df['Docs status'] == 'Approved')])
            rejected_count = len(df[(df['New Property'] == label) & (df['Docs status'] == 'Rejected')])
            total_count = approved_count + rejected_count
            stats[label] = {'Approved': approved_count, 'Rejected': rejected_count, 'Total': total_count}

        return df, stats

    @app.callback(
        Output('breakdown-stats-table', 'data'),
        Output('breakdown-stats-table', 'columns'),
        Output('breakdown-upload-message', 'children'),
        Output('category-checklist', 'options'),
        Output('category-checklist', 'value'),  # Default selected values
        Output('original-table-data', 'data'),  # Store original data
        Output('remaining-quota', 'children'),  # Display remaining quota
        Input('breakdown-upload-data', 'contents'),
        Input('category-checklist', 'value'),
        Input('quota-input', 'value'),  # Get the quota input
        State('breakdown-upload-data', 'filename'),
        State('original-table-data', 'data'),
        prevent_initial_call=True
    )
    def update_table(contents, selected_categories, quota, filename, original_data):
        trigger = callback_context.triggered[0]['prop_id'].split('.')[0]

        if trigger == 'breakdown-upload-data' and contents is not None:
            # Process file upload
            mv_urgency_days = 7
            last_day_in_country = 10
            
            df, stats = parse_and_filter_data(contents, filename, mv_urgency_days, last_day_in_country)
            if stats is None:
                return [], [], "Failed to process file. Please check the format.", [], [], [], ""

            columns = [
                {"name": "Type", "id": "Type"},
                {"name": "Mohre", "id": "Mohre"},
                {"name": "AIO", "id": "AIO"},
                {"name": "Total", "id": "Total"}
            ]
            data = [{"Type": k, "Mohre": v['Approved'], "AIO": v['Rejected'], "Total": v['Total']} for k, v in stats.items()]
            # Calculate the initial remaining quota
            total_aio = sum(item['AIO'] for item in data)
            print(f"quota: {quota}, total_aio: {total_aio}")
            remaining_quota = quota - total_aio
            # Calculate the initial total row and add it to data
            total_row = {
                "Type": "Total",
                "Mohre": sum(item['Mohre'] for item in data),
                "AIO": sum(item['AIO'] for item in data),
                "Total": sum(item['Total'] for item in data)
            }
            data.append(total_row)
                    
            # Exclude "Total" from checklist options
            options = [{"label": k, "value": k} for k in stats.keys()]
            default_values = [k for k in stats.keys()]  # Select all options by default

            message = "File successfully uploaded and processed."
            return data, columns, message, options, default_values, data, f"Remaining Quota: {remaining_quota}"

        elif trigger == 'category-checklist' and selected_categories is not None:
            # Filter original data based on selected categories
            filtered_data = [row for row in original_data if row['Type'] in selected_categories]
            
            # Calculate the dynamic total based on filtered data
            total_row = {
                "Type": "Total",
                "Mohre": sum(row['Mohre'] for row in filtered_data),
                "AIO": sum(row['AIO'] for row in filtered_data),
                "Total": sum(row['Total'] for row in filtered_data)
            }
            filtered_data.append(total_row)

            # Update remaining quota
            remaining_quota = quota - total_row["AIO"]

            return filtered_data, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, f"Remaining Quota: {remaining_quota}"

        elif trigger == 'quota-input':
            # Recalculate remaining quota based on current quota and total AIO in original data
            total_aio = sum(row['AIO'] for row in original_data if row['Type'] != "Total")
            remaining_quota = quota - total_aio
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, f"Remaining Quota: {remaining_quota}"
            return [], [], "No file uploaded.", [], [], [], ""
            
if __name__ == '__main__':
    app.run_server(debug=True)
