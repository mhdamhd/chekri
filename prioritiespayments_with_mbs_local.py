import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import io
import base64
import plotly.graph_objs as go
from dash.exceptions import PreventUpdate
import numpy as np
from datetime import datetime, timedelta

# Initialize the Dash app with a modern theme (Bootstrap for styling)
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define custom styles for better visual hierarchy
CARD_STYLE = {
    "box-shadow": "0 4px 6px 0 rgba(0, 0, 0, 0.18)",
    "margin-bottom": "24px",
    "border-radius": "8px",
}

HEADER_STYLE = {
    "background-color": "#f8f9fa",
    "padding": "20px",
    "margin-bottom": "20px",
    "border-radius": "8px",
    "box-shadow": "0 2px 4px rgba(0,0,0,0.1)",
}

BUTTON_STYLE = {
    "width": "100%",
    "margin-bottom": "10px",
}

# Define the layout of the app with improved design, filters, and explanations
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Maid Document Prioritization Dashboard", className="text-center my-4 text-primary"),
            html.P("This dashboard helps prioritize maid documents based on various criteria.", className="text-center text-muted"),
        ], width=12)
    ], style=HEADER_STYLE),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H4("Priority Filters", className="text-info")),
                dbc.CardBody([
                    html.P("Adjust these filters to set priority counters and thresholds.", className="text-muted mb-4"),
                    dbc.Row([
                        dbc.Col([
                            html.H5("Current Counters", className="mb-3 text-secondary"),
                            dbc.InputGroup([
                                dbc.InputGroupText("Filipina Live-In"),
                                dbc.Input(id="counter-filipina-live-in", type="number", placeholder="Enter count", value=0),
                            ], className="mb-2"),
                            dbc.InputGroup([
                                dbc.InputGroupText("African Live-In"),
                                dbc.Input(id="counter-african-live-in", type="number", placeholder="Enter count", value=0),
                            ], className="mb-2"),
                            dbc.InputGroup([
                                dbc.InputGroupText("Ethiopian Live-In"),
                                dbc.Input(id="counter-ethiopian-live-in", type="number", placeholder="Enter count", value=0),
                            ], className="mb-2"),
                            dbc.InputGroup([
                                dbc.InputGroupText("Filipina Live-Out"),
                                dbc.Input(id="counter-filipina-live-out", type="number", placeholder="Enter count", value=0),
                            ], className="mb-2"),
                            dbc.InputGroup([
                                dbc.InputGroupText("African Live-Out"),
                                dbc.Input(id="counter-african-live-out", type="number", placeholder="Enter count", value=0),
                            ], className="mb-2"),
                        ], md=6),
                        dbc.Col([
                            html.H5("Maximum Thresholds", className="mb-3 text-secondary"),
                            dbc.InputGroup([
                                dbc.InputGroupText("Filipina Live-In"),
                                dbc.Input(id="threshold-filipina-live-in", type="number", placeholder="Enter max", value=80),
                            ], className="mb-2"),
                            dbc.InputGroup([
                                dbc.InputGroupText("African Live-In"),
                                dbc.Input(id="threshold-african-live-in", type="number", placeholder="Enter max", value=60),
                            ], className="mb-2"),
                            dbc.InputGroup([
                                dbc.InputGroupText("Ethiopian Live-In"),
                                dbc.Input(id="threshold-ethiopian-live-in", type="number", placeholder="Enter max", value=70),
                            ], className="mb-2"),
                            dbc.InputGroup([
                                dbc.InputGroupText("Filipina Live-Out"),
                                dbc.Input(id="threshold-filipina-live-out", type="number", placeholder="Enter max", value=60),
                            ], className="mb-2"),
                            dbc.InputGroup([
                                dbc.InputGroupText("African Live-Out"),
                                dbc.Input(id="threshold-african-live-out", type="number", placeholder="Enter max", value=40),
                            ], className="mb-2"),
                        ], md=6),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.H5("Offer Letter Date Threshold (Days)", className="mb-3 text-secondary"),
                            dbc.InputGroup([
                                dbc.InputGroupText("Days Threshold"),
                                dbc.Input(id="offer-letter-threshold", type="number", placeholder="Enter threshold", value=2),
                            ], className="mb-2"),
                        ], md=6),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.H5("MV Urgency Threshold", className="mb-3 text-secondary"),
                            dbc.InputGroup([
                                dbc.InputGroupText("Days for MV Urgency"),
                                dbc.Input(id="mv-urgency-days", type="number", placeholder="Enter days", value=5),
                            ], className="mb-2"),

                        ], md=6),
                    ]),
                ])
            ], style=CARD_STYLE),
        ], width=12),
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H4("File Upload", className="text-info")),
                dbc.CardBody([
                    html.P("Please upload an Excel file containing the maid data. Ensure the file has the necessary columns for processing.", className="text-muted mb-4"),
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div([
                            'Drag and Drop or ',
                            html.A('Select an Excel File', className="text-primary")
                        ]),
                        style={
                            'width': '100%',
                            'height': '60px',
                            'lineHeight': '60px',
                            'borderWidth': '2px',
                            'borderStyle': 'dashed',
                            'borderRadius': '5px',
                            'textAlign': 'center',
                            'margin': '20px 0'
                        },
                        multiple=False
                    ),
                    html.Div(id='upload-status', className="mt-3"),
                ])
            ], style=CARD_STYLE),
        ], width=12),
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H4("Generate Reports", className="text-info")),
                dbc.CardBody([
                    html.P("Click on a button to generate the corresponding report. Each report includes three sheets: Accepted, Rejected, and Combined (sorted by priority).", className="text-muted mb-4"),
                    dbc.Row([
                        dbc.Col(dbc.Button("Download Combined Report", id="btn-combined-report", color="primary", className="w-100", size="lg", style=BUTTON_STYLE), width=12, md=4),
                        dbc.Col(dbc.Button("Download LAWP Report", id="btn-lawp-report", color="info", className="w-100", size="lg", style=BUTTON_STYLE), width=12, md=4),
                        dbc.Col(dbc.Button("Download Non-LAWP Report", id="btn-no-lawp-report", color="success", className="w-100", size="lg", style=BUTTON_STYLE), width=12, md=4),
                    ]),
                    dbc.Row([
                       dbc.Col(dbc.Button("Download Top Priorities", id="btn-top-priorities", color="warning", className="w-100", size="lg", style=BUTTON_STYLE), width=12, md=4),
                    ]),
                    dbc.Spinner(html.Div(id="loading-output"), color="primary", type="grow", spinnerClassName="mt-3"),
                ])
            ], style=CARD_STYLE),
        ], width=12),
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H4("Statistics", className="text-info")),
                dbc.CardBody([
                    html.Div(id='output-stats', className="mt-4"),
                ])
            ], style=CARD_STYLE),
        ], width=12),
    ]),
    
    dcc.Download(id="download-report"),
], fluid=True)

