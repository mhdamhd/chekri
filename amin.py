import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import pyotp
import cv2
import base64
import io
import numpy as np
import time

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
app.title = "OTP Generator"

DEFAULT_SECRET_KEY = "KMGXHPTI6ZEW5RWT"


# App Layout
app.layout = dbc.Container([
    # Hidden storage for secret key
    dcc.Store(id='amin-secret-key-store', storage_type='memory'),

    dbc.Row([
        dbc.Col(html.H1("OTP Generator with QR Code Upload"), className="text-center mt-4")
    ]),

    dbc.Row([
        dbc.Col([
            dcc.Upload(
                id='amin-upload-qr',
                children=html.Div(['Drag and Drop or ', html.A('Select a QR Code File')]),
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '10px'
                },
                multiple=False
            ),
            html.Div(id='amin-output-message', className='text-center mt-2'),
        ], width=6, className='offset-md-3')
    ]),

    dbc.Row([
        dbc.Col([
            html.H2(id='amin-otp-display', className='text-center mt-4'),
            html.Div(id='amin-time-left', className='text-center mt-2'),
            dcc.Interval(id='amin-interval-component', interval=1000, n_intervals=0)
        ])
    ]),

    dbc.Row([
        dbc.Col([
            dbc.Button("Reset QR Code", id='amin-reset-button', color='danger', className='mt-4'),
        ], width=12, className='text-center')
    ])
])
layout = app.layout


def register_callbacks(app):
        
    # Extract secret from QR code using OpenCV
    def extract_secret_from_qr(image_data):
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(img)
        if data and 'secret=' in data:
            secret = data.split('secret=')[1].split('&')[0]
            return secret
        return None

    # Handle QR code upload and reset
    @app.callback(
        [Output('amin-secret-key-store', 'data'),
        Output('amin-output-message', 'children')],
        [Input('amin-upload-qr', 'contents'),
        Input('amin-reset-button', 'n_clicks')],
        prevent_initial_call=True
    )
    def handle_qr_upload_or_reset(contents, reset_n_clicks):
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update, dash.no_update

        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if triggered_id == 'amin-upload-qr' and contents:
            content_type, content_string = contents.split(',')
            decoded_image = base64.b64decode(content_string)
            new_secret_key = extract_secret_from_qr(decoded_image)

            if new_secret_key:
                return new_secret_key, "QR Code uploaded successfully!"
            else:
                return None, "Failed to read QR code. Please upload a valid QR code."

        if triggered_id == 'amin-reset-button':
            return None, "QR code reset successfully."

        return dash.no_update, dash.no_update

    # Update OTP and countdown timer
    @app.callback(
        [Output('amin-otp-display', 'children'),
        Output('amin-time-left', 'children')],
        [Input('amin-interval-component', 'n_intervals')],
        [State('amin-secret-key-store', 'data')]
    )
    def update_otp(n_intervals, secret_key):
        if not secret_key:
            secret_key = DEFAULT_SECRET_KEY

        # Generate the current OTP
        totp = pyotp.TOTP(secret_key)
        otp = totp.now()

        # Calculate time left until OTP refresh
        time_left = 30 - (int(time.time()) % 30)
        return f"Current OTP: {otp}", f"Time left: {time_left} seconds"

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
