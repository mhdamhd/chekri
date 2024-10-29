import json
import os
import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from awp_requests import login, getAWP

# Google Sheet ID and Service Account Key
SPREADSHEET_ID = '1v1sIz1-Y90oX6tBTSnSGay_xtn_USIzd5VTIbptXcDc'
# SERVICE_ACCOUNT_FILE = 'service_account_key.json'
service_account_key = os.environ.get('SERVICE_ACCOUNT_KEY', '{}')
SERVICE_ACCOUNT_INFO = json.loads(service_account_key)

# Dash App Initialization
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# App Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Ayoub for Work Permit"), className="mb-4")
    ]),
    dbc.Row([
        dbc.Col(
            dbc.Button("Refresh the Table", id="ayoub-refresh-button", color="primary", n_clicks=0),
            className="mb-4"
        ),
    ]),
    dbc.Row([
        dbc.Col(
            dbc.Button("Open Google Sheet", id="ayoub-open-sheet-button", color="secondary", href="https://docs.google.com/spreadsheets/d/1v1sIz1-Y90oX6tBTSnSGay_xtn_USIzd5VTIbptXcDc/edit?gid=0#gid=0", target="_blank"),
            className="mb-4"
        ),
    ]),
    dbc.Row([
        dbc.Col(
            dcc.Loading(
                id="ayoub-loading",
                type="default",
                children=html.Div(id="ayoub-output", children="Click the button to refresh the table.")
            )
        )
    ])
], fluid=True)
layout = app.layout


def register_callbacks(app):
        
    # Helper Function to Update Google Sheet
    def update_google_sheet():
        # Authenticate and connect to Google Sheets
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(SERVICE_ACCOUNT_INFO, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1

        # Get the token and response data
        token = login()
        res = getAWP(token)

        # Prepare data for the DataFrame
        data = []
        for task in res:
            for request in task['requests']:
                data.append({
                    "Request ID": request.get("id", ""),
                    "Housemaid Name": request.get("housemaidName", ""),
                    "Nationality": request.get("nationality", ""),
                    "Has MB?": "Yes" if request.get("mb") else "No",
                    "MB": request.get("mb", ""),
                    "Contract MB?": "Yes" if request.get("contractMb") else "No",
                    "Contract MB": request.get("contractMb", ""),
                    "Has Offer Letter Number?": "Yes" if request.get("offerLetterNumber") else "No",
                    "Offer Letter Number": request.get("offerLetterNumber", ""),
                    "Excluded?": request.get("rpaExcluded", ""),
                    "Task Move In Date with Days Count": request.get("taskMoveInDateWithDaysCount", ""),
                    "Type": request.get("type", ""),
                    "Housemaid Status": request.get("housemaidStatus", ""),
                    "Is Live Out": request.get("isLiveOut", ""),
                    "RPA Status": request.get("rpaStatus", ""),
                    "Snoozed Tasks": ', '.join(request.get("snoozedTasks", [])),  # Convert list to comma-separated string
                    "Task Modified Date": request.get("taskModifiedDate", ""),
                    "RPA Portal": request.get("rpaPortal", "")
                })

        # Create a DataFrame from the data
        df = pd.DataFrame(data)

        # Convert the DataFrame to a list of lists (for Google Sheets)
        data_to_write = [df.columns.tolist()] + df.values.tolist()

        # Clear the existing data in the Google Sheet and write the new data
        sheet.clear()
        sheet.insert_rows(data_to_write, 1)

        return "Google Sheet has been successfully updated."

    # Callback to Refresh Google Sheet
    @app.callback(
        Output("ayoub-output", "children"),
        Input("ayoub-refresh-button", "n_clicks"),
        prevent_initial_call=True
    )
    def refresh_google_sheet(n_clicks):
        try:
            # Update the Google Sheet
            message = update_google_sheet()
            return message
        except Exception as e:
            # Return the error message
            return f"An error occurred: {e}"

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
