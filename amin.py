import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import pyotp
import cv2  # Import OpenCV
from PIL import Image
import time
import os
import base64
import io
import numpy as np

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
app.title = "OTP Generator"

# Global variable to store the secret key
secret_key = None

# App Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("OTP Generator with QR Code Upload"), className="text-center mt-4")
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Upload(
                id='amin-upload-qr',
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select a QR Code File')
                ]),
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
            dcc.Interval(id='amin-interval-component', interval=1000, n_intervals=0),
            html.Div(id='amin-time-left', className='text-center mt-2')
        ])
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Button("Reset QR Code", id='amin-reset-button', color='danger', className='mt-4'),
        ], width=12, className='text-center')
    ])
])
layout = app.layout
# Function to extract secret key from QR code using OpenCV

# Register callbacks
def register_callbacks(app):

    def extract_secret_from_qr(image_data):
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(img)

        if data and 'secret=' in data:
            secret = data.split('secret=')[1].split('&')[0]
            return secret
        return None

    # Callback to handle QR code upload
    @app.callback(
        Output('amin-output-message', 'children'),
        Input('amin-upload-qr', 'contents'),
        prevent_initial_call=True
    )
    def upload_qr(contents):
        global secret_key
        if contents:
            content_type, content_string = contents.split(',')
            decoded_image = base64.b64decode(content_string)
            
            # Extract secret from uploaded QR code
            new_secret_key = extract_secret_from_qr(decoded_image)
            if new_secret_key:
                secret_key = new_secret_key
                return "QR Code uploaded successfully!"
            else:
                return "Failed to read QR code. Please upload a valid QR code."

    # Callback to update OTP and time left
    @app.callback(
        [Output('amin-otp-display', 'children'),
        Output('amin-time-left', 'children')],
        [Input('amin-interval-component', 'n_intervals')]
    )
    def update_otp(n_intervals):
        if secret_key is None:
            return "No QR code uploaded yet.", ""

        # Generate the current OTP
        totp = pyotp.TOTP(secret_key)
        otp = totp.now()

        # Calculate time left until OTP refresh
        time_left = 30 - (int(time.time()) % 30)
        return f"Current OTP: {otp}", f"Time left: {time_left} seconds"

    # Callback to reset the QR code
    @app.callback(
        Output('amin-upload-qr', 'contents', allow_duplicate=True),
        Input('amin-reset-button', 'n_clicks'),
        prevent_initial_call=True
    )
    def reset_qr(n_clicks):
        global secret_key
        secret_key = None
        return None

# Register callbacks
# register_callbacks(app)

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
