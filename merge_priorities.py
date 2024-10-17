import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import io
import base64

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define the layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Work Permit Prioritization App", className="text-center")),
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Upload(id='upload-priorities', children=html.Div(['Drag and Drop or ', html.A('Select Priorities File')]), style={
                'width': '100%', 'height': '60px', 'lineHeight': '60px', 'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px', 'textAlign': 'center'}, multiple=False),
            html.Div(id='output-priorities')
        ], width=4),
        dbc.Col([
            dcc.Upload(id='upload-allmaids', children=html.Div(['Drag and Drop or ', html.A('Select All Maids File')]), style={
                'width': '100%', 'height': '60px', 'lineHeight': '60px', 'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px', 'textAlign': 'center'}, multiple=False),
            html.Div(id='output-allmaids')
        ], width=4),
        dbc.Col([
            dcc.Upload(id='upload-newmaids', children=html.Div(['Drag and Drop or ', html.A('Select New Maids File')]), style={
                'width': '100%', 'height': '60px', 'lineHeight': '60px', 'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px', 'textAlign': 'center'}, multiple=False),
            html.Div(id='output-newmaids')
        ], width=4),
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Input(id='priority_number', type='number', placeholder='Priority Number'),
            dbc.Input(id='priority_name', type='text', placeholder='Priority Name'),
            dbc.Input(id='max_maids', type='number', placeholder='Max Maids', value=100),
            dbc.Button("Merge", id="merge-button", color="primary", className="mt-3")
        ])
    ]),
    dbc.Row([
        dbc.Col(html.Div(id='output-merge-status'))
    ]),
    dcc.Download(id="download-priorities")
])


