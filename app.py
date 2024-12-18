import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from priorities import layout as prioritization_layout, register_callbacks as prioritization_callbacks
from replacement_distribution import layout as replacement_distribution_layout, register_callbacks as replacement_distribution_callbacks
from quota_distribution import layout as quota_distribution_layout, register_callbacks as quota_distribution_callbacks
from replacement_distribution_remote import layout as replacement_distribution_remote_layout, register_callbacks as replacement_distribution_remote_callbacks
from quota_distribution_remote import layout as quota_distribution_remote_layout, register_callbacks as quota_distribution_remote_callbacks
from links_distribution_remote import layout as links_distribution_remote_layout, register_callbacks as links_distribution_remote_callbacks
from merge_priorities import layout as merge_priorities_layout, register_callbacks as merge_priorities_layout_callbacks
from amin import layout as amin_layout, register_callbacks as amin_callbacks
from get_awp_dash import layout as awp_layout, register_callbacks as awp_callbacks
from mohre_application_status import layout as mohre_layout, register_callbacks as mohre_callbacks
from combined_stats_table import layout as stats_layout, register_callbacks as stats_callbacks
# Add other apps as needed

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Multi-App Dashboard"
server = app.server

# Sidebar with navigation links to the different apps
sidebar = dbc.Nav(
    [
        dbc.NavLink("Prioritization", href="/prioritization", active="exact"),
        # dbc.NavLink("Replacement Distribution Local", href="/distribution_local", active="exact"),
        # dbc.NavLink("Quota Distribution Local", href="/quota_local", active="exact"),
        
        dbc.NavLink("Quota Distribution", href="/quota_remote", active="exact"),
        dbc.NavLink("Replacement Distribution", href="/distribution_remote", active="exact"),
        dbc.NavLink("Links Distribution Remote", href="/links_remote", active="exact"),
        dbc.NavLink("Merge Priorities", href="/merge_priorities", active="exact"),
        dbc.NavLink("Priorities Stats", href="/priorities_stats", active="exact"),
        dbc.NavLink("AWP", href="/awp", active="exact"),
        dbc.NavLink("Mohre App-Status", href="/mohre_app_status", active="exact"),
        dbc.NavLink("Amin", href="/amin", active="exact"),
        # Add other links here
    ],
    vertical=True,
    pills=True,
    className="bg-light"
)

app.layout = dbc.Container([
    dcc.Location(id='url', refresh=False),
    dbc.Row(id='main-row')
], fluid=True)

# Callback to manage sidebar visibility and page content
@app.callback(
    Output('main-row', 'children'),
    Input('url', 'pathname')
)
def update_layout(pathname):
    if pathname == '/amin':
        # If the path is '/amin', hide the sidebar and show only the main content
        return dbc.Col(html.Div(amin_layout), width=12)
    else:
        # For other paths, show the sidebar and main content
        return [
            dbc.Col(sidebar, width=2),
            dbc.Col(html.Div(display_page(pathname)), width=10)
        ]


# Main callback to load the appropriate page
@app.callback(Output('page-content', 'children'), [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/prioritization':
        return prioritization_layout
    # elif pathname == '/distribution_local':
    #     return replacement_distribution_layout
    # elif pathname == '/quota_local':
    #     return quota_distribution_layout
    elif pathname == '/quota_remote':
        return quota_distribution_remote_layout
    elif pathname == '/distribution_remote':
        return replacement_distribution_remote_layout
    elif pathname == '/links_remote':
        return links_distribution_remote_layout
    elif pathname == '/merge_priorities':
        return merge_priorities_layout
    elif pathname == '/priorities_stats':
        return stats_layout
    elif pathname == '/awp':
        return awp_layout
    elif pathname == '/mohre_app_status':
        return mohre_layout
    elif pathname == '/amin':
        return amin_layout
    else:
        return html.Div("Welcome to the Dashboard")

# Register callbacks for each app

# replacement_distribution_callbacks(app)
# quota_distribution_callbacks(app)

prioritization_callbacks(app)
quota_distribution_remote_callbacks(app)
replacement_distribution_remote_callbacks(app)
links_distribution_remote_callbacks(app)
merge_priorities_layout_callbacks(app)
stats_callbacks(app)
awp_callbacks(app)
mohre_callbacks(app)
amin_callbacks(app)


if __name__ == '__main__':
    app.run_server(debug=True)
