import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import importlib

# Initialize the main Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Multi-App Dashboard"
server = app.server  # For deployment

# Sidebar with navigation links to the different apps
sidebar = dbc.Nav(
    [
        dbc.NavLink("Prioritization", href="/prioritization", active="exact"),
        dbc.NavLink("Replacement Distribution Local", href="/distribution_local", active="exact"),
        dbc.NavLink("Quota Distribution Local", href="/quota_local", active="exact"),
        dbc.NavLink("Replacement Distribution Remote", href="/distribution_remote", active="exact"),
        dbc.NavLink("Quota Distribution Remote", href="/quota_remote", active="exact"),
        dbc.NavLink("Links Distribution Remote", href="/links_remote", active="exact"),
        dbc.NavLink("Merge Priorities", href="/merge_priorities", active="exact"),
        # Add new apps here without modifying their code
    ],
    vertical=True,
    pills=True,
    className="bg-light"
)

# Layout with a sidebar and dynamic page content
app.layout = dbc.Container([
    dcc.Location(id='url', refresh=False),
    dbc.Row([
        dbc.Col(sidebar, width=2),
        dbc.Col(html.Div(id='page-content'), width=10),
    ])
], fluid=True)

# Dynamically load the correct app layout and register callbacks
@app.callback(Output('page-content', 'children'), [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/prioritization':
        module = importlib.import_module('priorities')  # Dynamically import the module
        module.register_callbacks(app)  # Register callbacks dynamically
        return module.app.layout  # Return the layout from the module

    elif pathname == '/distribution_local':
        module = importlib.import_module('replacement_distribution')  # Distribution
        module.register_callbacks(app)  # Register callbacks dynamically
        return module.app.layout

    elif pathname == '/quota_local':
        module = importlib.import_module('quota_distribution')  # Distribution
        module.register_callbacks(app)  # Register callbacks dynamically
        return module.app.layout

    elif pathname == '/distribution_remote':
        module = importlib.import_module('replacement_distribution_remote')  # Distribution
        module.register_callbacks(app)  # Register callbacks dynamically
        return module.app.layout

    elif pathname == '/quota_remote':
        module = importlib.import_module('quota_distribution_remote')  # Distribution
        module.register_callbacks(app)  # Register callbacks dynamically
        return module.app.layout

    elif pathname == '/links_remote':
        module = importlib.import_module('links_distribution_remote')  # Distribution
        module.register_callbacks(app)  # Register callbacks dynamically
        return module.app.layout

    elif pathname == '/merge_priorities':
        module = importlib.import_module('merge_priorities')  # Distribution
        module.register_callbacks(app)  # Register callbacks dynamically
        return module.app.layout

    else:
        return html.Div("Welcome to the Dashboard")

if __name__ == '__main__':
    app.run_server(debug=True)
