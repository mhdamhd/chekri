import dash
from dash import dcc, html, Input, Output, State, callback_context
from dash.exceptions import PreventUpdate
import pandas as pd
from postRequest import postRequest
from bs4 import BeautifulSoup
import time
from datetime import datetime
import dash_bootstrap_components as dbc
import io
import base64

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Dash layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H2("MB Status Application"), className="text-center")
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col([
            html.Label("Enter MB numbers, one per line:"),
            dcc.Textarea(id="mohre-input-mb", style={"width": "100%", "height": "150px"}, placeholder="Enter each MB number on a new line"),
        ])
    ], className="mb-3"),
    
    dbc.Row([
        dbc.Col([
            html.Label("Delay between requests (seconds):"),
            dcc.Input(id="mohre-input-delay", type="number", value=1, min=0, step=0.1, className="form-control"),
        ], width=6)
    ], className="mb-3"),
    
    dbc.Row([
        dbc.Col([
            dbc.Button("Start Processing", id="mohre-start-button", color="primary", className="me-2"),
            dcc.Interval(id="mohre-interval", interval=1000, n_intervals=0, disabled=True),
            html.Div(id="mohre-progress-indicator", className="mt-3"),
        ], className="text-center")
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(html.Div(id="mohre-progress-text", className="text-center"), className="mb-2")
    ]),

    dbc.Row([
        dbc.Col(html.Div(id="mohre-download-link-container", className="text-center"), className="mb-3")
    ]),
], fluid=True)
layout = app.layout
# Variables to hold progress data across intervals
mb_data = {
    'mb_numbers': [],
    'output_df': pd.DataFrame(columns=['mb', 'Application Status', 'Transaction Type']),
    'start_time': None,
    'completed_mbs': 0,
    'total_mbs': 0,
    'delay': 1,
}

def register_callbacks(app):
    # Helper function to process each mb number
    def process_mb(inputData, delay):
        time.sleep(delay)  # Wait to avoid firewall ban
        try:
            html_content = postRequest(inputData)
            soup = BeautifulSoup(html_content, 'html.parser')
            application_status = soup.find('td', string='Application Status:').find_next_sibling('td').text.strip()
            transaction_type = soup.find('td', string='Transaction Type:').find_next_sibling('td').text.strip()
            return {'mb': inputData, 'Application Status': application_status, 'Transaction Type': transaction_type}
        except Exception:
            return {'mb': inputData, 'Application Status': 'Error', 'Transaction Type': 'Error'}
        
    # Combined callback for start and progress updates
    @app.callback(
        Output("mohre-interval", "disabled"),
        Output("mohre-progress-indicator", "children"),
        Output("mohre-progress-text", "children"),
        Output("mohre-download-link-container", "children"),
        Input("mohre-start-button", "n_clicks"),
        Input("mohre-interval", "n_intervals"),
        State("mohre-input-mb", "value"),
        State("mohre-input-delay", "value")
    )
    def handle_progress(n_clicks, n_intervals, mb_text, delay):
        # Check which input triggered the callback
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # Start button clicked, initialize processing
        if triggered_id == "mohre-start-button":
            if not mb_text:
                raise PreventUpdate
            
            # Reinitialize mb_data for a new processing batch
            mb_data.update({
                'mb_numbers': [mb.strip() for mb in mb_text.split("\n") if mb.strip()],
                'total_mbs': len(mb_data['mb_numbers']),
                'delay': delay,
                'completed_mbs': 0,
                'start_time': datetime.now(),
                'output_df': pd.DataFrame(columns=['mb', 'Application Status', 'Transaction Type']),
            })
            # Hide the download button at the start of processing
            return False, "Processing started...", f"{mb_data['total_mbs']} MBs to process.", ""

        # Interval triggered, process next MB
        if triggered_id == "mohre-interval":
            if mb_data['completed_mbs'] >= mb_data['total_mbs']:
                # Generate download link when complete
                excel_data = io.BytesIO()
                mb_data['output_df'].to_excel(excel_data, index=False, engine='openpyxl')
                excel_data.seek(0)
                download_link = "data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64," + base64.b64encode(excel_data.read()).decode()
                download_button = html.A("Download Output", id="mohre-download-link", download="processed_data.xlsx", href=download_link, target="_blank", className="btn btn-success")

                return True, "Processing complete!", f"Processed {mb_data['total_mbs']} MBs.", download_button

            current_mb = mb_data['mb_numbers'][mb_data['completed_mbs']]

            # Retry logic
            max_retries = 3
            attempt = 0
            success = False

            while attempt < max_retries and not success:
                result = process_mb(current_mb, mb_data['delay'])
                if result['Application Status'] != 'Error':
                    success = True
                    mb_data['output_df'] = pd.concat([mb_data['output_df'], pd.DataFrame([result])], ignore_index=True)
                else:
                    attempt += 1
                    if attempt == max_retries:
                        mb_data['output_df'] = pd.concat([mb_data['output_df'], pd.DataFrame([result])], ignore_index=True)

            # Update progress data
            mb_data['completed_mbs'] += 1
            elapsed_time = (datetime.now() - mb_data['start_time']).total_seconds()
            mbs_per_sec = mb_data['completed_mbs'] / elapsed_time if elapsed_time > 0 else 0
            remaining_mbs = mb_data['total_mbs'] - mb_data['completed_mbs']

            # Progress indicator and text
            progress_indicator = f"Processed {mb_data['completed_mbs']}/{mb_data['total_mbs']} MBs"
            progress_text = f"{remaining_mbs} MBs left | {mbs_per_sec:.2f} MBs/sec"

            return False, progress_indicator, progress_text, ""

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
