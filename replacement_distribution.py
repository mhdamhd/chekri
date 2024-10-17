import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import io
import base64
from collections import defaultdict
import plotly.graph_objs as go

# Initialize the Dash app with a modern theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME])

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

# Nationality matching rules
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

# App layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("RPA Assignment Dashboard", className="display-4 text-center mb-3"),
            html.P("Distribute maids for Replacements and Quota across PCs.", className="lead text-center"),
        ], width=12)
    ], style=HEADER_STYLE),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H4("Replacement Distribution", className="text-white"), className="bg-primary"),
                dbc.CardBody([
                    dcc.Upload(
                        id='upload-replacement-data',
                        children=html.Div([
                            html.I(className="fas fa-file-excel me-2"),
                            'Drag and Drop or ',
                            html.A('Select Replacement Excel File', className="text-primary")
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
                    dcc.Upload(
                        id='upload-canceled-data',
                        children=html.Div([
                            html.I(className="fas fa-file-excel me-2"),
                            'Drag and Drop or ',
                            html.A('Select Canceled Employee Excel File', className="text-danger")
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
                    html.Div(id='canceled-upload-status', className="mt-3"),
                    dbc.InputGroup([
                        dbc.InputGroupText(html.I(className="fas fa-desktop")),
                        dbc.Input(id="replacement-num-pcs", type="number", placeholder="Enter number of PCs", value=7),
                    ], className="mb-3"),
                    dbc.Button("Distribute Replacements", id="btn-distribute-replacements", color="primary", className="w-100", size="lg", style=BUTTON_STYLE),
                    dbc.Spinner(html.Div(id="replacement-distribution-output"), color="primary", type="border", spinnerClassName="mt-3"),
                ])
            ], style=CARD_STYLE),
        ], width=12, md=6),

        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H4("Quota Distribution", className="text-white"), className="bg-info"),
                dbc.CardBody([
                    dcc.Upload(
                        id='upload-quota-data',
                        children=html.Div([
                            html.I(className="fas fa-file-excel me-2"),
                            'Drag and Drop or ',
                            html.A('Select Quota Excel File', className="text-info")
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
                    html.Div(id='quota-upload-status', className="mt-3"),
                    dbc.InputGroup([
                        dbc.InputGroupText(html.I(className="fas fa-desktop")),
                        dbc.Input(id="quota-num-pcs", type="number", placeholder="Enter number of PCs", value=2),
                    ], className="mb-3"),
                    dbc.Button("Distribute Quota", id="btn-distribute-quota", color="info", className="w-100", size="lg", style=BUTTON_STYLE),
                    dbc.Spinner(html.Div(id="quota-distribution-output"), color="info", type="border", spinnerClassName="mt-3"),
                ])
            ], style=CARD_STYLE),
        ], width=12, md=6),
    ]),

    dcc.Download(id="download-replacement-distribution"),
    dcc.Download(id="download-quota-distribution"),
], fluid=True, className="px-4 py-5 bg-light")
layout = app.layout

