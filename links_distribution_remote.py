import dash
from dash import dcc, html, Input, Output, State, ALL, ctx
import dash_bootstrap_components as dbc
import pandas as pd
import io
import base64
from google.oauth2 import service_account
from googleapiclient.discovery import build
import re

# Initialize the Dash app with Bootstrap styling
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Set the path to your service account JSON file
SERVICE_ACCOUNT_FILE = './service_account_key.json'

# Initial PCs with sample Google Sheets URLs or IDs
initial_pcs = [
    {"name": "PC 1", "link": "https://docs.google.com/spreadsheets/d/1iNnPAcueulelAKeAFVHBV07EdAt8GnT_4duCU1S2XH0/edit?gid=0#gid=0"},
    {"name": "PC 2", "link": "https://docs.google.com/spreadsheets/d/1-htj-EWu2x7GcKWzTKSfUPemBoYLDP68g0vIgEzjLdM/edit?gid=0#gid=0"},
    {"name": "PC 3", "link": "https://docs.google.com/spreadsheets/d/1MP4hoas3522DovdAJo9xIEU62KLX-azajJ9LI07mK2U/edit?gid=0#gid=0"},
    {"name": "PC 4", "link": "https://docs.google.com/spreadsheets/d/1lNcsXdWQ2y2QKNexgLk_ZjBHOaXEcMXBNtmSBw_dtKs/edit?gid=0#gid=0"},
    # Add more as needed
]

# Custom styles
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

# Helper function to create dynamic PC rows
def create_pc_row(name, link, index):
    return dbc.Row([
        dbc.Col(dbc.Checkbox(id={'type': 'pc-checkbox', 'index': index}, value=False), width=1),
        dbc.Col(dbc.Input(id={'type': 'pc-name', 'index': index}, value=name, placeholder="PC Name"), width=3),
        dbc.Col(dbc.Input(id={'type': 'pc-link', 'index': index}, value=link, placeholder="Google Sheet URL or ID"), width=6),
        dbc.Col(dbc.Button("Delete", id={'type': 'delete-pc', 'index': index}, color="danger", size="sm"), width=2),
    ], className="mb-2")

# App layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Login Link Distribution", className="display-4 text-center mb-3"),
            html.P("Distribute login links across Google Sheets (PCs).", className="lead text-center"),
        ], width=12)
    ], style=HEADER_STYLE),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H4("Distribute Links to PCs", className="text-white"), className="bg-primary"),
                dbc.CardBody([
                    dcc.Tabs(id="input-tabs", value='upload-tab', children=[
                        dcc.Tab(label='Upload Excel', value='upload-tab', children=[
                            dcc.Upload(
                                id='upload-login-links',
                                children=html.Div(['Drag and Drop or ', html.A('Select Excel File')]),
                                style={
                                    'width': '100%', 'height': '60px', 'lineHeight': '60px', 'borderWidth': '2px',
                                    'borderStyle': 'dashed', 'borderRadius': '10px', 'textAlign': 'center', 'margin': '10px'
                                },
                                multiple=False
                            ),
                            html.Div(id='upload-status', className="mt-2")
                        ]),
                        dcc.Tab(label='Manual Input', value='manual-tab', children=[
                            dcc.Textarea(
                                id='manual-login-links',
                                placeholder='Enter login links, one per line',
                                style={'width': '100%', 'height': '200px'}
                            ),
                            html.Div(id='manual-input-status', className="mt-2")
                        ]),
                    ]),
                    html.Hr(),
                    html.H5("Select PCs to Distribute Links"),
                    dbc.Row([
                        dbc.Col(dbc.Button("Select All", id="select-all-button", color="info", className="mb-3"), width=3),
                        dbc.Col(dbc.Button("Add New PC", id="add-pc-button", color="success", className="mb-3"), width=3),
                        dbc.Col(dbc.Button("Undo", id="undo-button", color="warning", className="mb-3", disabled=True), width=3),
                    ]),
                    html.Div(id='pc-list', children=[create_pc_row(pc['name'], pc['link'], i) for i, pc in enumerate(initial_pcs)]),
                    dbc.Button("Distribute Links", id="distribute-button", color="primary", className="w-100 mt-3", size="lg"),
                    dbc.Spinner(html.Div(id="distribution-output"), color="primary", type="border", spinnerClassName="mt-3"),
                ])
            ], style=CARD_STYLE),
        ], width=12),
    ]),
    dcc.Store(id='pc-data-store', data=initial_pcs),
    dcc.Store(id='undo-store', data=[]),
], fluid=True, className="px-4 py-5 bg-light")

