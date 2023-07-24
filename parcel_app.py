import pandas as pd
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import io
import base64
import urllib.parse

# Read the parcel data from the CSV file
df = pd.read_csv('/Users/knarcisi/Desktop/MGN data/Primary_Land_Use_Tax_Lot_Output__PLUTO_.csv')

# Selecting only the desired columns
columns_of_interest = [
    'borough', 'block', 'lot', 'address', 'zonedist1', 'landuse',
    'lotarea', 'ownertype', 'bldgarea', 'numbldgs', 'bbl', 'latitude', 'longitude'
]

# Create a new DataFrame with only the columns of interest
df2 = df[columns_of_interest]

# Create a dictionary to map the first letter of zoning categories to their respective labels
zoning_mapping = {
    'C': 'Commercial',
    'R': 'Residential',
    'P': 'Park',
    'M': 'Manufacturing'
}

# Extract the first letter of 'zonedist1' and map it to the corresponding label
df2['zone_category'] = df2['zonedist1'].str[0].map(zoning_mapping)

# Handle null values in 'ownertype' by replacing them with 'Unknown' or 'No Data'
df2['ownertype'].fillna('Unknown', inplace=True)

# Handle null values in 'landuse' by adding an option for 'Unknown'
df2['landuse'].fillna('Unknown', inplace=True)

# Remove rows with null values in 'zone_category'
df2 = df2.dropna(subset=['zone_category'])

# Get the actual minimum and maximum lot area values from the dataset
lotarea_min = df2['lotarea'].min()
lotarea_max = df2['lotarea'].max()

# Create the Dash app
app = dash.Dash(__name__)

# Use the same options for land use, owner type, and zone category as the borough filter
borough_options = [{'label': b, 'value': b} for b in ['All'] + df2['borough'].unique().tolist()]
landuse_options = [{'label': lu, 'value': lu} for lu in ['Unknown'] + df2['landuse'].unique().tolist()]
ownertype_options = [{'label': ot, 'value': ot} for ot in ['Unknown'] + df2['ownertype'].unique().tolist()]
zone_category_options = [{'label': zc, 'value': zc} for zc in df2['zone_category'].unique().tolist()]

# Create interactive widgets for filtering
borough_filter = dcc.Dropdown(
    id='borough-filter',
    options=borough_options,
    value=['All'],  # Default: Select 'All'
    multi=True
)

landuse_filter = dcc.Dropdown(
    id='landuse-filter',
    options=landuse_options,
    value=[landuse_options[0]['value']],  # Default: Select the first option
    multi=True
)

ownertype_filter = dcc.Dropdown(
    id='ownertype-filter',
    options=ownertype_options,
    value=[ownertype_options[0]['value']],  # Default: Select the first option
    multi=True
)

zone_category_filter = dcc.Dropdown(
    id='zone-category-filter',
    options=zone_category_options,
    value=[zone_category_options[0]['value']],  # Default: Select the first option
    multi=True
)

# Create the graph
parcel_graph = dcc.Graph(id='parcel-graph')

# Create the table figure
parcel_table = dcc.Graph(
    id='parcel-table',
    figure={
        'data': [
            {
                'type': 'table',
                'header': dict(values=['Borough', 'Parcel Count']),
                'cells': dict(values=[[], []])
            }
        ],
        'layout': {
            'title': 'Parcel Count per Borough',
            'plot_bgcolor': 'lightblue',
            'header': {
                'bgcolor': 'blue',
                'fill_color': 'blue',
                'font': {'color': 'white'}
            }
        }
    }
)