# List of African countries for prioritization
african_countries = [
    "Algeria", "Algerian", "Algerians", "Algerian (adj.)",
    "Angola", "Angolan", "Angolans", "Angolan (adj.)",
    "Benin", "Beninese", "Beninese (plural)", "Beninese (adj.)",
    "Botswana", "Botswanan", "Botswanans", "Botswanan (adj.)",
    "Burkina Faso", "Burkinabe", "Burkinabe (plural)", "Burkinabe (adj.)",
    "Burundi", "Burundian", "Burundians", "Burundian (adj.)",
    "Cabo Verde", "Cabo Verdean", "Cabo Verdeans", "Cabo Verdean (adj.)",
    "Cameroon", "Cameroonian", "Cameroonians", "Cameroonian (adj.)",
    "Central African Republic", "Central African", "Central Africans", "Central African (adj.)",
    "Chad", "Chadian", "Chadians", "Chadian (adj.)",
    "Comoros", "Comoran", "Comorans", "Comoran (adj.)",
    "Democratic Republic of the Congo", "Congolese (Democratic Republic)", "Congolese (plural)", "Congolese (Democratic Republic adj.)",
    "Republic of the Congo", "Congolese (Republic)", "Congolese (plural)", "Congolese (Republic adj.)",
    "Djibouti", "Djiboutian", "Djiboutians", "Djiboutian (adj.)",
    "Egypt", "Egyptian", "Egyptians", "Egyptian (adj.)",
    "Equatorial Guinea", "Equatoguinean", "Equatoguineans", "Equatoguinean (adj.)",
    "Eritrea", "Eritrean", "Eritreans", "Eritrean (adj.)",
    "Eswatini", "Swazi", "Swazis", "Swazi (adj.)",
    "Ethiopia", "Ethiopian", "Ethiopians", "Ethiopian (adj.)",
    "Gabon", "Gabonese", "Gabonese (plural)", "Gabonese (adj.)",
    "Gambia", "Gambian", "Gambians", "Gambian (adj.)",
    "Ghana", "Ghanaian", "Ghanaians", "Ghanaian (adj.)",
    "Guinea", "Guinean", "Guineans", "Guinean (adj.)",
    "Guinea-Bissau", "Bissau-Guinean", "Bissau-Guineans", "Bissau-Guinean (adj.)",
    "Ivory Coast", "Ivorian", "Ivorians", "Ivorian (adj.)",
    "Kenya", "Kenyan", "Kenyans", "Kenyan (adj.)",
    "Lesotho", "Mosotho", "Basotho", "Basotho (adj.)",
    "Liberia", "Liberian", "Liberians", "Liberian (adj.)",
    "Libya", "Libyan", "Libyans", "Libyan (adj.)",
    "Madagascar", "Malagasy", "Malagasy (plural)", "Malagasy (adj.)",
    "Malawi", "Malawian", "Malawians", "Malawian (adj.)",
    "Mali", "Malian", "Malians", "Malian (adj.)",
    "Mauritania", "Mauritanian", "Mauritanians", "Mauritanian (adj.)",
    "Mauritius", "Mauritian", "Mauritians", "Mauritian (adj.)",
    "Morocco", "Moroccan", "Moroccans", "Moroccan (adj.)",
    "Mozambique", "Mozambican", "Mozambicans", "Mozambican (adj.)",
    "Namibia", "Namibian", "Namibians", "Namibian (adj.)",
    "Niger", "Nigerien", "Nigeriens", "Nigerien (adj.)",
    "Nigeria", "Nigerian", "Nigerians", "Nigerian (adj.)",
    "Rwanda", "Rwandan", "Rwandans", "Rwandan (adj.)",
    "São Tomé and Príncipe", "São Toméan", "São Toméans", "São Toméan (adj.)",
    "Senegal", "Senegalese", "Senegalese (plural)", "Senegalese (adj.)",
    "Seychelles", "Seychellois", "Seychellois (plural)", "Seychellois (adj.)",
    "Sierra Leone", "Sierra Leonean", "Sierra Leoneans", "Sierra Leonean (adj.)",
    "Somalia", "Somali", "Somalis", "Somali (adj.)",
    "South Africa", "South African", "South Africans", "South African (adj.)",
    "South Sudan", "South Sudanese", "South Sudanese (plural)", "South Sudanese (adj.)",
    "Sudan", "Sudanese", "Sudanese (plural)", "Sudanese (adj.)",
    "Tanzania", "Tanzanian", "Tanzanians", "Tanzanian (adj.)",
    "Togo", "Togolese", "Togolese (plural)", "Togolese (adj.)",
    "Tunisia", "Tunisian", "Tunisians", "Tunisian (adj.)",
    "Uganda", "Ugandan", "Ugandans", "Ugandan (adj.)",
    "Zambia", "Zambian", "Zambians", "Zambian (adj.)",
    "Zimbabwe", "Zimbabwean", "Zimbabweans", "Zimbabwean (adj.)"
]
    # Define priority names for display



