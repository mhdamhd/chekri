import dash
from dash import dcc, html, Input, Output, State, ALL, ctx
import dash_bootstrap_components as dbc
import pandas as pd
import io
import base64
from collections import defaultdict
import plotly.graph_objs as go
from google.oauth2 import service_account
from googleapiclient.discovery import build
import re
from googleapiclient.discovery import build
from googleapiclient.http import HttpRequest
# Initialize the Dash app with a modern theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME])

# Set the path to your service account JSON file
SERVICE_ACCOUNT_FILE = './service_account_key.json'

# Define custom styles
CARD_STYLE = {
    "box-shadow": "0 4px 15px 0 rgba(0, 0, 0, 0.1)",
    "margin-bottom": "24px",
    "border-radius": "12px",
    "border": "none",
    "transition": "transform 0.3s ease-in-out",
}

HEADER_STYLE = {
    "background": "linear-gradient(120deg, #1e3c72 0%, #2a5298 100%)",
    "padding": "30px",
    "margin-bottom": "30px",
    "border-radius": "15px",
    "box-shadow": "0 5px 15px rgba(0,0,0,0.1)",
    "color": "#fff",
}

BUTTON_STYLE = {
    "border-radius": "30px",
    "font-weight": "bold",
    "text-transform": "uppercase",
    "letter-spacing": "1px",
    "transition": "all 0.3s ease",
}

# Initial PC list with default Google Sheets URLs
initial_pcs = [
    {"name": "PC 1", "link": "https://docs.google.com/spreadsheets/d/1iNnPAcueulelAKeAFVHBV07EdAt8GnT_4duCU1S2XH0/edit?gid=0#gid=0"},
    {"name": "PC 9", "link": "12ZOSMc6tMeMDclTrywUb3FQ0bn-oss2l"},
    {"name": "PC 12", "link": "12NW85s4xxMKzmI8Qh6aMyEYhxnpr3_E6"},
    {"name": "PC 17", "link": "1224rmKmIBXk0HcCKfbMdToMP6av31W1e"},
    {"name": "PC 19", "link": "128HWbGhkK8xkGrWRAOD5RZaARG6gMXZc"},
    {"name": "PC 26", "link": "11ltLVK99sVGgsxR7Z9wEkZTspsCGqILs"},
    {"name": "PC 27", "link": "11cO9HVSoLF-Uzf8HT7_m49xyXIB8A-9b"},
    {"name": "PC 28", "link": "11au7tZ_YQWMb2ub7Is1ubp9aQMyeGHWM"},
    {"name": "PC 29", "link": "11IEei__yDg9nj8S7CbGOpwmZw01-qIJH"},
    {"name": "PC 37", "link": "133QY2xr3TwjWwuO7HGgcPRbudY9fmtbH"},
    {"name": "PC 38", "link": "11AxzJUtLZ11ks1NIWwRyowvXVxdK-0-g"},
    {"name": "PC 39", "link": "1-iTn_6gksKPAZFxBYg8FoLgfwW7qS9gn"},
    {"name": "PC 40", "link": "1--A5VrFI4QsyiGNOsWFcHkT0bWYNobCd"},
    {"name": "PC 41", "link": "119Sikg_fcPZsvLXnMLak7-XvFpuyX_lP"},
    {"name": "PC 42", "link": "111IkXCGkjhjeveCjrTVCkh2_apphYbuS"},
    {"name": "PC 43", "link": "13H4iNd37GUVG-l2YKQ-9Wz5A8TJy2Eks"},
    {"name": "PC 44", "link": "13PsdegXt8lElP4MgsGi_ZzTb5PXBhE2_"},
    {"name": "PC 45", "link": "13fd-rq-6fI1uQBPDzuWykN_M8M-qZe0K"},
    {"name": "PC 46", "link": "13WqgEtTCuzuSBN2U0cNa_e0r7nwuYTtZ"},
    {"name": "PC 47", "link": "13m1OqjkOk2eKCi7oHudYlN_BJpzGUcF0"},
]