def register_callbacks(app):

    def parse_excel(contents, filename):
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            if 'xlsx' in filename:
                df = pd.read_excel(io.BytesIO(decoded))
                # Replace NaN values with empty strings
                df.fillna("", inplace=True)
                return df['Login link'].tolist()  # Convert the 'Login link' column to a list
            return None
        except Exception as e:
            print(e)
            return None

    # Helper function to extract links from text input
    def parse_manual_input(text):
        return [line.strip() for line in text.split('\n') if line.strip()]

    # Helper function to distribute links evenly among PCs
    def distribute_links(links, num_pcs):
        distribution = {f"PC_{i+1}": [] for i in range(num_pcs)}
        for i, link in enumerate(links):
            distribution[f"PC_{(i % num_pcs) + 1}"].append(link)
        return distribution

    def extract_sheet_id(link):
        # Regular expression to extract Google Sheet ID from the link
        match = re.search(r"/d/([a-zA-Z0-9-_]+)", link)
        return match.group(1) if match else link  # Return ID if found, otherwise return link (in case direct ID is provided)

    def write_to_google_sheet(sheet_id, data):
        creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
        service = build('sheets', 'v4', credentials=creds)

        # Clear the existing data and formatting in the sheet
        service.spreadsheets().values().clear(spreadsheetId=sheet_id, range='A1:Z').execute()

        # Write headers for the new data
        headers = [['Login link', 'Status']]  # First row as headers
        body = {'values': headers + data}

        # Append the data starting from A1
        result = service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range='A1',
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()

        return result


    # Callbacks to manage PC list (Add, Delete, Undo)
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

    @app.callback(
        Output("distribution-output", "children"),
        Input("distribute-button", "n_clicks"),
        [State("input-tabs", "value"),  # Detect which tab is active (Excel or Manual)
        State("upload-login-links", "contents"),
        State("upload-login-links", "filename"),
        State("manual-login-links", "value"),
        State({'type': 'pc-checkbox', 'index': ALL}, 'value'),
        State({'type': 'pc-name', 'index': ALL}, 'value'),
        State({'type': 'pc-link', 'index': ALL}, 'value')],
        prevent_initial_call=True
    )
    def process_maid_distribution(n_clicks, active_tab, contents, filename, manual_links, pc_checks, pc_names, pc_links):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate

        # Determine which input to use based on the active tab
        links = []
        if active_tab == 'upload-tab':
            if contents is None:
                return html.Div("Please upload an Excel file.", className="alert alert-warning")
            # Get the login links from the Excel file
            links = parse_excel(contents, filename)
            # Check if 'links' is a Pandas Series and convert to a list if necessary
            if isinstance(links, pd.Series):
                links = links.tolist()
        elif active_tab == 'manual-tab':
            if not manual_links.strip():
                return html.Div("Please enter some login links manually.", className="alert alert-warning")
            # Get the login links from the manual input
            links = parse_manual_input(manual_links)

        # Filter out empty or whitespace-only links
        filtered_links = [link for link in links if link and link.strip()]

        # Check if there are any valid links left after filtering
        if len(filtered_links) == 0:
            return html.Div("No valid login links found.", className="alert alert-danger")

        # Process selected PCs
        selected_pcs = [{"name": name, "link": link} for name, link, checked in zip(pc_names, pc_links, pc_checks) if checked and link.strip()]
        if not selected_pcs:
            return html.Div("Please select at least one PC with a valid Google Sheet URL or ID.", className="alert alert-warning")

        # Distribute the links in round-robin fashion across the selected PCs
        num_pcs = len(selected_pcs)
        distribution = {pc['name']: [] for pc in selected_pcs}  # Initialize dictionary to hold links for each PC

        for i, link in enumerate(filtered_links):
            # Assign each link to a PC in a round-robin manner
            pc_name = selected_pcs[i % num_pcs]['name']
            distribution[pc_name].append(link)

        # Write distributed links to each selected PC
        for pc in selected_pcs:
            # Prepare the data for the current PC, leaving the Status column empty
            pc_data = [[link, ""] for link in distribution[pc['name']]]

            # Extract the sheet ID from the provided Google Sheet link
            sheet_id = extract_sheet_id(pc['link'])

            # Write the data to the Google Sheet (clear, write headers, then append the data)
            write_to_google_sheet(sheet_id, pc_data)

        return html.Div("Links distributed successfully.")


    @app.callback(
        Output('upload-status', 'children'),
        Input('upload-login-links', 'contents'),
        State('upload-login-links', 'filename')
    )
    def update_upload_status(contents, filename):
        if contents is not None:
            return html.Div([
                html.I(className="fas fa-check-circle text-success me-2"),
                f"File uploaded successfully: {filename}"
            ], className="mt-2 alert alert-success")
        return ""

if __name__ == '__main__':
    app.run_server(debug=True)