def register_callbacks(app):
    def clean_data_frame(df):
        # Remove columns that have "Unnamed" in their names (common with Excel files)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        
        # You can also add more cleaning steps here if needed, e.g., handling NaN values
        df = df.dropna(how='all')  # Drop rows where all elements are NaN

        return df


    # Helper functions
    def parse_contents(contents, filename):
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        try:
            if 'xlsx' in filename:
                df = pd.read_excel(io.BytesIO(decoded))
            elif 'csv' in filename:
                # Handle the file as a tab-delimited CSV
                df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), delimiter='\t')
            else:
                return html.Div(['Please upload an Excel or CSV file.']), None

            # Strip any leading/trailing spaces from column names
            df.columns = df.columns.str.strip()

            # Clean any 'Unnamed' columns if they exist
            df = clean_data_frame(df)

            print(f"Column names in {filename}: {df.columns.tolist()}")
            return df
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            return html.Div([f'Error processing the file: {e}']), None

    def parse_contents_file1(contents, filename):
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        try:
            if 'xlsx' in filename:
                df = pd.read_excel(io.BytesIO(decoded))
            elif 'csv' in filename:
                # Assuming the first file is comma-separated
                df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), delimiter=',')
            else:
                return html.Div(['Please upload an Excel or CSV file.']), None

            # Strip any leading/trailing spaces from column names
            df.columns = df.columns.str.strip()

            # Debugging: Print the columns to verify the parsing
            print(f"Column names in {filename}: {df.columns.tolist()}")
            return df
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            return html.Div([f'Error processing the file: {e}']), None

    def parse_contents_file2(contents, filename):
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        try:
            if 'xlsx' in filename:
                df = pd.read_excel(io.BytesIO(decoded))
            elif 'csv' in filename:
                # Try reading the file using multiple encodings, since there's a UTF-8 error
                try:
                    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), delimiter='\t')
                except UnicodeDecodeError:
                    try:
                        df = pd.read_csv(io.StringIO(decoded.decode('utf-16')), delimiter='\t')
                    except UnicodeDecodeError:
                        df = pd.read_csv(io.StringIO(decoded.decode('ISO-8859-1')), delimiter='\t')
            else:
                return html.Div(['Please upload an Excel or CSV file.']), None

            # Strip any leading/trailing spaces from column names
            df.columns = df.columns.str.strip()

            # Debugging: Print the columns to verify the parsing
            print(f"Column names in {filename}: {df.columns.tolist()}")
            return df
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            return html.Div([f'Error processing the file: {e}']), None


    def filter_blank_entries(df):
        return df.dropna(subset=['Request ID', 'Housemaid Name'])

    def prioritize_maids(df):
        df['Priority'] = df['Priority number']
        return df.sort_values('Priority')

    def distribute_maids_with_cancel_id(df, num_pcs, canceled_employees_df):
        distribution = defaultdict(list)
        used_cancel_ids = set()  # Track used Cancel IDs
        pc_index = 0

        for _, maid in df.iterrows():
            maid_info = {
                'Request ID': maid['Request ID'],
                'Housemaid Name': maid['Housemaid Name'],
                'Type': maid['Housemaid Type'],
                'Gender': maid['Gender'],
                'Priority Name': maid['Priority Name'],
                'Cancel ID': ''
            }

            # Assign Cancel ID based on gender and nationality rules
            maid_nationality = maid['Housemaid Nationality']
            maid_gender = maid['Gender']

            # Get nationality priority list (same nationality first)
            nationality_priority = NATIONALITY_RULES.get(maid_nationality, [])

            # Iterate through nationalities in priority order
            for nationality in nationality_priority:
                valid_cancel_employees = canceled_employees_df[
                    (canceled_employees_df['Gender'] == maid_gender) &
                    (canceled_employees_df['Cancelled Employee Nationality'] == nationality) &
                    (~canceled_employees_df['Cancelled Employee ID'].isin(used_cancel_ids))
                ]

                # If a valid Cancel ID is found for this nationality, assign it and mark as used
                if not valid_cancel_employees.empty:
                    cancel_id = valid_cancel_employees.iloc[0]['Cancelled Employee ID']
                    maid_info['Cancel ID'] = cancel_id
                    used_cancel_ids.add(cancel_id)  # Mark Cancel ID as used
                    break  # Stop once a valid Cancel ID is found

            # Only add the maid to the distribution if they have a Cancel ID
            if maid_info['Cancel ID']:
                distribution[f"PC_{pc_index + 1}"].append(maid_info)
                pc_index = (pc_index + 1) % num_pcs

        return distribution


    def create_output_file(distribution, distribution_type):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for pc, maids in distribution.items():
                pc_df = pd.DataFrame(maids)
                if distribution_type == 'replacement':
                    columns = ['Request ID', 'Housemaid Name', 'Cancel ID', 'Type', 'Gender', 'Priority Name']
                else:
                    columns = ['Request ID', 'Housemaid Name', 'Type', 'Gender', 'Priority Name']
                pc_df = pc_df[columns]
                pc_df.to_excel(writer, sheet_name=pc, index=False)
        return output

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

    # Callbacks for upload status
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
        Output('canceled-upload-status', 'children'),
        Input('upload-canceled-data', 'contents'),
        State('upload-canceled-data', 'filename')
    )
    def update_canceled_upload_status(contents, filename):
        if contents is not None:
            return html.Div([
                html.I(className="fas fa-check-circle text-success me-2"),
                f"File uploaded successfully: {filename}"
            ], className="mt-2 alert alert-success")
        return ""

    @app.callback(
        Output('quota-upload-status', 'children'),
        Input('upload-quota-data', 'contents'),
        State('upload-quota-data', 'filename')
    )
    def update_quota_upload_status(contents, filename):
        if contents is not None:
            return html.Div([
                html.I(className="fas fa-check-circle text-success me-2"),
                f"File uploaded successfully: {filename}"
            ], className="mt-2 alert alert-success")
        return ""

    # Callback for Replacement Distribution
    @app.callback(
        [Output("replacement-distribution-output", "children"),
        Output("download-replacement-distribution", "data")],
        [Input("btn-distribute-replacements", "n_clicks")],
        [State("upload-replacement-data", "contents"),
        State("upload-replacement-data", "filename"),
        State("replacement-num-pcs", "value"),
        State("upload-canceled-data", "contents"),
        State("upload-canceled-data", "filename")],
        prevent_initial_call=True
    )
    def process_replacement_distribution(n_clicks, contents, filename, num_pcs, canceled_contents, canceled_filename):
        if contents is None or canceled_contents is None:
            return html.Div("Please upload both the replacement and canceled employee files.", className="alert alert-warning"), None

        df = parse_contents_file1(contents, filename)
        canceled_df = parse_contents_file1(canceled_contents, canceled_filename)
        if not isinstance(df, pd.DataFrame) or not isinstance(canceled_df, pd.DataFrame):
            return html.Div("Error processing the files.", className="alert alert-danger"), None

        df_filtered = filter_blank_entries(df)
        df_prioritized = prioritize_maids(df_filtered)
        distribution = distribute_maids_with_cancel_id(df_prioritized, num_pcs or 7, canceled_df)

        output = create_output_file(distribution, 'replacement')

        summary = html.Div([
            html.H5("Replacement Distribution Summary:", className="mt-4 mb-3"),
            html.Ul([
                html.Li(f"{pc} contains {len(maids)} maids", className="list-group-item") for pc, maids in distribution.items()
            ], className="list-group"),
            dcc.Graph(figure=create_distribution_chart(distribution), className="mt-4")
        ])

        return summary, dcc.send_bytes(output.getvalue(), "replacement_distribution.xlsx")

    # Callback for Quota Distribution
    @app.callback(
        [Output("quota-distribution-output", "children"),
        Output("download-quota-distribution", "data")],
        [Input("btn-distribute-quota", "n_clicks")],
        [State("upload-quota-data", "contents"),
        State("upload-quota-data", "filename"),
        State("quota-num-pcs", "value")],
        prevent_initial_call=True
    )
    def process_quota_distribution(n_clicks, contents, filename, num_pcs):
        if contents is None:
            return html.Div("Please upload a file first.", className="alert alert-warning"), None

        df = parse_contents_file1(contents, filename)
        
        if not isinstance(df, pd.DataFrame):
            return html.Div("Error processing the file.", className="alert alert-danger"), None

        df_filtered = filter_blank_entries(df)
        df_prioritized = prioritize_maids(df_filtered)
        distribution = distribute_maids_with_cancel_id(df_prioritized, num_pcs or 2, pd.DataFrame())

        output = create_output_file(distribution, 'quota')

        summary = html.Div([
            html.H5("Quota Distribution Summary:", className="mt-4 mb-3"),
            html.Ul([
                html.Li(f"{pc} contains {len(maids)} maids", className="list-group-item") for pc, maids in distribution.items()
            ], className="list-group"),
            dcc.Graph(figure=create_distribution_chart(distribution), className="mt-4")
        ])

        return summary, dcc.send_bytes(output.getvalue(), "quota_distribution.xlsx")

if __name__ == '__main__':
    app.run_server(debug=True, port=7001)