def register_callbacks(app):
    
    # Helper functions to process files and handle merging
    def parse_contents(contents, filename):
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        if 'xlsx' in filename:
            return pd.read_excel(io.BytesIO(decoded))
        else:
            return None

    def classify_maid(maid_row):
        """Classify the maid as accepted or rejected based on the document status."""
        docs_status = maid_row.get('Docs status')
        if docs_status in [' Rejected', 'Rejected', 'NA', ' ']:
            return 'Rejected'
        elif docs_status in [' Approved', 'Approved', 'Maid is already verified and accepted']:
            return 'Accepted'
        return None

    # Callback to handle file uploads and show success messages
    @app.callback(
        Output('output-priorities', 'children'),
        Input('upload-priorities', 'filename')
    )
    def update_priorities_output(filename):
        if filename is not None:
            return html.Div(f"File uploaded successfully: {filename}")
        return ""

    @app.callback(
        Output('output-allmaids', 'children'),
        Input('upload-allmaids', 'filename')
    )
    def update_allmaids_output(filename):
        if filename is not None:
            return html.Div(f"File uploaded successfully: {filename}")
        return ""

    @app.callback(
        Output('output-newmaids', 'children'),
        Input('upload-newmaids', 'filename')
    )
    def update_newmaids_output(filename):
        if filename is not None:
            return html.Div(f"File uploaded successfully: {filename}")
        return ""

    # Callback to handle file uploads and merging
    @app.callback(
        Output('output-merge-status', 'children'),
        Output("download-priorities", "data"),
        Input('merge-button', 'n_clicks'),
        State('upload-priorities', 'contents'),
        State('upload-allmaids', 'contents'),
        State('upload-newmaids', 'contents'),
        State('priority_number', 'value'),
        State('priority_name', 'value'),
        State('max_maids', 'value'),
        prevent_initial_call=True
    )
    def merge_files(n_clicks, priorities_contents, allmaids_contents, newmaids_contents, priority_number, priority_name, max_maids):
        if not all([priorities_contents, allmaids_contents, newmaids_contents]):
            return "Please upload all required files.", None

        # Parse the uploaded Excel files
        priorities_file = parse_contents(priorities_contents, 'priorities.xlsx')
        allmaids_df = parse_contents(allmaids_contents, 'allmaids.xlsx')
        newmaids_df = parse_contents(newmaids_contents, 'newmaids.xlsx')

        if priorities_file is None or allmaids_df is None or newmaids_df is None:
            return "Error processing files.", None

        # Use pd.ExcelFile to get access to sheet names
        priorities_excel = pd.ExcelFile(io.BytesIO(base64.b64decode(priorities_contents.split(',')[1])))

        # Check if the required sheets exist
        if len(priorities_excel.sheet_names) >= 2:
            accepted_df = pd.read_excel(priorities_excel, sheet_name=priorities_excel.sheet_names[0])
            rejected_df = pd.read_excel(priorities_excel, sheet_name=priorities_excel.sheet_names[1])
        else:
            return "Error: The priorities file must contain at least two sheets.", None


        # Process each maid in newmaids.xlsx
        for _, new_maid in newmaids_df.iterrows():
            request_id = new_maid['Request ID']
            maid_info = allmaids_df[allmaids_df['Request ID'] == request_id]

            if maid_info.empty:
                continue

            # Check if MB? or Has Contract MB? is 'Yes'
            if maid_info['MB?'].values[0] == 'Yes' or maid_info['Has Contract MB?'].values[0] == 'Yes':
                continue

            # Fill missing 'Housemaid Type' and 'Gender' from allmaids
            new_maid['Housemaid Type'] = maid_info['Housemaid Type'].values[0]
            new_maid['Gender'] = maid_info['Gender'].values[0]
            new_maid['Been in the table for (in days)'] = None  # Leave this empty for new maids

            status = classify_maid(maid_info.iloc[0])

            # Prepare the new row with priority number and name
            new_row = new_maid.copy()
            new_row['Priority number'] = priority_number if priority_number else 24
            new_row['Priority Name'] = priority_name if priority_name else 'new'

            # Determine where to insert: top of the rows with the same priority number
            if status == 'Accepted':
                existing_maid_index = accepted_df[accepted_df['Request ID'] == request_id].index
                if not existing_maid_index.empty:
                    # Maid exists, update priority number and name
                    existing_maid = accepted_df.loc[existing_maid_index[0]]
                    old_priority_number = existing_maid['Priority number']
                    old_priority_number = int(old_priority_number)
                    old_priority_name = existing_maid['Priority Name']
                    priority_number = priority_number if priority_number else 24
                    if priority_number > old_priority_number:
                        # Smaller or equal priority number: only update name
                        accepted_df.at[existing_maid_index[0], 'Priority Name'] = f"{priority_name if priority_name else 'new'} - {old_priority_name}"
                    else:
                        # Larger priority number: update both number and name, move maid
                        accepted_df.drop(existing_maid_index[0], inplace=True)
                        new_row['Priority number'] = priority_number  # Ensure priority number is updated
                        new_row['Priority Name'] = f"{priority_name if priority_name else 'new'} - {old_priority_name}"
                        insert_index = get_priority_top_index(accepted_df, new_row, 'Priority number')
                        accepted_df = pd.concat([accepted_df.iloc[:insert_index], pd.DataFrame([new_row]), accepted_df.iloc[insert_index:]]).reset_index(drop=True)
                else:
                    # Maid does not exist, insert new maid
                    insert_index = get_priority_top_index(accepted_df, new_row, 'Priority number')
                    accepted_df = pd.concat([accepted_df.iloc[:insert_index], pd.DataFrame([new_row]), accepted_df.iloc[insert_index:]]).reset_index(drop=True)

            elif status == 'Rejected':
                existing_maid_index = rejected_df[rejected_df['Request ID'] == request_id].index
                if not existing_maid_index.empty:
                    # Maid exists, update priority number and name
                    existing_maid = rejected_df.loc[existing_maid_index[0]]
                    old_priority_number = existing_maid['Priority number']
                    old_priority_number = int(old_priority_number)
                    old_priority_name = existing_maid['Priority Name']
                    priority_number = priority_number if priority_number else 24

                    if priority_number > old_priority_number:
                        # Larger priority number: only update name
                        rejected_df.at[existing_maid_index[0], 'Priority Name'] = f"{priority_name if priority_name else 'new'} - {old_priority_name}"
                    else:
                        # Smaller or equal priority number: update both number and name, move maid
                        rejected_df.drop(existing_maid_index[0], inplace=True)
                        new_row['Priority number'] = priority_number  # Ensure priority number is updated
                        new_row['Priority Name'] = f"{priority_name if priority_name else 'new'} - {old_priority_name}"
                        insert_index = get_priority_top_index(rejected_df, new_row, 'Priority number')
                        rejected_df = pd.concat([rejected_df.iloc[:insert_index], pd.DataFrame([new_row]), rejected_df.iloc[insert_index:]]).reset_index(drop=True)
                else:
                    # Maid does not exist, insert new maid
                    insert_index = get_priority_top_index(rejected_df, new_row, 'Priority number')
                    rejected_df = pd.concat([rejected_df.iloc[:insert_index], pd.DataFrame([new_row]), rejected_df.iloc[insert_index:]]).reset_index(drop=True)

        # Limit the number of maids in the final output if max_maids is set
        if max_maids:
            accepted_df = accepted_df.head(max_maids)
            rejected_df = rejected_df.head(max_maids)

        # Save the updated priorities.xlsx file
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            accepted_df.to_excel(writer, sheet_name='Accepted', index=False)
            rejected_df.to_excel(writer, sheet_name='Rejected', index=False)

        return "Merge completed.", dcc.send_bytes(output.getvalue(), "priorities_updated.xlsx")


    def get_priority_top_index(df, new_row, priority_col):
        """
        Find the index to insert a new row at the top of the same priority number.
        """
        # Find the index of the first row with the same priority number
        same_priority_rows = df[df[priority_col] == new_row[priority_col]]
        
        if not same_priority_rows.empty:
            # Return the index of the first occurrence of the same priority number
            return same_priority_rows.index[0]
        # If no such priority exists, append to the end
        return len(df)


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