def get_priority_names(mv_urgency_days):
    return {
        1: "MV with Super Angry Client",
        2: "MV with Visa Prioritization Request",
        3: "Filipina with Flight in more than 2 days and Less Than 4 Days",
        4: f"MV in Table for More Than {mv_urgency_days} Days",
        5: "Last day to stay in country < 5",  # New priority
        6: "Filipina Live-In in Dubai",  # This was previously priority 5
        7: "African Live-In in Dubai",  # Previously 6, and so on...
        8: "Ethiopian Live-In in Dubai",
        9: "Ethiopian Pending COC for More Than 10 Days",
        10: "Filipina Live-Out in Dubai",
        11: "African Live-Out in Dubai",
        12: "Filipina with Flight in 4 to 7 Days",
        13: f"MV in Table for {mv_urgency_days} Days or Less",
        14: "Landed in Dubai Live In",
        15: "Landed in Dubai Live Out",
        16: "Outcome is LAWP",
        17: "Filipina with Flight in 7 to 14 Days",
        18: "African with Attested GCC",
        19: "Ethiopian Pending Exit Permit",
        20: "African with MFA",
        21: "Ethiopian Pending COC",
        22: "African with GCC",
        23: "Other"
    }

def parse_contents(contents, filename):
    """Parse the contents of the uploaded file and return a pandas DataFrame."""
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'xlsx' in filename:
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            return html.Div(['Please upload an Excel file.'])
        return df
    except Exception as e:
        print(e)
        return html.Div(['There was an error processing this file.'])


