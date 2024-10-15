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

# Define custom styles with enhanced design and new color scheme
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

# App layout with improved design
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

# Helper functions
def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'xlsx' in filename:
            # Read Excel file
            df = pd.read_excel(io.BytesIO(decoded))
        elif 'csv' in filename:
            # Read CSV file
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        else:
            return html.Div(['Please upload an Excel or CSV file.'])
        return df
    except Exception as e:
        print(e)
        return html.Div(['There was an error processing this file.'])


def prioritize_maids(df):
    df['Priority'] = df['Priority number']
    return df.sort_values('Priority')

def filter_blank_entries(df):
    return df.dropna(subset=['Request ID', 'Housemaid Name'])

def distribute_maids(df, num_pcs, distribution_type):
    distribution = defaultdict(list)
    pc_index = 0
    for _, maid in df.iterrows():
        maid_info = {
            'Request ID': maid['Request ID'],
            'Housemaid Name': maid['Housemaid Name'],
            'Type': maid['Housemaid Type'],
            'Gender': maid['Gender'],
            'Priority Name': maid['Priority Name']
        }
        if distribution_type == 'replacement':
            maid_info['Cancel ID'] = maid.get('Cancel ID', '')
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

# Callbacks
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

@app.callback(
    [Output("replacement-distribution-output", "children"),
     Output("download-replacement-distribution", "data")],
    [Input("btn-distribute-replacements", "n_clicks")],
    [State("upload-replacement-data", "contents"),
     State("upload-replacement-data", "filename"),
     State("replacement-num-pcs", "value")],
    prevent_initial_call=True
)
def process_replacement_distribution(n_clicks, contents, filename, num_pcs):
    if contents is None:
        return html.Div("Please upload a file first.", className="alert alert-warning"), None

    df = parse_contents(contents, filename)
    if not isinstance(df, pd.DataFrame):
        return html.Div("Error processing the file.", className="alert alert-danger"), None

    df_filtered = filter_blank_entries(df)
    df_prioritized = prioritize_maids(df_filtered)
    distribution = distribute_maids(df_prioritized, num_pcs or 7, 'replacement')

    output = create_output_file(distribution, 'replacement')

    summary = html.Div([
        html.H5("Replacement Distribution Summary:", className="mt-4 mb-3"),
        html.Ul([
            html.Li(f"{pc} contains {len(maids)} maids", className="list-group-item") for pc, maids in distribution.items()
        ], className="list-group"),
        dcc.Graph(figure=create_distribution_chart(distribution), className="mt-4")
    ])

    return summary, dcc.send_bytes(output.getvalue(), "replacement_distribution.xlsx")

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

    df = parse_contents(contents, filename)
    if not isinstance(df, pd.DataFrame):
        return html.Div("Error processing the file.", className="alert alert-danger"), None

    df_filtered = filter_blank_entries(df)
    df_prioritized = prioritize_maids(df_filtered)
    distribution = distribute_maids(df_prioritized, num_pcs or 2, 'quota')

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