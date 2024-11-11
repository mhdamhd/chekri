import dash
from dash import dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd
from postRequest import postRequest
from bs4 import BeautifulSoup
import time
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
            html.Div(id="mohre-progress-indicator", className="mt-3"),
        ], className="text-center")
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(html.Div(id="mohre-download-link-container", className="text-center"), className="mb-3")
    ]),
], fluid=True)
layout = app.layout

def register_callbacks(app):
        
    # Helper function to process each MB number
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

    # Callback for processing MB numbers and generating download link
    @app.callback(
        Output("mohre-progress-indicator", "children"),
        Output("mohre-download-link-container", "children"),
        Input("mohre-start-button", "n_clicks"),
        State("mohre-input-mb", "value"),
        State("mohre-input-delay", "value")
    )
    def handle_processing(n_clicks, mb_text, delay):
        if n_clicks is None or not mb_text:
            raise PreventUpdate

        # Show "Processing..." message
        progress_message = "Processing..."

        # Process all MB numbers at once
        mb_numbers = [mb.strip() for mb in mb_text.split("\n") if mb.strip()]
        results = []

        for mb in mb_numbers:
            # Retry logic for each MB number
            max_retries = 3
            attempt = 0
            success = False
            while attempt < max_retries and not success:
                result = process_mb(mb, delay)
                if result['Application Status'] != 'Error':
                    success = True
                else:
                    attempt += 1
            results.append(result)

        # Create DataFrame and Excel file
        output_df = pd.DataFrame(results)
        excel_data = io.BytesIO()
        output_df.to_excel(excel_data, index=False, engine='openpyxl')
        excel_data.seek(0)
        download_link = "data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64," + base64.b64encode(excel_data.read()).decode()
        download_button = html.A("Download Output", id="mohre-download-link", download="processed_data.xlsx", href=download_link, target="_blank", className="btn btn-success")

        return progress_message, download_button

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