def assign_priority(row, priority_counters, priority_thresholds, mv_urgency_days):
    """Assign priority to a row based on various conditions."""
    priorities = []
    
    # Priority assignment logic
    if row['Housemaid Type'] == 'MV' and row['Client Note'] == 'SUPER_ANGRY_CLIENT':
        priorities.append(1)
    
    if row['Housemaid Type'] == 'MV' and row['Client Note'] == 'PRIORITIZE_VISA':
        priorities.append(2)
    
    if row['Housemaid Nationality'] == 'Filipina' and pd.notna(row['Flight in (days)']) and row['Flight in (days)'] < 4 and row['Flight in (days)'] > 2:
        priorities.append(3)
    
    if row['Housemaid Type'] == 'MV' and pd.notna(row['Been in the table for (in days)']) and row['Been in the table for (in days)'] > mv_urgency_days:
        priorities.append(4)
    
    # New priority: Last day to stay in country < 5 (This becomes Priority 5)
    if pd.notna(row['Last day to stay in country in']) and row['Last day to stay in country in'] < 5:
        priorities.append(5)
    
    # Shift all subsequent priorities by 1
    if row['Housemaid Nationality'] == 'Filipina' and row['Housemaid Status'] == 'LANDED_IN_DUBAI' and row['Live out'] == 'No':
        if priority_counters[6] < priority_thresholds['Filipina Live-In']:
            priorities.append(6)
            priority_counters[6] += 1
    
    if row['Housemaid Nationality'] in african_countries and row['Housemaid Status'] == 'LANDED_IN_DUBAI' and row['Live out'] == 'No':
        if priority_counters[7] < priority_thresholds['African Live-In']:
            priorities.append(7)
            priority_counters[7] += 1
    
    if row['Housemaid Nationality'] == 'Ethiopian' and row['Housemaid Status'] == 'LANDED_IN_DUBAI' and row['Live out'] == 'No':
        if priority_counters[8] < priority_thresholds['Ethiopian Live-In']:
            priorities.append(8)
            priority_counters[8] += 1
    
    if row['Housemaid Nationality'] == 'Ethiopian' and row['Stage in Freedom Operator Page'] == 'Pending COC' and pd.notna(row['Been in the table for (in days)']) and row['Been in the table for (in days)'] > 10 and row['Live out'] == 'No':
        priorities.append(9)
    
    if row['Housemaid Nationality'] == 'Filipina' and row['Housemaid Status'] == 'LANDED_IN_DUBAI' and row['Live out'] == 'Yes':
        if priority_counters[10] < priority_thresholds['Filipina Live-Out']:
            priorities.append(10)
            priority_counters[10] += 1
    
    if row['Housemaid Nationality'] in african_countries and row['Housemaid Status'] == 'LANDED_IN_DUBAI' and row['Live out'] == 'Yes':
        if priority_counters[11] < priority_thresholds['African Live-Out']:
            priorities.append(11)
            priority_counters[11] += 1
    
    if row['Housemaid Nationality'] == 'Filipina' and pd.notna(row['Flight in (days)']) and 4 <= row['Flight in (days)'] <= 7:
        priorities.append(12)
    
    if row['Housemaid Type'] == 'MV' and pd.notna(row['Been in the table for (in days)']) and row['Been in the table for (in days)'] <= mv_urgency_days:
        priorities.append(13)

    if row['Housemaid Status'] == 'LANDED_IN_DUBAI' and row['Live out'] == 'No':
        priorities.append(14)

    if row['Housemaid Status'] == 'LANDED_IN_DUBAI' and row['Live out'] == 'Yes':
        priorities.append(15)

    if row['Outcome'] == 'LAWP':
        priorities.append(16)

    if row['Housemaid Nationality'] == 'Filipina' and pd.notna(row['Flight in (days)']) and 7 < row['Flight in (days)'] <= 14:
        priorities.append(17)
    
    if row['Housemaid Nationality'] in african_countries and row['Attested GCC'] == 'Yes':
        priorities.append(18)
    
    if row['Housemaid Nationality'] == 'Ethiopian' and row['Stage in Freedom Operator Page'] == 'Pending Exit Permit':
        priorities.append(19)
    
    if row['Housemaid Nationality'] in african_countries and row['MFA'] == 'Yes':
        priorities.append(20)
    
    if row['Housemaid Nationality'] == 'Ethiopian' and row['Stage in Freedom Operator Page'] == 'Pending COC':
        priorities.append(21)
    
    if row['Housemaid Nationality'] in african_countries and row['GCC'] == 'Yes':
        priorities.append(22)
    
    priorities.append(23)
    
    return min(priorities) if priorities else None

