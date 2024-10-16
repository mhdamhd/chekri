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

NATIONALITY_RULES = {
    'Filipina': ['Filipina', 'Ethiopian'],
    'Ethiopian': ['Filipina', 'Ethiopian'],
    'Kenyan': ['Kenyan', 'Ethiopian'],
    'Nepali': ['Nepali','Filipina' ],
    'Ugandan': ['Ugandan', 'Filipina'],
    'Nigerian': ['Nigerian', 'Filipina'],
    'Sri Lankan': ['Sri Lankan', 'Filipina'],
    'Myanmarese': ['Myanmarese'],
    'Uzbekistani': ['Uzbekistani'],
    'Indian': ['Indian'],
    'Spanish': ['Spanish'],
    'Afghan': ['Afghan', 'Filipina'],
    'Cameroonian': ['Cameroonian', 'Filipina'],
    'Colombian': ['Colombian', 'Filipina'],
    'Georgian': ['Georgian', 'Filipina'],
    'German': ['German'],
    'Indonesian': ['Indonesian', 'Filipina'],
    'Ghanaian': ['Ghanaian', 'Filipina'],
    'Kazakhstani': ['Kazakhstani', 'Filipina'],
    'Lebanese': ['Lebanese'],
    'Malagasy': ['Malagasy', 'Filipina'],
    'Moroccan': ['Moroccan'],
    'Pakistani': ['Pakistani', 'Filipina'],
    'Peruvian': ['Peruvian', 'Filipina'],
    'Rwandan': ['Rwandan', 'Filipina'],
    'South African': ['South African', 'Filipina'],
    'Thai': ['Thai', 'Filipina'],
    'Turkmen': ['Turkmen', 'Filipina'],
    'Ukrainian': ['Ukrainian', 'Filipina'],
    'Zimbabwean': ['Zimbabwean', 'Filipina'],
    # Add more nationality rules here as needed
}

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
    {"name": "PC 1", "link": "1iNnPAcueulelAKeAFVHBV07EdAt8GnT_4duCU1S2XH0"},
    {"name": "PC 2", "link": "1-htj-EWu2x7GcKWzTKSfUPemBoYLDP68g0vIgEzjLdM"},
    {"name": "PC 3", "link": "1MP4hoas3522DovdAJo9xIEU62KLX-azajJ9LI07mK2U"},
    {"name": "PC 4", "link": "1lNcsXdWQ2y2QKNexgLk_ZjBHOaXEcMXBNtmSBw_dtKs"},  
]

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
                    # Upload for Application Maids file
                    dcc.Upload(
                        id='upload-maid-data',
                        children=html.Div([
                            html.I(className="fas fa-file-excel me-2"),
                            'Drag and Drop or ',
                            html.A('Select Application Maid Excel File', className="text-primary")
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
                    
                    # Add Upload for Replacement Maids file
                    dcc.Upload(
                        id='upload-replacement-data',
                        children=html.Div([
                            html.I(className="fas fa-file-excel me-2"),
                            'Drag and Drop or ',
                            html.A('Select Replacement Maids Excel File', className="text-primary")
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
                    html.Div(id='replacement-upload-status', className="mt-3"),
                    
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


def register_callbacks(app):
    def create_pc_row(name, link, index):
        return dbc.Row([
            dbc.Col(dbc.Checkbox(id={'type': 'pc-checkbox', 'index': index}, value=False), width=1),
            dbc.Col(dbc.Input(id={'type': 'pc-name', 'index': index}, value=name, placeholder="PC Name"), width=2),
            dbc.Col(dbc.Input(id={'type': 'pc-link', 'index': index}, value=link, placeholder="Google Sheet URL or ID"), width=7),
            dbc.Col(dbc.Button("Delete", id={'type': 'delete-pc', 'index': index}, color="danger", size="sm"), width=2),
        ], className="mb-2")

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

    # Helper function to find a replacement for an application maid
    def find_replacement(application_maid, replacement_maids):
        app_nationality = application_maid['Housemaid Nationality']  # Using the specified column name
        app_gender = application_maid['Gender']

        # Get allowed nationalities based on the rules
        allowed_nationalities = NATIONALITY_RULES.get(app_nationality, [])
        
        # print(f"Finding replacement for {application_maid['Housemaid Name']} with nationality {app_nationality} and gender {app_gender}")
        # print(f"Allowed nationalities: {allowed_nationalities}")

        # Filter available replacements by nationality, gender, and 'Used' status
        for nationality in allowed_nationalities:
            available_replacements = replacement_maids.loc[
                (replacement_maids['Cancelled Employee Nationality'] == nationality) &
                (replacement_maids['Gender'] == app_gender) &
                (replacement_maids['Used'] == False)
            ]

            if not available_replacements.empty:
                # Choose the replacement with the smallest 'Cancelled Work Permit Expiry Date'
                best_replacement = available_replacements.loc[available_replacements['Cancelled Work Permit Expiry Date'].idxmin()]
                replacement_index = best_replacement.name

                # Mark the selected replacement maid as used
                replacement_maids.loc[replacement_index, 'Used'] = True

                # print(f"Replacement found: {best_replacement['Cancelled Employee Name']} with nationality {best_replacement['Cancelled Employee Nationality']}")
                return best_replacement, replacement_index

        # No match found
        # print(f"No replacement found for {application_maid['Housemaid Name']}")
        return None, None

    # Distribute maids to PCs with replacement logic
    def distribute_maids_with_replacements(app_maids, replacement_maids, num_pcs):
        distribution = {f"PC_{i+1}": [] for i in range(num_pcs)}
        pc_index = 0

        # Safely add the 'Used' column if it doesn't exist
        if 'Used' not in replacement_maids.columns:
            replacement_maids['Used'] = False  # Initialize as False for all maids

        for _, app_maid in app_maids.iterrows():
            # Find a matching replacement maid
            replacement_maid, replacement_index = find_replacement(app_maid, replacement_maids)
            
            if replacement_maid is not None:
                print(f"Assigning replacement {replacement_maid['Cancelled Employee Name']} to {app_maid['Housemaid Name']}")
                # Prepare the result row with both application and replacement maid details
                result_row = {
                    'Priority number': app_maid['Priority number'],
                    'id': app_maid['Request ID'],
                    'name': app_maid['Housemaid Name'],
                    'Nationality': app_maid['Housemaid Nationality'],
                    'Gender': app_maid['Gender'],
                    'cancelRequestID': replacement_maid['Cancelled Employee ID'],
                    'Cancelled Employee Name': replacement_maid['Cancelled Employee Name'],
                    'replacementNationality': replacement_maid['Cancelled Employee Nationality'],
                    'Cancelled Employee Gender': replacement_maid['Gender'],
                    'Cancelled Work Permit Expiry Date': replacement_maid['Cancelled Work Permit Expiry Date']
                }
                distribution[f"PC_{pc_index + 1}"].append(result_row)
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
        Output('replacement-upload-status', 'children'),
        Input('upload-replacement-data', 'contents'),
        State('upload-replacement-data', 'filename')
    )
    def update_replacement_upload_status(contents, filename):
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


    # Callback for uploading both application maids and replacement maids
    @app.callback(
        Output("maid-distribution-output", "children"),
        Input("btn-distribute-maids", "n_clicks"),
        [State("upload-maid-data", "contents"),
        State("upload-maid-data", "filename"),
        State("upload-replacement-data", "contents"),
        State("upload-replacement-data", "filename"),
        State({'type': 'pc-checkbox', 'index': ALL}, 'value'),
        State({'type': 'pc-name', 'index': ALL}, 'value'),
        State({'type': 'pc-link', 'index': ALL}, 'value')],
        prevent_initial_call=True
    )
    def process_maid_distribution_with_replacements(n_clicks, app_contents, app_filename, rep_contents, rep_filename, pc_checks, pc_names, pc_links):
        if app_contents is None or rep_contents is None:
            return html.Div("Please upload both application maids and replacement maids files.", className="alert alert-warning")

        app_maids = parse_contents(app_contents, app_filename)
        rep_maids = parse_contents(rep_contents, rep_filename)

        if not isinstance(app_maids, pd.DataFrame) or not isinstance(rep_maids, pd.DataFrame):
            return html.Div("Error processing the files.", className="alert alert-danger")

        # Validate necessary columns
        try:
            app_maids = filter_blank_entries(app_maids)
            # app_maids = prioritize_maids(app_maids)
        except KeyError as e:
            return html.Div(str(e), className="alert alert-danger")

        selected_pcs = [{"name": name, "link": extract_sheet_id(link)} for name, link, checked in zip(pc_names, pc_links, pc_checks) if checked and link.strip()]
        if not selected_pcs:
            return html.Div("Please select at least one PC with a valid Google Sheet URL or ID.", className="alert alert-warning")

        # Perform distribution with replacements
        distribution = distribute_maids_with_replacements(app_maids, rep_maids, len(selected_pcs))

        summary = html.Div([
            html.H5("Maid Distribution Summary with Replacements:", className="mt-4 mb-3"),
            html.Ul(id="distribution-results", className="list-group"),
            dcc.Graph(figure=create_distribution_chart(distribution), className="mt-4"),
            html.Div(generate_detailed_statistics(distribution), className="mt-4")
        ])

        # Write the distribution results to the selected PCs
        results = []
        for i, ((pc_key, maids), pc) in enumerate(zip(distribution.items(), selected_pcs)):
            df_to_write = pd.DataFrame(maids)
            success = write_to_google_sheet(pc['link'], df_to_write)
            status = "Success" if success else "Failed"
            results.append(html.Li(f"{pc['name']} ({pc_key}): {len(maids)} maids - Writing {status}", 
                                className=f"list-group-item {'list-group-item-success' if success else 'list-group-item-danger'}"))

        summary.children[1].children = results

        # Provide the CSV summary for download
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