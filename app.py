from dash import Dash, html

# Define the app
app = Dash(__name__)

# App layout
app.layout = html.Div("Hello, Dash!")
# Expose the underlying WSGI server instance
server = app.server

# Ensure this block is included for local development
if __name__ == "__main__":
    app.run_server(debug=True)