def register_callbacks(app):

    def create_pc_row(name, link, index):
        return dbc.Row([
            dbc.Col(dbc.Checkbox(id={'type': 'pc-checkbox', 'index': index}, value=False), width=1),
            dbc.Col(dbc.Input(id={'type': 'pc-name', 'index': index}, value=name, placeholder="PC Name"), width=2),
            dbc.Col(dbc.Input(id={'type': 'pc-link', 'index': index}, value=link, placeholder="Google Sheet URL or ID"), width=7),
            dbc.Col(dbc.Button("Delete", id={'type': 'delete-pc', 'index': index}, color="danger", size="sm"), width=2),
        ], className="mb-2")

    # App layout
    app.layout = dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1("RPA Assignment Dashboard", className="display-4 text-center mb-3"),
                html.P("Distribute maids across Google Sheets based on priority.", className="lead text-center"),
            ], width=12)
        ], style=HEADER_STYLE),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H4("Maid Distribution", className="text-white"), className="bg-primary"),
                    dbc.CardBody([
                        dcc.Upload(
                            id='upload-maid-data',
                            children=html.Div([
                                html.I(className="fas fa-file-excel me-2"),
                                'Drag and Drop or ',
                                html.A('Select Maid Excel File', className="text-primary")
                            ]),
                            style={
                                'width': '100%',
                                'height': '60px',
                                'lineHeight': '60px',
                                'borderWidth': '2px',
                                'borderStyle': 'dashed',
                                'borderRadius': '15px',
                                'textAlign': 'center',
                                'margin': '20px 0',
                                'cursor': 'pointer',
                            },
                            multiple=False
                        ),
                        html.Div(id='maid-upload-status', className="mt-3"),
                        html.Div(id='pc-container', children=[
                            dbc.Row([
                                dbc.Col(dbc.Button("Select All", id="select-all-button", color="info", className="mb-3"), width=3),
                                dbc.Col(dbc.Button("Add New PC", id="add-pc-button", color="success", className="mb-3"), width=3),
                                dbc.Col(dbc.Button("Undo", id="undo-button", color="warning", className="mb-3", disabled=True), width=3),
                            ]),
                            html.Div(id='pc-list', children=[create_pc_row(pc['name'], pc['link'], i) for i, pc in enumerate(initial_pcs)]),
                        ]),
                        dbc.Button("Distribute Maids", id="btn-distribute-maids", color="primary", className="w-100 mt-3", size="lg", style=BUTTON_STYLE),
                        dbc.Spinner(html.Div(id="maid-distribution-output"), color="primary", type="border", spinnerClassName="mt-3"),
                    ])
                ], style=CARD_STYLE),
            ], width=12),
        ]),
        dcc.Store(id='pc-data-store', data=initial_pcs),
        dcc.Store(id='undo-store', data=[]),
    ], fluid=True, className="px-4 py-5 bg-light")

    # Helper function to extract Google Sheet ID from either URL or direct ID
    def extract_sheet_id(link):
        if re.match(r'^[a-zA-Z0-9-_]+$', link):  # Direct Sheet ID format
            return link
        match = re.search(r"/d/([a-zA-Z0-9-_]+)", link)
        return match.group(1) if match else None

    # Parse uploaded file
    def parse_contents(contents, filename):
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            if 'xlsx' in filename:
                df = pd.read_excel(io.BytesIO(decoded))
            elif 'csv' in filename:
                df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            else:
                return html.Div(['Please upload an Excel or CSV file.'])
            return df
        except Exception as e:
            print(e)
            return html.Div(['There was an error processing this file.'])

    # Sort maids based on priority
    def prioritize_maids(df):
        if 'Priority number' not in df.columns:
            raise KeyError("The column 'Priority number' is missing from the file.")
        return df.sort_values('Priority number')

    # Filter out blank entries
    def filter_blank_entries(df):
        missing_columns = [col for col in ['Request ID', 'Housemaid Name'] if col not in df.columns]
        if missing_columns:
            raise KeyError(f"The following required columns are missing: {', '.join(missing_columns)}")
        return df.dropna(subset=['Request ID', 'Housemaid Name'])

    # Distribute maids to PCs
    def distribute_maids(df, num_pcs):
        df_sorted = df  # Keep the original order from the uploaded Excel
        distribution = {f"PC_{i+1}": [] for i in range(num_pcs)}
        priorities = df_sorted['Priority number'].unique()
        pc_index = 0
        for priority in priorities:
            priority_maids = df_sorted[df_sorted['Priority number'] == priority]
            for _, maid in priority_maids.iterrows():
                maid_info = {
                    'Priority number': maid['Priority number'],  # Add Priority Number
                    'id': maid['Request ID'],
                    'name': maid['Housemaid Name'],
                    'Nationality': maid['Housemaid Nationality']  # Add Nationality
                }
                distribution[f"PC_{pc_index + 1}"].append(maid_info)
                pc_index = (pc_index + 1) % num_pcs
        return distribution

    HttpRequest.DEFAULT_HTTP_TIMEOUT = 300  # Set to 300 seconds (5 minutes)

    # Write data to Google Sheet
    def write_to_google_sheet(sheet_id, data):
        try:
            creds = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            service = build('sheets', 'v4', credentials=creds)
            service.spreadsheets().values().clear(spreadsheetId=sheet_id, range='A1:Z').execute()
            body = {'values': [data.columns.tolist()] + data.values.tolist()}
            result = service.spreadsheets().values().update(spreadsheetId=sheet_id, range='A1', valueInputOption='USER_ENTERED', body=body).execute()
            print(f"{result.get('updatedCells')} cells updated.")
            return True
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    # Create a distribution chart
    def create_distribution_chart(distribution):
        pc_names = list(distribution.keys())
        maid_counts = [len(maids) for maids in distribution.values()]
        fig = go.Figure(data=[go.Bar(
            x=pc_names,
            y=maid_counts,
            marker_color='rgba(30, 60, 114, 0.7)',
            text=maid_counts,
            textposition='auto',
        )])
        fig.update_layout(
            title="Maid Distribution Across PCs",
            xaxis_title="PC",
            yaxis_title="Number of Maids",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )
        return fig

    # Generate detailed statistics
    def generate_detailed_statistics(distribution):
        total_maids = sum(len(maids) for maids in distribution.values())
        avg_maids_per_pc = total_maids / len(distribution)
        priority_distribution = defaultdict(int)
        for maids in distribution.values():
            for maid in maids:
                priority_distribution[maid['Priority number']] += 1
        stats = [
            html.H6("Detailed Statistics:"),
            html.P(f"Total Maids: {total_maids}"),
            html.P(f"Average Maids per PC: {avg_maids_per_pc:.2f}"),
            html.H6("Distribution by Priority:"),
            html.Ul([html.Li(f"Priority {priority}: {count} maids") for priority, count in sorted(priority_distribution.items())])
        ]
        return stats

    # Callbacks for managing file uploads and PC selection
    @app.callback(
        Output('maid-upload-status', 'children'),
        Input('upload-maid-data', 'contents'),
        State('upload-maid-data', 'filename')
    )
    def update_maid_upload_status(contents, filename):
        if contents is not None:
            return html.Div([
                html.I(className="fas fa-check-circle text-success me-2"),
                f"File uploaded successfully: {filename}"
            ], className="mt-2 alert alert-success")
        return ""

    @app.callback(
        [Output('pc-list', 'children'),
        Output('pc-data-store', 'data'),
        Output('undo-store', 'data'),
        Output('undo-button', 'disabled')],
        [Input('add-pc-button', 'n_clicks'),
        Input({'type': 'delete-pc', 'index': ALL}, 'n_clicks'),
        Input('undo-button', 'n_clicks')],
        [State('pc-list', 'children'),
        State('pc-data-store', 'data'),
        State('undo-store', 'data')],
        prevent_initial_call=True
    )
    def manage_pcs(add_clicks, delete_clicks, undo_clicks, current_pcs, stored_data, undo_data):
        ctx_msg = ctx.triggered_id
        if not ctx_msg:
            raise dash.exceptions.PreventUpdate

        if ctx_msg == 'add-pc-button':
            new_index = len(current_pcs)
            new_pc = create_pc_row("", "", new_index)
            current_pcs.append(new_pc)
            stored_data.append({"name": "", "link": ""})
            undo_data.append(('add', new_index))
        elif isinstance(ctx_msg, dict) and ctx_msg.get('type') == 'delete-pc':
            delete_index = ctx_msg['index']
            deleted_pc = current_pcs.pop(delete_index)
            deleted_data = stored_data.pop(delete_index)
            undo_data.append(('delete', delete_index, deleted_pc, deleted_data))
            current_pcs = [create_pc_row(stored_data[i]['name'], stored_data[i]['link'], i) for i in range(len(stored_data))]
        elif ctx_msg == 'undo-button' and undo_data:
            last_action = undo_data.pop()
            if last_action[0] == 'add':
                current_pcs.pop()
                stored_data.pop()
            elif last_action[0] == 'delete':
                current_pcs.insert(last_action[1], last_action[2])
                stored_data.insert(last_action[1], last_action[3])
                current_pcs = [create_pc_row(stored_data[i]['name'], stored_data[i]['link'], i) for i in range(len(stored_data))]

        return current_pcs, stored_data, undo_data, len(undo_data) == 0

    @app.callback(
        Output({'type': 'pc-checkbox', 'index': ALL}, 'value'),
        Input('select-all-button', 'n_clicks'),
        State({'type': 'pc-checkbox', 'index': ALL}, 'value'),
        prevent_initial_call=True
    )
    def toggle_all_checkboxes(n_clicks, current_states):
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate
        
        all_checked = all(current_states)
        return [not all_checked] * len(current_states)

    # Callback for distributing maids
    @app.callback(
        Output("maid-distribution-output", "children"),
        Input("btn-distribute-maids", "n_clicks"),
        [State("upload-maid-data", "contents"),
        State("upload-maid-data", "filename"),
        State({'type': 'pc-checkbox', 'index': ALL}, 'value'),
        State({'type': 'pc-name', 'index': ALL}, 'value'),
        State({'type': 'pc-link', 'index': ALL}, 'value')],
        prevent_initial_call=True
    )
    def process_maid_distribution(n_clicks, contents, filename, pc_checks, pc_names, pc_links):
        if contents is None:
            return html.Div("Please upload a file first.", className="alert alert-warning")

        df = parse_contents(contents, filename)
        if not isinstance(df, pd.DataFrame):
            return html.Div("Error processing the file.", className="alert alert-danger")

        selected_pcs = [{"name": name, "link": extract_sheet_id(link)} for name, link, checked in zip(pc_names, pc_links, pc_checks) if checked and link.strip()]
        if not selected_pcs:
            return html.Div("Please select at least one PC with a valid Google Sheet URL or ID.", className="alert alert-warning")

        try:
            df_filtered = filter_blank_entries(df)
            # df_prioritized = prioritize_maids(df_filtered)
            df_prioritized = df_filtered
        except KeyError as e:
            return html.Div(str(e), className="alert alert-danger")

        distribution = distribute_maids(df_prioritized, len(selected_pcs))

        summary = html.Div([
            html.H5("Maid Distribution Summary:", className="mt-4 mb-3"),
            html.Ul(id="distribution-results", className="list-group"),
            dcc.Graph(figure=create_distribution_chart(distribution), className="mt-4"),
            html.Div(generate_detailed_statistics(distribution), className="mt-4")
        ])

        results = []
        for i, ((pc_key, maids), pc) in enumerate(zip(distribution.items(), selected_pcs)):
            # Include the additional columns in the DataFrame before writing to Google Sheets
            df_to_write = pd.DataFrame(maids)[['Priority number', 'id', 'name', 'Nationality']]  # Include new columns
            success = write_to_google_sheet(pc['link'], df_to_write)
            status = "Success" if success else "Failed"
            results.append(html.Li(f"{pc['name']} ({pc_key}): {len(maids)} maids - Writing {status}", 
                                className=f"list-group-item {'list-group-item-success' if success else 'list-group-item-danger'}"))

        summary.children[1].children = results

        # Provide a CSV summary for download
        df_summary = pd.DataFrame([(pc['name'], len(maids)) for (_, maids), pc in zip(distribution.items(), selected_pcs)], columns=['PC Name', 'Number of Maids'])
        csv_string = df_summary.to_csv(index=False, encoding='utf-8')
        csv_string = "data:text/csv;charset=utf-8," + csv_string.replace('\n', '%0A')
        
        download_button = html.A(
            html.Button('Download Distribution Summary', className='btn btn-primary mt-3'),
            href=csv_string,
            download="maid_distribution_summary.csv",
            target="_blank"
        )

        summary.children.append(download_button)

        return summary


if __name__ == '__main__':
    app.run_server(debug=True, port=7121)