def process_dataframe(df, docs_status_list, priority_counters, priority_thresholds, mv_urgency_days):
    """Process the DataFrame to assign priorities and generate statistics."""

    if 'NA' in docs_status_list:
        # Remove 'NA' as a string
        docs_status_list.remove('NA')
        # Add np.nan to check for missing values
        docs_status_list.append(np.nan)
        df = df[df['Docs status'].isin(docs_status_list) | df['Docs status'].isna()]
    
    else:
        df = df[df['Docs status'].isin(docs_status_list)]
    
    priority_names = get_priority_names(mv_urgency_days)
    df['Priority number'] = df.apply(lambda row: assign_priority(row, priority_counters, priority_thresholds, mv_urgency_days), axis=1)
    df['Priority Name'] = df['Priority number'].map(priority_names)
    
    df_prioritized = df[df['Priority number'].notna()]
    output_df = df_prioritized.sort_values(by=['Priority number', 'Been in the table for (in days)'], ascending=[True, False])    
    output_df = output_df[['Priority number', 'Request ID', 'Housemaid Name', 'Housemaid Nationality', 'Housemaid Type', 'Gender', 'Priority Name', 'Been in the table for (in days)']]

    # output_df = output_df.sort_values('Priority number')
    
    stats = calculate_statistics(df_prioritized, priority_names)
    
    return output_df, stats

def calculate_statistics(df, priority_names):
    """Calculate statistics for the prioritized DataFrame."""
    stats = {}
    for priority, name in priority_names.items():
        priority_df = df[df['Priority number'] == priority]
        males = len(priority_df[priority_df['Gender'] == 'Male'])
        females = len(priority_df[priority_df['Gender'] == 'Female'])
        total = len(priority_df)
        stats[name] = {'Males': males, 'Females': females, 'Total': total}
    return stats

def create_stats_table(stats, title):
    """Create a formatted table for displaying statistics."""
    table_header = [
        html.Thead(html.Tr([html.Th("Priority Name"), html.Th("Males"), html.Th("Females"), html.Th("Total")]))
    ]
    rows = []
    for name, data in stats.items():
        row = html.Tr([html.Td(name), html.Td(data['Males']), html.Td(data['Females']), html.Td(data['Total'])])
        rows.append(row)
    table_body = [html.Tbody(rows)]
    return dbc.Table(table_header + table_body, bordered=True, hover=True, responsive=True, striped=True, className="mt-3", style={"fontSize": "0.9rem"})

