import json
import os
import dash
from dash import html, dcc, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from awp_requests import login, getAWP, verifyOtp

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
            dcc.Input(id="ayoub-username-input", type="text", placeholder="Enter Username"),
            className="mb-4"
        ),
        dbc.Col(
            dcc.Input(id="ayoub-password-input", type="password", placeholder="Enter Password"),
            className="mb-4"
        ),
    ]),
    dbc.Row([
        dbc.Col(
            dbc.Button("Login and Refresh Table", id="ayoub-login-button", color="primary", n_clicks=0),
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
                children=html.Div(id="ayoub-output", children="Click the login button to refresh the table.")
            )
        )
    ]),
    # OTP Modal
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Enter OTP")),
        dbc.ModalBody(
            dcc.Input(id="ayoub-otp-input", type="text", placeholder="Enter OTP code")
        ),
        dbc.ModalFooter(
            dbc.Button("Submit OTP", id="ayoub-submit-otp-button", className="ms-auto", n_clicks=0)
        ),
    ], id="ayoub-otp-modal", is_open=False)
], fluid=True)
layout = app.layout
# Global token storage
app_token = None

def register_callbacks(app):
    # Helper Function to Update Google Sheet
    def update_google_sheet(token):
        # Authenticate and connect to Google Sheets
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(SERVICE_ACCOUNT_INFO, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1

        # Get the response data
        res = getAWP(token)

        # Prepare data for the DataFrame
        data = []
        for task in res:
            for request in task['requests']:
                task_move_in = request.get("taskMoveInDateWithDaysCount", "")
                date_part, days_part = task_move_in.split(" - ") if " - " in task_move_in else ("", "")

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
                    "Task Move In Date": date_part,
                    "Days Count": days_part.strip("()").replace(" days", ""),  # Remove parentheses from days count
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

    # Combined Callback for Login and OTP Verification
    @app.callback(
        Output("ayoub-otp-modal", "is_open"),
        Output("ayoub-output", "children"),
        Input("ayoub-login-button", "n_clicks"),
        Input("ayoub-submit-otp-button", "n_clicks"),
        State("ayoub-username-input", "value"),
        State("ayoub-password-input", "value"),
        State("ayoub-otp-input", "value"),
        prevent_initial_call=True
    )
    def handle_login_and_otp(login_clicks, otp_clicks, username, password, otp_code):
        global app_token
        ctx = callback_context
        if not ctx.triggered:
            return False, ""
        
        # Identify which button was clicked
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # Login button was clicked
        if triggered_id == "ayoub-login-button":
            try:
                app_token = login(username, password)
                if app_token:
                    return True, "Login successful. Please enter the OTP."
                else:
                    return False, "Login failed. Please check your credentials."
            except Exception as e:
                return False, f"An error occurred: {e}"

        # OTP submit button was clicked
        elif triggered_id == "ayoub-submit-otp-button":
            try:
                verified = verifyOtp(app_token, otp_code)
                if not verified:
                    # OTP failed, reopen modal
                    return True, "OTP verification failed. Please try again."
                
                # OTP successful, update Google Sheet and close modal
                message = update_google_sheet(app_token)
                return False, message  # Close the modal and display the message
            except Exception as e:
                return False, f"An error occurred: {e}"

        return False, ""

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