# Function to update the graph and table based on filters
@app.callback(
    [Output('parcel-graph', 'figure'),
     Output('parcel-table', 'figure'),
     Output('download-link', 'href')],
    [Input('update-graph-btn', 'n_clicks')],
    [State('borough-filter', 'value'),
     State('landuse-filter', 'value'),
     State('ownertype-filter', 'value'),
     State('zone-category-filter', 'value'),
     State('min-lotarea', 'value'),
     State('max-lotarea', 'value')]
)
def update_graph_table_download(n_clicks, borough, landuse, ownertype, zone_category, min_lotarea, max_lotarea):
    # Filter the data based on selected filters
    filtered_data = df2.copy()  # Make a copy to avoid modifying the original DataFrame

    if 'All' not in borough:  # Filter by selected boroughs only if not 'All'
        filtered_data = filtered_data[filtered_data['borough'].isin(borough)]

    if landuse:
        filtered_data = filtered_data[filtered_data['landuse'].isin(landuse)]

    if ownertype:
        filtered_data = filtered_data[filtered_data['ownertype'].isin(ownertype)]

    if zone_category:
        filtered_data = filtered_data[filtered_data['zone_category'].isin(zone_category)]

    # Filter by lotarea range
    filtered_data = filtered_data[(filtered_data['lotarea'] >= min_lotarea) & (filtered_data['lotarea'] <= max_lotarea)]

    # Calculate the parcel count based on filtered data
    parcel_count = filtered_data['borough'].value_counts().reset_index()
    parcel_count.columns = ['borough', 'Parcel Count']

    # Calculate the selected lot area range and display it
    selected_lot_area_text = f"Selected Lot Area Range: {min_lotarea} - {max_lotarea}"

    # Construct the annotation text for the graph
    annotation_text = 'Parameters:<br>'
    if landuse:
        annotation_text += f"Land Use: {', '.join(landuse)}<br>"
    if ownertype:
        annotation_text += f"Owner Type: {', '.join(ownertype)}<br>"
    if zone_category:
        annotation_text += f"Zone Category: {', '.join(zone_category)}<br>"
    annotation_text += f"Lot Area: {min_lotarea} - {max_lotarea}"

    graph_data = filtered_data.groupby('borough').size().reset_index(name='Count')

    graph = {
        'data': [dict(
            x=graph_data['borough'],
            y=graph_data['Count'],
            type='bar'
        )],
        'layout': dict(
            title=dict(text='Parcel Count per Borough', y=1.1),
            xaxis=dict(title='Borough'),
            yaxis=dict(title='Parcel Count'),
            annotations=[
                dict(
                    x=.94,
                    y=1.12,
                    xref='paper',
                    yref='paper',
                    showarrow=False,
                    text='Parameters:',
                    font=dict(size=12),
                    borderpad=4,
                    bgcolor='rgba(255,255,255,0.7)'
                ),
                dict(
                    x=1,
                    y=1.05,
                    xref='paper',
                    yref='paper',
                    showarrow=False,
                    text=annotation_text,
                    font=dict(size=12),
                    borderpad=4,
                    bgcolor='rgba(255,255,255,0.7)'
                )
            ]
        )
    }

    # Update the table figure
    table_data = [parcel_count['borough'].tolist(), parcel_count['Parcel Count'].tolist()]
    table = {
        'data': [
            {
                'type': 'table',
                'header': dict(values=['Borough', 'Parcel Count']),
                'cells': dict(values=table_data)
            }
        ],
        'layout': {
            'title': 'Parcel Count per Borough',
            'plot_bgcolor': 'lightblue',
            'header': {
                'bgcolor': 'blue',
                'fill_color': 'blue',
                'font': {'color': 'white'}
            }
        }
    }

    # Generate CSV file in memory
    csv_buffer = io.StringIO()
    filtered_data.to_csv(csv_buffer, index=False, encoding='utf-8')
    csv_buffer.seek(0)

    # Encode CSV data to base64 and create the download link
    csv_data = base64.b64encode(csv_buffer.read().encode()).decode()
    download_link = f"data:text/csv;charset=utf-8;base64,{csv_data}"

    return graph, table, download_link

# Create the layout
app.layout = html.Div([
    html.H1("Interactive Parcel Data Table"),
    html.Label('Borough:'),
    borough_filter,
    html.Label('Land Use:'),
    landuse_filter,
    html.Label('Owner Type:'),
    ownertype_filter,
    html.Label('Zone Category:'),
    zone_category_filter,
    html.Div([
        html.Label('Lot Area Range:'),
        html.Label('Min:'),
        dcc.Input(id='min-lotarea', type='number', value=lotarea_min, step=1000),
        html.Label('Max:'),
        dcc.Input(id='max-lotarea', type='number', value=lotarea_max, step=1000),
        html.Button('Update Graph', id='update-graph-btn', n_clicks=0),
    ]),
    parcel_graph,
    html.A(
        'Download Table',
        id='download-link',
        download="parcel_data.csv",
        href="",
        target="_blank"
    ),
    parcel_table
])

if __name__ == '__main__':
    app.run_server(debug=True)