@app.callback(
    Output('upload-status', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def update_upload_status(contents, filename):
    if contents is not None:
        return html.Div([
            html.I(className="fas fa-check-circle text-success me-2"),
            f"File uploaded successfully: {filename}"
        ], className="mt-2")
    return ""

@app.callback(
    [Output("download-report", "data"),
    Output('output-stats', 'children'),
    Output("loading-output", "children")],
    [Input("btn-combined-report", "n_clicks"),
    Input("btn-lawp-report", "n_clicks"),
    Input("btn-no-lawp-report", "n_clicks"),
    Input("btn-top-priorities", "n_clicks")],
    [State('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State("counter-filipina-live-in", "value"),
    State("counter-african-live-in", "value"),
    State("counter-ethiopian-live-in", "value"),
    State("counter-filipina-live-out", "value"),
    State("counter-african-live-out", "value"),
    State("threshold-filipina-live-in", "value"),
    State("threshold-african-live-in", "value"),
    State("threshold-ethiopian-live-in", "value"),
    State("threshold-filipina-live-out", "value"),
    State("threshold-african-live-out", "value"),
    State("offer-letter-threshold", "value"),
    State("mv-urgency-days", "value")],
    prevent_initial_call=True,
)
def generate_report(n_clicks_combined, n_clicks_lawp, n_clicks_no_lawp, n_clicks_top_priorities, 
                    contents, filename,
                    counter_filipina_live_in, counter_african_live_in, counter_ethiopian_live_in,
                    counter_filipina_live_out, counter_african_live_out,
                    threshold_filipina_live_in, threshold_african_live_in, threshold_ethiopian_live_in,
                    threshold_filipina_live_out, threshold_african_live_out, offer_letter_threshold,
                    mv_urgency_days):
    """Generate reports and display statistics based on the button clicked and input counters and thresholds."""
    if contents is None:
        raise PreventUpdate

    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    df = parse_contents(contents, filename)
    if not isinstance(df, pd.DataFrame):
        raise PreventUpdate
    original_df = df
    offer_letter_threshold = offer_letter_threshold or 2
    # df['Offer Letter date'] = pd.to_datetime(df['Offer Letter date'], errors='coerce')
    today = pd.Timestamp.today()
    df = df[((df['Payment added?'] == 'No'))]
    # df = df[((df['MB?'] == 'No') & (df['Has Contract MB?'] == 'No')) | (((df['MB?'] == 'Yes') | (df['Has Contract MB?'] == 'Yes')) & (((today - df['Offer Letter date']) <= timedelta(days=offer_letter_threshold))))]
    priority_counters = {
        6: counter_filipina_live_in or 0,
        7: counter_african_live_in or 0,
        8: counter_ethiopian_live_in or 0,
        10: counter_filipina_live_out or 0,
        11: counter_african_live_out or 0
    }
    
    priority_thresholds = {
        'Filipina Live-In': threshold_filipina_live_in or 80,
        'African Live-In': threshold_african_live_in or 60,
        'Ethiopian Live-In': threshold_ethiopian_live_in or 70,
        'Filipina Live-Out': threshold_filipina_live_out or 60,
        'African Live-Out': threshold_african_live_out or 40
    }

    mv_urgency_days = mv_urgency_days or 5

    if button_id == "btn-combined-report":
        accepted_df, accepted_stats = process_dataframe(df, [' Approved', 'Approved', 'Maid is already verified and accepted'], priority_counters.copy(), priority_thresholds, mv_urgency_days)
        rejected_df, rejected_stats = process_dataframe(df, [' Rejected', 'Rejected', 'NA', ' '], priority_counters.copy(), priority_thresholds, mv_urgency_days)
        combined_df, _ = process_dataframe(df, [' Approved', 'Approved', 'Maid is already verified and accepted', ' Rejected', 'Rejected', 'NA', ' '], priority_counters.copy(), priority_thresholds, mv_urgency_days)
        # combined_df = pd.concat([accepted_df, rejected_df]).sort_values('Priority number')

        # Exclude African maids, but keep Ethiopians
        non_african_accepted_df = accepted_df[~accepted_df['Housemaid Nationality'].isin(african_countries) | (accepted_df['Housemaid Nationality'] == 'Ethiopian')]
        non_african_rejected_df = rejected_df[~rejected_df['Housemaid Nationality'].isin(african_countries) | (rejected_df['Housemaid Nationality'] == 'Ethiopian')]
        non_african_combined_df = combined_df[~combined_df['Housemaid Nationality'].isin(african_countries) | (combined_df['Housemaid Nationality'] == 'Ethiopian')]

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            accepted_df.to_excel(writer, sheet_name='Accepted', index=False)
            rejected_df.to_excel(writer, sheet_name='Rejected', index=False)
            combined_df.to_excel(writer, sheet_name='Combined', index=False)
            
            # Add the new sheet with the filtered data (excluding Africans, but keeping Ethiopians)
            non_african_accepted_df.to_excel(writer, sheet_name='Accepted No-Africans', index=False)
            non_african_rejected_df.to_excel(writer, sheet_name='Rejected No-Africans', index=False)
            non_african_combined_df.to_excel(writer, sheet_name='Combined No-Africans', index=False)
        
        stats_div = html.Div([
            html.H4("Combined Statistics:", className="text-primary mb-4"),
            dbc.Row([
                dbc.Col([
                    html.H5("Accepted:", className="text-success"),
                    create_stats_table(accepted_stats, "Accepted")
                ], md=4),
                dbc.Col([
                    html.H5("Rejected:", className="text-danger"),
                    create_stats_table(rejected_stats, "Rejected")
                ], md=4),
                dbc.Col([  
                    html.H5("Total:", className="text-primary"),
                    create_stats_table({k: {'Males': v['Males'] + rejected_stats.get(k, {}).get('Males', 0),
                                            'Females': v['Females'] + rejected_stats.get(k, {}).get('Females', 0),
                                            'Total': v['Total'] + rejected_stats.get(k, {}).get('Total', 0)}
                                        for k, v in accepted_stats.items()}, "Total")
                ], md=4),
            ]),
        ])
        
        return dcc.send_bytes(output.getvalue(), "combined_maids_docs_report.xlsx"), stats_div, ""
    
    elif button_id == "btn-lawp-report":
        lawp_df = df[df['Outcome'] == 'LAWP']
        accepted_df, accepted_stats = process_dataframe(lawp_df, [' Approved', 'Approved', 'Maid is already verified and accepted'], priority_counters.copy(), priority_thresholds, mv_urgency_days)
        rejected_df, rejected_stats = process_dataframe(lawp_df, [' Rejected', 'Rejected', 'NA', ' '], priority_counters.copy(), priority_thresholds, mv_urgency_days)
        combined_df, _ = process_dataframe(df, [' Approved', 'Approved', 'Maid is already verified and accepted', ' Rejected', 'Rejected', 'NA', ' '], priority_counters.copy(), priority_thresholds, mv_urgency_days)
        # combined_df = pd.concat([accepted_df, rejected_df]).sort_values('Priority number')
        
        # Exclude African maids, but keep Ethiopians
        non_african_accepted_df = accepted_df[~accepted_df['Housemaid Nationality'].isin(african_countries) | (accepted_df['Housemaid Nationality'] == 'Ethiopian')]
        non_african_rejected_df = rejected_df[~rejected_df['Housemaid Nationality'].isin(african_countries) | (rejected_df['Housemaid Nationality'] == 'Ethiopian')]
        non_african_combined_df = combined_df[~combined_df['Housemaid Nationality'].isin(african_countries) | (combined_df['Housemaid Nationality'] == 'Ethiopian')]

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            accepted_df.to_excel(writer, sheet_name='Accepted LAWP', index=False)
            rejected_df.to_excel(writer, sheet_name='Rejected LAWP', index=False)
            combined_df.to_excel(writer, sheet_name='Combined LAWP', index=False)

            # Add the new sheet with the filtered data (excluding Africans, but keeping Ethiopians)
            non_african_accepted_df.to_excel(writer, sheet_name='Accepted No-Africans LAWP', index=False)
            non_african_rejected_df.to_excel(writer, sheet_name='Rejected No-Africans LAWP', index=False)
            non_african_combined_df.to_excel(writer, sheet_name='Combined No-Africans LAWP', index=False)
        

        
        stats_div = html.Div([
            html.H4("LAWP Statistics:", className="text-info mb-4"),
            dbc.Row([
                dbc.Col([
                    html.H5("Accepted LAWP:", className="text-success"),
                    create_stats_table(accepted_stats, "Accepted LAWP")
                ], md=6),
                dbc.Col([
                    html.H5("Rejected LAWP:", className="text-danger"),
                    create_stats_table(rejected_stats, "Rejected LAWP")
                ], md=6),
            ]),
        ])
        
        return dcc.send_bytes(output.getvalue(), "lawp_maids_docs_report.xlsx"), stats_div, ""
    
    elif button_id == "btn-no-lawp-report":
        non_lawp_df = df[df['Outcome'] != 'LAWP']
        accepted_df, accepted_stats = process_dataframe(non_lawp_df, [' Approved', 'Approved', 'Maid is already verified and accepted'], priority_counters.copy(), priority_thresholds, mv_urgency_days)
        rejected_df, rejected_stats = process_dataframe(non_lawp_df, [' Rejected', 'Rejected', 'NA', ' '], priority_counters.copy(), priority_thresholds, mv_urgency_days)
        combined_df, _ = process_dataframe(df, [' Approved', 'Approved', 'Maid is already verified and accepted', ' Rejected', 'Rejected', 'NA', ' '], priority_counters.copy(), priority_thresholds, mv_urgency_days)
        # combined_df = pd.concat([accepted_df, rejected_df]).sort_values('Priority number')
        
        # Exclude African maids, but keep Ethiopians
        non_african_accepted_df = accepted_df[~accepted_df['Housemaid Nationality'].isin(african_countries) | (accepted_df['Housemaid Nationality'] == 'Ethiopian')]
        non_african_rejected_df = rejected_df[~rejected_df['Housemaid Nationality'].isin(african_countries) | (rejected_df['Housemaid Nationality'] == 'Ethiopian')]
        non_african_combined_df = combined_df[~combined_df['Housemaid Nationality'].isin(african_countries) | (combined_df['Housemaid Nationality'] == 'Ethiopian')]

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            accepted_df.to_excel(writer, sheet_name='Accepted Non-LAWP', index=False)
            rejected_df.to_excel(writer, sheet_name='Rejected Non-LAWP', index=False)
            combined_df.to_excel(writer, sheet_name='Combined Non-LAWP', index=False)

            # Add the new sheet with the filtered data (excluding Africans, but keeping Ethiopians)
            non_african_accepted_df.to_excel(writer, sheet_name='Accepted No-Africans Non-LAWP', index=False)
            non_african_rejected_df.to_excel(writer, sheet_name='Rejected No-Africans Non-LAWP', index=False)
            non_african_combined_df.to_excel(writer, sheet_name='Combined No-Africans Non-LAWP', index=False)
        
        
        stats_div = html.Div([
            html.H4("Non-LAWP Statistics:", className="text-success mb-4"),
            dbc.Row([
                dbc.Col([
                    html.H5("Accepted Non-LAWP:", className="text-success"),
                    create_stats_table(accepted_stats, "Accepted Non-LAWP")
                ], md=6),
                dbc.Col([
                    html.H5("Rejected Non-LAWP:", className="text-danger"),
                    create_stats_table(rejected_stats, "Rejected Non-LAWP")
                ], md=6),
            ]),
        ])
        
        return dcc.send_bytes(output.getvalue(), "non_lawp_maids_docs_report.xlsx"), stats_div, ""

    elif button_id == "btn-top-priorities":
        # Filter for top 4 priorities
        non_lawp_df = df[df['Outcome'] != 'LAWP']
        accepted_df, accepted_stats = process_dataframe(non_lawp_df, [' Approved', 'Approved', 'Maid is already verified and accepted'], priority_counters.copy(), priority_thresholds, mv_urgency_days)
        rejected_df, rejected_stats = process_dataframe(non_lawp_df, [' Rejected', 'Rejected', 'NA', ' '], priority_counters.copy(), priority_thresholds, mv_urgency_days)
        combined_df, _ = process_dataframe(df, [' Approved', 'Approved', 'Maid is already verified and accepted', ' Rejected', 'Rejected', 'NA', ' '], priority_counters.copy(), priority_thresholds, mv_urgency_days)
        # combined_df = pd.concat([accepted_df, rejected_df]).sort_values('Priority number')

        accepted_df = accepted_df[accepted_df['Priority number'].isin([1, 2, 3, 4, 5])]
        rejected_df = rejected_df[rejected_df['Priority number'].isin([1, 2, 3, 4, 5])]
        combined_df = combined_df[combined_df['Priority number'].isin([1, 2, 3, 4, 5])]

        # Exclude African maids, but keep Ethiopians
        non_african_accepted_df = accepted_df[~accepted_df['Housemaid Nationality'].isin(african_countries) | (accepted_df['Housemaid Nationality'] == 'Ethiopian')]
        non_african_rejected_df = rejected_df[~rejected_df['Housemaid Nationality'].isin(african_countries) | (rejected_df['Housemaid Nationality'] == 'Ethiopian')]
        non_african_combined_df = combined_df[~combined_df['Housemaid Nationality'].isin(african_countries) | (combined_df['Housemaid Nationality'] == 'Ethiopian')]

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            accepted_df.to_excel(writer, sheet_name='Accepted Non-LAWP-Top', index=False)
            rejected_df.to_excel(writer, sheet_name='Rejected Non-LAWP-Top', index=False)
            combined_df.to_excel(writer, sheet_name='Combined Non-LAWP-Top', index=False)
            # Add the new sheet with the filtered data (excluding Africans, but keeping Ethiopians)
            non_african_accepted_df.to_excel(writer, sheet_name='Accepted No-Afr Non-LAWP-Top', index=False)
            non_african_rejected_df.to_excel(writer, sheet_name='Rejected No-Afr Non-LAWP-Top', index=False)
            non_african_combined_df.to_excel(writer, sheet_name='Combined No-Afr Non-LAWP-Top', index=False)
            
        
        return dcc.send_bytes(output.getvalue(), "top_priorities_report.xlsx"), "", ""

    return dash.no_update, dash.no_update, ""


# Add a callback to update the download button based on file upload
@app.callback(
    [Output("btn-combined-report", "disabled"),
    Output("btn-lawp-report", "disabled"),
    Output("btn-no-lawp-report", "disabled")],
    [Input('upload-data', 'contents')]
)
def update_download_buttons(contents):
    if contents is None:
        return True, True, True
    return False, False, False

if __name__ == '__main__':
    app.run_server(debug=True, port=7001)