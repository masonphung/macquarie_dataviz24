import dash
from dash import clientside_callback
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
# Load pre-defined functions that help our work
from utils import *



# Load the dataset
file_path = 'dataset/cleaned_emrat.xlsx'
data = pd.read_excel(file_path)


#### I. DATA & FUNCTIONS PREPARATION 
# Make sure datatypes are correct
data['last_update'] = pd.to_datetime(data['last_update'], errors='coerce')
# In dash, there is a problem with int64 dtype that'll not allow the dashboard to run.
# `year` is currently int64 and we work around this by converting `year` to str.
# When plotting with plotly, we'll convert it back to int later.
data['year'] = data['year'].astype(str)

# Calculate key statistics
## Total statistics
total_deaths = data['total_deaths'].sum()
total_affected = data['total_affected'].sum()
total_damage = data['total_damage'].sum()

## Most statistics
most_deaths_country = data.groupby('country')['total_deaths'].sum().idxmax()
most_affected_country = data.groupby('country')['total_affected'].sum().idxmax()
most_damaged_country = data.groupby('country')['total_damage'].sum().idxmax()

# Last update date
last_updated = data['last_update'].max()

# Prepare Year + Month filter data
data['YearMonth'] = data['year'].astype(str) + '-' + data['month'].astype(str)

# Get unique values for the dropdowns
years = sorted(data['year'].unique())
months = sorted(data['month'].unique())
continents = sorted(data['region'].unique())
subregions = sorted(data['subregion'].unique())
countries = sorted(data['country'].unique())
disaster_types = sorted(data['type'].unique())

# Get max-min year
max_year = max(years)
min_year = min(years)




#### DASH APP
app = dash.Dash(
    __name__, 
    # Apply external bootstrap theme
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    # Tweaks meta tags for a better compatibility with devices
    meta_tags=[
        {'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0, maximum-scale=1.2, minimum-scale=0.5'},
        {"name": "description", "content": "A dash Dashboard app provides global insights about natural disasters."},
        {"property": "og:title", "content": "Global Disaster Statistics Dashboard"},
        {"property": "og:description", "content": "Explore global natural disasters and their economic impacts through interactive visuals"},
        {"property": "og:image", "content": "./assets/images/dataviz-dash1.png"},
        {"property": "og:type", "content": "website"},
        {"name": "twitter:card", "content": "summary_large_image"},
        {"name": "twitter:title", "content": "Global Disaster Statistics Dashboard"},
        {"name": "twitter:description", "content": "Explore global natural disasters and their economic impacts through interactive visuals"},
        {"name": "twitter:image", "content": "./assets/images/dataviz-dash1.png"},
    ]
)
app.title = "Global Disaster Statistics - DataViz 2024"
server = app.server

# Layout of the dashboard: Consists of 2 rows.
# R1 includes the title and filter bars.
# R2 includes the dashboard cards (statistics & charts).
# There'll be more detailed layers in each of the rows.
app.layout = html.Div([
    # Row 1: Title and filter bar
    dbc.Row([
        # Col 1 of Row 1: Dashboard title
        dbc.Col(
            [html.H1('Global Disaster Statistics'),
             html.P(id='last-updated-card')],
            className = ['align-items-center', 'flex-column', 'text-center', 'justify-content-center','align-content-center'],
            xs=12, sm=12, md=12, lg=2, xl=2 # Match with Col 2 of Row 1
        ),
        # Col 2 of Row 1: Filters
        dbc.Col(
            [
            dbc.Card([
            # Must make all filters in the same row as we can't directly have a `dbc.Col` inside a `dbc.Col`
            dbc.Row([
                # Filter 1: Year and Month (Year above Month)
                dbc.Col([
                    html.Div([
                        # Year slider
                        html.Label(
                            'Year',
                            id = 'tt-year',
                            style={'cursor':'pointer'}
                        ),
                        dbc.Tooltip(
                            'Pull both the slider bar to change the year period. If you want to select a single year, pull them together at the same place.',
                            target='tt-year'
                        ),
                        dcc.RangeSlider(
                            # There is an developer's issue with dtype int64 (data['year'] dtype) with dcc.RangeSlider.
                            # We'll have to state the years manually in this part.
                            id='year-slider',
                            min=2000, 
                            max=2024, 
                            step=1,
                            value=[2000, 2024],
                            marks={str(i): {'label': str(i)} for i in range(2000, 2025, 4)},
                            tooltip={"placement": "bottom", "always_visible": True},
                            #className="form-range"
                        ),
                        
                        # Month dropdown
                        html.Label(
                            'Month',
                            id='tt-month',
                            style={'cursor':'pointer'}
                        ),
                        dbc.Tooltip(
                            'Select the preferred month for the filter. Multiple months can be selected.',
                            target='tt-month'
                        ),
                        dcc.Dropdown(
                            id='month-dropdown',
                            options=[
                                {'label': 'January', 'value': 1},
                                {'label': 'February', 'value': 2},
                                {'label': 'March', 'value': 3},
                                {'label': 'April', 'value': 4},
                                {'label': 'May', 'value': 5},
                                {'label': 'June', 'value': 6},
                                {'label': 'July', 'value': 7},
                                {'label': 'August', 'value': 8},
                                {'label': 'September', 'value': 9},
                                {'label': 'October', 'value': 10},
                                {'label': 'November', 'value': 11},
                                {'label': 'December', 'value': 12}],
                            placeholder='Select Month',
                            multi=True
                        ),
                        dbc.Row([
                            html.Div([
                                dbc.Button("Reset Filter", id="clear-filter"),
                                dbc.Button("Dashboard Guide", id="open-modal"),
                                html.Div("Press Reset Filter if the plots don't load", style = {"fontSize": "14px", "textAlign":"center"}),
                                dbc.Modal(
                                    [
                                        dbc.ModalHeader(dbc.ModalTitle("How to use the dashboard")),
                                        dbc.ModalBody(
                                            html.Div([
                                                html.P(
                                                    "Welcome to Team A's Global Disaster Statistics Dashboard! There are 3 filters to help you view the data from different perspectives, including:",
                                                    style={'marginBottom': '5px'}  # Reduced margin
                                                ),
                                                html.Ul(
                                                    [
                                                        html.Li("Time filter (year and month)"),
                                                        html.Li("Geographical filter (Continent/Subregion/Country)"),
                                                        html.Li("Disaster filter (different types of disasters)"),
                                                    ],
                                                    style={'marginLeft': '20px', 'marginBottom': '5px'}  # Adjusted margin
                                                ),
                                                html.P(
                                                    "To apply the filters to the dashboard, select your preferred attributes and choose the values you desire. Multiple values can be chosen in each filter.",
                                                    style={'marginBottom': '5px'}  # Reduced margin
                                                ),
                                                html.P(
                                                    "To reset the filters, press the 'Reset Filter' button.",
                                                    style={'marginBottom': '5px'}  # Reduced margin
                                                ),
                                                html.P(
                                                    "Point at each label to see hints and explanations related to the components/statistics.",
                                                    style={'marginBottom': '5px'}  # Reduced margin
                                                ),
                                                html.P(
                                                    "At each plot, hover on data points on the graphs to see detailed information about the presenting data.",
                                                    style={'marginBottom': '5px'}  # Reduced margin
                                                ),
                                                html.P(
                                                    "Plotly offers useful interaction to play with the plots, which you can find in the hidden bar on the top right of each graph:",
                                                    style={'marginBottom': '5px'}  # Reduced margin
                                                ),
                                                html.Ul(
                                                    [
                                                        html.Li("Click the 'Camera' icon to download the current plot as a picture."),
                                                        html.Li("'Pan' icon helps navigate the content inside the plot."),
                                                        html.Li("You can choose the data zone using the 'Box' or 'Lasso' select tool, which helps to filter the selected data."),
                                                        html.Li("Zoom in and zoom out with '+' and '-' buttons."),
                                                        html.Li("To reset the applied Plotly interaction, press the 'Reset' icon."),
                                                    ],
                                                    style={'marginLeft': '20px', 'marginBottom': '5px'}  # Adjusted margin
                                                ),
                                                html.P(
                                                    "The dashboard was initially made for Macquarie DataViz challenge 2024 entry by Team A: @Mason, @Erik, @Anh Duc @Viet Anh. Feel free to contact us for discussions and let us know if we can improve anything: pphungwork@gmail.com (Mason).",
                                                    style={'marginBottom': '5px'}  # Reduced margin
                                                ),
                                            ])
                                        ),
                                        dbc.ModalFooter(
                                            dbc.Button(
                                                "I got it!", id="close-modal", className="ms-auto", n_clicks=0
                                            )
                                        ),
                                    ],
                                    id="modal",
                                    is_open=False,
                                ),
                                
                                # dbc.Button("Download as JPG", id='download-image') # Under development
                            ], className='d-flex align-items-center justify-content-between')
                        ])
                    ], className = 'd-flex flex-column justify-content-between h-100'),
                ], className = ['h-100'], 
                xs=12, sm=12, md=12, lg=4, xl=4),
                
                # Filter 2: Location (Continent, Subregion, Country in vertical stack)
                dbc.Col([
                    html.Div([
                        # Continent dropdown
                        html.Label(
                            'Continent',
                            id='tt-continent',
                            style={'cursor': 'pointer'}
                        ),
                        dbc.Tooltip(
                            'Select the preferred continent for the filter. Multiple continents can be selected.',
                            target='tt-continent'
                        ),
                        dcc.Dropdown(
                            id='continent-dropdown',
                            options=[{'label': c, 'value': c} for c in continents],
                            placeholder='Select Continent',
                            multi=True
                        ),
                        
                        # Region dropdown
                        html.Label(
                            'Region',
                            id='tt-region',
                            style={'cursor':'pointer'}
                        ),
                        dbc.Tooltip(
                            'Select the preferred region in the selected continents. Multiple regions can be selected.',
                            target='tt-region'
                        ),
                        dcc.Dropdown(
                            id='subregion-dropdown',
                            placeholder='Select Subregion',
                            multi=True
                        ),
                        
                        # Country dropdown
                        html.Label(
                            'Country',
                            id='tt-country',
                            style={'cursor':'pointer'}
                        ),
                        dbc.Tooltip(
                            'Select the preferred countries or type the country names for the filter. Country list is affected by selected continents & regions.',
                            target='tt-country'
                        ),
                        dcc.Dropdown(
                            id='country-dropdown',
                            placeholder='Select Country',
                            multi=True
                        )
                        ]),  
                ], className = ['h-100'], 
                xs=12, sm=12, md=12, lg=3, xl=4),
                # Filter 3: Disaster Type
                dbc.Col([
                    html.Div([
                        html.Label(
                            'Disaster type',
                            id = 'tt-disastertype', 
                            spellCheck = 'false',
                            style={'cursor':'pointer'}
                        ),
                        dbc.Tooltip(
                            'Select the preferred disaster types for the filter. Multiple disaster types can be selected.',
                            target='tt-disastertype'
                        ),
                        dcc.Checklist(
                            className="form-check",
                            id='disaster-type-checkbox',
                            options = [
                                {
                                    "label": [
                                        html.Img(src="/assets/images/disaster_types/drought.jpg", 
                                                 style={'width': '60px', 'height': '35px', 'objectFit': 'cover', 'padding-left': 10}),
                                        html.Span("Drought", style={"padding-left": 10}),
                                    ],
                                    "value": "Drought",
                                },
                                {
                                    "label": [
                                        html.Img(src="/assets/images/disaster_types/earthquake.jpg", 
                                                 style={'width': '60px', 'height': '35px', 'objectFit': 'cover', 'padding-left': 10}),
                                        html.Span("Earthquake", style={"padding-left": 10}),
                                    ],
                                    "value": "Earthquake",
                                },
                                {
                                    "label": [
                                        html.Img(src="/assets/images/disaster_types/extreme_temp.jpg", 
                                                 style={'width': '60px', 'height': '35px', 'objectFit': 'cover', 'padding-left': 10}),
                                        html.Span("Extreme temp", style={"padding-left": 10}),
                                    ],
                                    "value": "Extreme temperature",
                                },
                                {
                                    "label": [
                                        html.Img(src="/assets/images/disaster_types/flood.jpg", 
                                                 style={'width': '60px', 'height': '35px', 'objectFit': 'cover', 'padding-left': 10}),
                                        html.Span("Flood", style={"padding-left": 10}),
                                    ],
                                    "value": "Flood",
                                },
                                {
                                    "label": [
                                        html.Img(src="/assets/images/disaster_types/mass_movement.jpg", 
                                                 style={'width': '60px', 'height': '35px', 'objectFit': 'cover', 'padding-left': 10}),
                                        html.Span("Mass movement", style={"padding-left": 10}),
                                    ],
                                    "value": "Mass movement",
                                },
                                {
                                    "label": [
                                        html.Img(src="/assets/images/disaster_types/storm.jpeg",
                                                 style={'width': '60px', 'height': '35px', 'objectFit': 'cover', 'padding-left': 10}),
                                        html.Span("Storm", style={"padding-left": 10}),
                                    ],
                                    "value": "Storm",
                                },
                                {
                                    "label": [
                                        html.Img(src="/assets/images/disaster_types/volcanic.jpg", 
                                                 style={'width': '60px', 'height': '35px', 'objectFit': 'cover', 'padding-left': 10}),
                                        html.Span("Volcanic activity", style={"padding-left": 10}),
                                    ],
                                    "value": "Volcanic activity",
                                },
                                {
                                    "label": [
                                        html.Img(src="/assets/images/disaster_types/wildfire.jpg",
                                                 style={'width': '60px', 'height': '35px', 'objectFit': 'cover', 'padding-left': 10}),
                                        html.Span("Wildfire", style={"padding-left": 10}),
                                    ],
                                    "value": "Wildfire",
                                }
                            ],
                            value=disaster_types,
                            inline = True,
                            style={
                                'display': 'flex', 'flexDirection': 'row', 
                                'flexWrap': 'wrap', 'display':'grid',
                                'gridTemplateColumns': 'repeat(2, 1fr)', 'gap': '5px',
                                'text-overflow': 'ellipsis', 'overflow': 'hidden', 'white-space': 'nowrap'
                            }
                        )
                    ])
                ], className = ['h-100'], 
                xs=12, sm=12, md=12, lg=5, xl=4)
            ])],style = {'padding': '0 0.5rem'}, className = 'justify-content-center')], 
            className = ['col', 'dflex', 'h-100'], 
            xs=12, sm=12, md=12, lg=10, xl=10  # Match with Col 1 of Row 1
        )
    ], className=['row']),  # Match with Row 2 classes
    
    # Row 2: Statistics cards and graphs                
    dbc.Spinner(
        color="black",
        fullscreen_style={"visibility":"visible", "filter": "blur(2px)"},
        children=[html.Div([
            dbc.Row([
                # Col 1 of Row 2: Statistics
                dbc.Col(
                    [
                        # Card 1: Total deaths
                        dbc.Card([
                            dbc.CardHeader(
                                'Total Casualty',
                                id="tt-card1",
                                style={'textAlign': 'center'}
                            ),
                            dbc.Tooltip(
                                "The number of fatalities (deceased and missing combined) during the period caused by the selected disasters.",
                                target='tt-card1'
                            ),
                            dbc.CardBody(
                                html.Div([
                                    html.H3(id='total-deaths-card', style={'textAlign': 'center', 'alignItems': 'center'}),
                                ], className='card-stats-body')
                            )
                        ], className='stats-card d-flex'),
                        # Card 2: Total Affected
                        dbc.Card([
                            dbc.CardHeader(
                                'Total People Affected',
                                id="tt-card2",
                                style={'textAlign': 'center'}
                            ),
                            dbc.Tooltip(
                                "Including: 1. whom with physical injuries, trauma, or illness requiring immediate medical assistance due to the disasters; 2. whom required shelter due to their house being destroyed or heavily damaged during the disasters; 3. whom required immediate assistance due to the disasters.",
                                target='tt-card2'
                            ),
                            dbc.CardBody(
                                html.Div([
                                    html.H3(id='total-affected-card', style={'textAlign': 'center', 'alignItems': 'center'}),
                                ], className='card-stats-body')
                            )
                        ], className='stats-card d-flex'),
                        # Card 3: Total Damage
                        dbc.Card([
                            dbc.CardHeader(
                                'Total Damage',
                                id="tt-card3",
                                style={'textAlign': 'center'}
                            ),
                            dbc.Tooltip(
                                "The value of all economic losses directly or indirectly due to the disaster. Adjusted for inflation using the Consumer Price Index.",
                                target='tt-card3'
                            ),
                            dbc.CardBody(
                                html.Div([
                                    html.H3(id='total-damage-card', style={'textAlign': 'center', 'alignItems': 'center'}),
                                ], className='card-stats-body')
                            )
                        ], className='stats-card d-flex'),
                        # Card 4: Country with most deaths
                        dbc.Card([
                            dbc.CardHeader(
                                'Highest Casualty',
                                id="tt-card4",
                                style={'textAlign': 'center'}
                            ),
                            dbc.Tooltip(
                                "The country with the highest number of fatalities caused by the disasters.",
                                target='tt-card4'
                            ),
                            dbc.CardBody(
                                html.Div([
                                    html.H3(id='most-deaths-country-card')],
                                    style={'textAlign': 'center', 'alignItems': 'center'},
                                    className='card-stats-body'
                                )
                            )
                        ], className='stats-card d-flex'),
                        # Card 5: Most affected country
                        dbc.Card([
                            dbc.CardHeader(
                                'Most People Affected',
                                id="tt-card5",
                                style={'textAlign': 'center'}
                            ),
                            dbc.Tooltip(
                                "The country with the highest number of people affected by the disasters.",
                                target='tt-card5'
                            ),
                            dbc.CardBody(
                                html.Div(
                                    [html.H3(id='most-affected-country-card')],
                                    style={'textAlign': 'center', 'alignItems': 'center'},
                                    className='card-stats-body'
                                )
                            )
                        ], className='stats-card d-flex'),
                        # Card 6: Most damaged country
                        dbc.Card([
                            dbc.CardHeader(
                                'Highest Damaged',
                                id="tt-card6",
                                style={'textAlign': 'center'}
                            ),
                            dbc.Tooltip(
                                "The country suffered the highest economical losses caused by the disasters.",
                                target='tt-card6'
                            ),
                            dbc.CardBody(
                                html.Div(
                                    [html.H3(id='most-damaged-country-card')],
                                    style={'textAlign': 'center', 'alignItems': 'center'},
                                    className='card-stats-body'
                                )
                            )
                        ], className='stats-card d-flex'),
                    ],
                    className=['d-flex', 'flex-column', 'gap-2'],
                    xs=12, sm=12, md=12, lg=12, xl=2
                ),
                # Col 2 of Row 2: Two maps
                dbc.Col(
                    [
                        dbc.Card([
                            dbc.CardHeader(             
                                id='damage-map-header', 
                            ),
                            dbc.CardBody(
                                html.Div([
                                    dcc.Graph(
                                        id='damage-map',
                                        config={'scrollZoom': False},  
                                        style={'height': '100%'}, 
                                        clear_on_unhover=True
                                    ),
                                    dcc.Tooltip(id='damage-map-tooltip', border_color = '#4C230A')
                                ], className = 'h-100')
                            )
                            ], className = 'map-card flex-fill d-flex flex-column h-50'
                        ),
                        dbc.Card([
                            dbc.CardHeader(id='disaster-count-map-header'),
                            dbc.CardBody(
                                html.Div([
                                    dcc.Graph(
                                        id='disaster-count-map', 
                                        config={'scrollZoom': False}, 
                                        style={'height': '100%'},  
                                        clear_on_unhover=True
                                    ),
                                    dcc.Tooltip(id='disaster-count-map-tooltip', border_color = '#4C230A')
                                ], className = 'h-100')
                            ),
                            ], className = 'map-card flex-fill d-flex flex-column h-50'
                        ),
                    ], 
                    className=['d-flex','flex-column', 'gap-2'],  
                    xs=12, sm=12, md=12, lg=12, xl=5  # Match with other Cols of Row 2
                ),
                # Col 3 of Row 2: Two right charts
                dbc.Col(
                    [
                        dbc.Card([
                            dbc.CardHeader(id='stacked-bar-chart-header'),
                            dbc.CardBody(
                                html.Div([
                                    dcc.Graph(
                                        id='stacked-bar-chart', 
                                        style={'height': '100%'},
                                        clear_on_unhover=True
                                    ),
                                    dcc.Tooltip(id='stacked-bar-chart-tooltip', border_color = '#4C230A')
                                ], className = 'h-100')
                            ),
                            ], className = 'map-card flex-fill d-flex flex-column h-50'
                        ),
                        dbc.Card([
                            dbc.CardHeader(id='casualty-trend-header'),
                            dbc.CardBody(
                                html.Div([
                                    dcc.Graph(
                                        id='casualty-trend', 
                                        style={'height': '100%'}, 
                                        clear_on_unhover=True
                                    ),
                                    dcc.Tooltip(id='casualty-trend-tooltip', border_color = '#4C230A')
                            ], className = 'h-100')
                            )
                            ], className = 'map-card flex-fill d-flex flex-column h-50'
                        )
                    ], 
                    className=['d-flex','flex-column', 'gap-2'],  
                    xs=12, sm=12, md=12, lg=12, xl=5  # Match with other Cols of Row 2
                ),
            ], style = {'margin-top': '1vh'}, className = ['row', 'vh-75'])
        ])]
    ),
    dcc.Store(id='store-data', storage_type='session'),
])

# Store filter data for quick access
@app.callback(
    Output('store-data', 'data'),
    [Input('continent-dropdown', 'value'),
     Input('subregion-dropdown', 'value'),
     Input('country-dropdown', 'value'),
     Input('year-slider', 'value'),
     Input('month-dropdown', 'value'),
     Input('disaster-type-checkbox', 'value')]
)
def store_data(selected_continent=None, selected_subregion=None, selected_country=None, selected_year=[2000,2024], selected_month=None, selected_disaster_type=disaster_types):
    # Start with the original data
    filtered_data = data
    
    # Initialize mask as True for all rows
    mask = pd.Series([True] * len(filtered_data))
    
    # Apply continent filter (allow multiple)
    if selected_continent and isinstance(selected_continent, list):
        mask &= filtered_data['region'].isin(selected_continent)

    # Apply subregion filter (allow multiple)
    if selected_subregion and isinstance(selected_subregion, list):
        mask &= filtered_data['subregion'].isin(selected_subregion)

    # Apply country filter (allow multiple)
    if selected_country and isinstance(selected_country, list):
        mask &= filtered_data['country'].isin(selected_country)

    # Apply year filter
    if selected_year:
        mask &= (filtered_data['year'] >= str(selected_year[0])) & (filtered_data['year'] <= str(selected_year[1]))

    # Apply month filter (allow multiple)
    if selected_month and isinstance(selected_month, list):
        filtered_data['month'] = filtered_data['month'].astype(int)
        mask &= filtered_data['month'].isin(selected_month)


    # Apply disaster type filter (allow multiple)
    if selected_disaster_type and isinstance(selected_disaster_type, list):
        mask &= filtered_data['type'].isin(selected_disaster_type)

    # Filter the DataFrame using the combined mask
    filtered_data = filtered_data[mask]

    return filtered_data.to_dict(orient='records')


# Filter B1: Update the subregion dropdown based on selected continent
@app.callback(
    Output('subregion-dropdown', 'options'),
    Input('continent-dropdown', 'value')
)
def update_subregions(selected_continent):
    if selected_continent:
        # Ensure selected_continent is a list
        filtered_subregions = data[data['region'].isin(selected_continent)]['subregion'].unique()
        return [{'label': s, 'value': s} for s in filtered_subregions]
    return []


# Filter B2: Update the country dropdown based on selected continent and subregion
@app.callback(
    Output('country-dropdown', 'options'),
    Input('continent-dropdown', 'value'),  # Add continent input
    Input('subregion-dropdown', 'value')
)
def update_countries(selected_continent, selected_subregion):
    # Start with the full DataFrame
    filtered_data = data.copy()

    # If a continent is selected, filter based on continent
    if selected_continent:
        filtered_data = filtered_data[filtered_data['region'].isin(selected_continent)]

    # If a subregion is selected, filter based on subregion
    if selected_subregion:
        filtered_data = filtered_data[filtered_data['subregion'].isin(selected_subregion)]

    # Get the unique countries from the filtered DataFrame
    filtered_countries = filtered_data['country'].unique()

    # Sort the list of countries alphabetically
    filtered_countries_sorted = sorted(filtered_countries)

    return [{'label': c, 'value': c} for c in filtered_countries_sorted]


# Generate card header
@app.callback(
    [Output('damage-map-header', 'children'),
    Output('disaster-count-map-header', 'children'),
    Output('stacked-bar-chart-header', 'children'),
    Output('casualty-trend-header', 'children')],
    [Input('continent-dropdown', 'value'),
     Input('subregion-dropdown', 'value'),
     Input('country-dropdown', 'value'),
     Input('year-slider', 'value'),
     Input('month-dropdown', 'value'),
     Input('disaster-type-checkbox', 'value')]
)

def generate_card_name(selected_continent, selected_subregion, selected_country, selected_year, selected_month, selected_disaster_type):
    # Update the plot card header name for each card (Total of 4 cards)
    MapA_base_header = "Total damage (in US$) inflicted by "
    damage_header = generate_header(MapA_base_header, selected_disaster_type, selected_year, selected_month)
    
    MapB_base_header = "Total number of "
    disaster_count_damage_header = generate_header(MapB_base_header, selected_disaster_type, selected_year, selected_month)
    
    Bar_base_header = "Trends of "
    stacked_bar_chart_header = generate_header(Bar_base_header, selected_disaster_type, selected_year, selected_month)

    Line_base_header = "Number of deaths by time from "
    casualty_trend_header = generate_header(Line_base_header, selected_disaster_type, selected_year, selected_month)
    
    return damage_header, disaster_count_damage_header, stacked_bar_chart_header, casualty_trend_header
    
# Button 1: Reset filters
@app.callback(
    [Output('continent-dropdown', 'value'),
    Output('subregion-dropdown', 'value'),
    Output('country-dropdown', 'value'),
    Output('year-slider', 'value'),
    Output('month-dropdown', 'value'),
    Output('disaster-type-checkbox', 'value')],
    [Input("clear-filter", "n_clicks")]
)
def reset_filters(n_clicks):
    return (
        None,  # Reset continent dropdown to None or default value
        None,  # Reset subregion dropdown to None or default value
        None,  # Reset country dropdown to None or default value
        [2000, 2024],  # Reset year slider to the default range
        None,          # Reset month dropdown to None or default value
        disaster_types # Reset disaster type checklist to the original list
    )

# Button 2: Dashboard guide
@app.callback(
    Output("modal", "is_open"),
    [Input("open-modal", "n_clicks"), Input("close-modal", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


# Stats: Update all the statistics cards
@app.callback(
    [Output('total-deaths-card', 'children'),
     Output('total-affected-card', 'children'),
     Output('total-damage-card', 'children'),
     Output('most-deaths-country-card', 'children'),
     Output('most-affected-country-card', 'children'),
     Output('most-damaged-country-card', 'children'),
     Output('last-updated-card', 'children')],
    Input('store-data', 'data')
)
def update_stat_cards(data):
    # Convert the data back to DataFrame format
    filtered_data = pd.DataFrame(data)

    # Convert 'last_update' column to datetime, errors='coerce' will convert invalid parsing to NaT
    filtered_data['last_update'] = pd.to_datetime(filtered_data['last_update'], errors='coerce')

    # Calculate totals for the filtered data
    total_deaths = filtered_data['total_deaths'].sum()
    total_affected = filtered_data['total_affected'].sum()
    total_damage = filtered_data['total_damage'].sum()

    # Convert sums to integers if they are not None
    total_deaths = int(total_deaths) if pd.notna(total_deaths) else 0
    total_affected = int(total_affected) if pd.notna(total_affected) else 0
    total_damage = int(total_damage) if pd.notna(total_damage) else 0

    # Get country with most affected
    most_affected_country = filtered_data.groupby('country')['total_affected'].sum().idxmax() if not filtered_data.empty else 'N/A'
    # Get country with most damage
    most_damaged_country = filtered_data.groupby('country')['total_damage'].sum().idxmax() if not filtered_data.empty else 'N/A'
    # Get country with most deaths
    most_deaths_country = filtered_data.groupby('country')['total_deaths'].sum().idxmax() if not filtered_data.empty else 'N/A'

    # Get last updated date, handle NaT (Not a Time) values gracefully
    last_updated = filtered_data['last_update'].max() if not filtered_data.empty else 'N/A'

    # Format the values with commas for better readability
    total_deaths_str = f"{total_deaths:,}"
    total_affected_str = f"{total_affected:,}"
    total_damage_str = f"{total_damage:,} US$"
    last_updated_str = f"Data last update: {last_updated.strftime('%Y-%m-%d')}" if last_updated != 'N/A' else "Last update: N/A"

    return (total_deaths_str, total_affected_str, total_damage_str,
            most_deaths_country, most_affected_country, most_damaged_country, last_updated_str)


## MapA: Total damage choropleth map based on filters
# MapA plotting
@app.callback(
    Output('damage-map', 'figure'),
    Input('store-data', 'data')
)

def mapA_damage_choropleth(data):
    # Convert the data back to DataFrame format
    filtered_data = pd.DataFrame(data)

    # Calculate total damage by country
    agg_damage = filtered_data.groupby('country')['total_damage'].sum().reset_index()
    agg_damage.rename(columns={'total_damage': 'damage_by_country'}, inplace=True)
    
    # Merge to get the damage values into filtered_data
    filtered_data = filtered_data.merge(agg_damage, on='country', how='left')

    # Get the minimum and maximum damage values
    median = filtered_data['damage_by_country'].median()
    
    # Define dynamic bins based on the value ranges
    if median < 1_000_000:
        bins = [0, 1000, 10_000, 100_000, 1_000_000, float('inf')]
        labels = ['0 - 1K', '1K - 10K', '10K - 100K', '100K - 1M', '> 1M']
    elif median < 1_000_000_000:
        bins = [0, 1_000_000, 10_000_000, 100_000_000, 1_000_000_000, float('inf')]
        labels = ['0 - 1M', '1M - 10M', '10M - 100M', '100M - 1B', '> 1B']
    else:
        bins = [0, 1_000_000_000, 10_000_000_000, 100_000_000_000, float('inf')]
        labels = ['0 - 1B', '1B - 10B', '10B - 100B', '> 100B']

    # Create a new column 'damage_category' using pd.cut
    filtered_data['damage_category'] = pd.cut(
        filtered_data['damage_by_country'], 
        bins=bins, labels=labels, 
        include_lowest=True)

    # Ensure 'damage_category' is a categorical type with the specified order
    filtered_data['damage_category'] = pd.Categorical(
        filtered_data['damage_category'],
        categories=labels,
        ordered=True
    )

    # Identify missing categories
    existing_categories = filtered_data['damage_category'].dropna().unique()
    missing_categories = set(labels) - set(existing_categories)

    if missing_categories:
        missing_df = pd.DataFrame({
            'country': [None]*len(missing_categories),
            'damage_by_country': [0]*len(missing_categories),
            'damage_category': pd.Categorical(list(missing_categories), categories=labels, ordered=True)
        })
        filtered_data = pd.concat([filtered_data, missing_df], ignore_index=True)

    # Sort the DataFrame by 'damage_category' to ensure correct plotting order
    filtered_data.sort_values('damage_category', inplace=True)
    
    # Assign color for each category
    category_color = {labels[i]: map_color[i] for i in range(len(labels))}

    # Create choropleth map for total damage categorized
    fig = px.choropleth(
        filtered_data,
        locations='country',
        locationmode='country names',
        color='damage_category',  # Use the 'damage_category' column for color
        color_discrete_map=category_color,  # Use explicit color mapping
        hover_name='country',  # Country name shown on hover
        custom_data=['damage_by_country','damage_category'],  # Add damage category to custom data
        category_orders={'damage_category': labels}  # Force the correct legend order
    )
    
    # Turn off native hover to use dash tooltip
    fig.update_traces(hoverinfo="none", hovertemplate=None)

    # Customize the map's appearance
    fig.update_geos(
        showcoastlines=True,
        fitbounds='locations',
        coastlinecolor="Black",
        showland=True, landcolor="lightgray", visible=False
    )

    fig.update_layout(
        margin={"r":0, "t":0, "l":0, "b":0},
        legend=dict(
            orientation='h',
            yanchor="bottom",
            y=-0.1,
            xanchor="center",
            x=0.5,
            title=None
        )
    )

    return fig

# MapA tooltip
@app.callback(
    Output("damage-map-tooltip", "show"),
    Output("damage-map-tooltip", "bbox"),
    Output("damage-map-tooltip", "children"),
    [Input("damage-map", "hoverData"),
     Input('year-slider', 'value'),
     Input('disaster-type-checkbox', 'value')]
)
def mapA_hover(hover_data, selected_year, selected_disaster_type):
    if hover_data is None:
        # Return default values when there's no hover data
        return False, {"x0": 0, "y0": 0, "x1": 0, "y1": 0}, "No data available"

    # Get hover details
    pt = hover_data["points"][0]
    bbox = pt["bbox"]  # This should already have the correct structure
    
    # Extract country name from the hover data
    country_name = pt["location"]
    
    # Extract the year based on year slider or input
    if isinstance(selected_year, list):
        year_display = f"{selected_year[0]} - {selected_year[1]}"
    else:
        year_display = f"{selected_year}"

    # Extract the damage category directly from hover data
    damage = pt.get('customdata', [None])[0]  # Adjust based on your hover data structure
    fmt_damage = format_value(damage)
    
    # Create tooltip content
    children = html.Div([
        html.H5(f"{country_name}", style={'margin': '0', 'textAlign': 'left'}),
        html.H6(year_display, style={'margin': '0', 'textAlign': 'left'}, className = 'text-muted b'),
        html.P(f"Total damage suffered: {fmt_damage} US$", style={'margin': '0', 'textAlign': 'left'}, className = 'b'),
    ])

    return True, bbox, children

# Map-B: The disaster count choropleth map based on filters
@app.callback(
    Output('disaster-count-map', 'figure'),
    Input('store-data', 'data')
)


def mapB_disaster_count_choropleth(data):
    # Convert the data back to DataFrame format
    filtered_data = pd.DataFrame(data)

    # Aggregate the number of disasters per country
    agg_count = filtered_data.groupby('country')['id'].count().reset_index()
    agg_count.rename(columns={'id': 'total_disasters'}, inplace=True)

    # Merge to get the damage values into filtered_data
    filtered_data = filtered_data.merge(agg_count, on='country', how='left')

    # Initialize disaster_count_filtered from filtered_data
    disaster_count_filtered = filtered_data.copy()
    
    # Get the minimum and maximum damage values
    median = filtered_data['total_disasters'].median()

    # Define bins and labels based on the current range of values (0 to over 600)
    if median <= 20:
        bins = [0, 10, 20, 30, 40, float('inf')]
        labels = ['0 - 10', '10 - 20', '20 - 30', '30 - 40', '> 40']

    elif median <= 50:
        bins = [0, 15, 25, 50, 100, float('inf')]
        labels = ['0 - 15', '15 - 25', '25 - 50', '50 - 100', '> 100']
        
    else:
        bins = [0, 50, 100, 200, 300, float('inf')]
        labels = ['0 - 50', '50 - 100', '100 - 200', '200 - 300', '> 300']

    # Create a new column 'disaster_category' using pd.cut
    disaster_count_filtered['disaster_category'] = pd.cut(
        filtered_data['total_disasters'], 
        bins=bins, labels=labels, 
        include_lowest=True
    )

    # Ensure 'disaster_category' is a categorical type with the specified order
    disaster_count_filtered['disaster_category'] = pd.Categorical(
        disaster_count_filtered['disaster_category'],
        categories=labels,
        ordered=True
    )

    # Identify missing categories
    existing_categories = disaster_count_filtered['disaster_category'].dropna().unique()
    missing_categories = set(labels) - set(existing_categories)

    if missing_categories:
        missing_df = pd.DataFrame({
            'country': [None]*len(missing_categories),
            'total_disasters': [1]*len(missing_categories), 
            'disaster_category': pd.Categorical(list(missing_categories), categories=labels, ordered=True)
        })
        disaster_count_filtered = pd.concat([disaster_count_filtered, missing_df], ignore_index=True)
    
    # Sort the DataFrame by the disaster category to ensure plotting order
    disaster_count_filtered.sort_values('disaster_category', inplace=True)

    # **Explicit color mapping to ensure the correct order of categories**
    category_color = {labels[i]: map_color[i] for i in range(len(labels))}


    # Create scatter_geo map for total number of disasters categorized
    fig = px.choropleth(
        disaster_count_filtered,
        locations='country',
        locationmode='country names',
        color='disaster_category',
        color_discrete_map=category_color,
        hover_name='country',  # Country name shown on hover
        custom_data=['total_disasters', 'disaster_category'],
        category_orders={'disaster_category': labels}
    )
    
    # Turn off native hover to use dash tooltip
    fig.update_traces(hoverinfo="none", hovertemplate=None)
    
    # Customize the map's appearance
    fig.update_geos(
        showcoastlines=True,
        fitbounds='locations',
        coastlinecolor="Black",
        showland=True, landcolor="lightgray", visible=False
    )
    
    # Adjust the layout and margins, ensuring all categories are visible and correctly ordered
    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        legend=dict(
            orientation='h',
            yanchor="bottom",
            y=-0.1,
            xanchor="center",
            x=0.5,
            traceorder="normal",
            itemsizing="constant",
            title=None
        )
    )

    return fig

# MapB tooltip
@app.callback(
    Output("disaster-count-map-tooltip", "show"),
    Output("disaster-count-map-tooltip", "bbox"),
    Output("disaster-count-map-tooltip", "children"),
    [Input("disaster-count-map", "hoverData"),
     Input('year-slider', 'value'),
     Input('disaster-type-checkbox', 'value')]
)
def mapB_hover(hover_data, selected_year, selected_disaster_type):
    if hover_data is None:
        # Return default values when there's no hover data
        return False, {"x0": 0, "y0": 0, "x1": 0, "y1": 0}, "No data available"

    # Get hover details
    pt = hover_data["points"][0]
    bbox = pt["bbox"]  # This should already have the correct structure
    
    # Extract country name from the hover data
    country_name = pt["location"]
    
    # Extract the year based on year slider or input
    if isinstance(selected_year, list):
        year_display = f"{selected_year[0]} - {selected_year[1]}"
    else:
        year_display = f"{selected_year}"

    # Extract the damage category directly from hover data
    count = pt.get('customdata', [None])[0]
    #disaster_cate = pt.get('customdata', [None, 'None'])[1]
    
    # Create tooltip content
    children = html.Div([
        html.H5(f"{country_name}", style={'margin': '0', 'textAlign': 'left'}),
        html.H6(year_display, style={'margin': '0', 'textAlign': 'left'}, className = 'text-muted b'),
        html.P(f"Number of disasters: {count}", style={'margin': '0', 'textAlign': 'left'}, className = 'b'),
    ])

    return True, bbox, children



# Bar chart: The stacked bar chart based on filters
@app.callback(
    Output('stacked-bar-chart', 'figure'),
    Input('store-data', 'data')
)
def plot_bar_total_disaster(data):
    # Convert the data back to DataFrame format
    filtered_data = pd.DataFrame(data)

    # Group by year and type for the filtered data
    disasters_type_and_year = filtered_data.groupby(['year', 'type']).size().reset_index(name='total_disasters')

    # Convert 'year' to int
    disasters_type_and_year['year'] = disasters_type_and_year['year'].astype(int)
    
    # Map the colors based on the disaster type
    disaster_colors = {disaster_types[i]: color_list[i] for i in range(len(disaster_types))}


    # Create stacked bar chart for total disasters by type and year
    fig = px.bar(
        disasters_type_and_year,
        x='year',
        y='total_disasters',
        color='type',
        color_discrete_map = disaster_colors,
        custom_data = ['type'],
        labels={'total_disasters': 'Total Disasters'}
    )
    
    fig.update_traces(hoverinfo="none", hovertemplate=None)
    
    fig.update_layout(
        xaxis = dict(
            title = 'Year',
            tickvals = [i for i in range(2000, 2025, 4)],
        ),
        yaxis_title='Total Disasters',
        plot_bgcolor='white',
        margin=dict(l=40, r=40, t=10, b=10),
        legend=dict(
            orientation='h',
            #yanchor="middle",
            y=-0.25,
            #xanchor="center",
            #x=0.5,
            title=None
        )
    )
    return fig

# Stacked bar chart tooltip
@app.callback(
    Output("stacked-bar-chart-tooltip", "show"),
    Output("stacked-bar-chart-tooltip", "bbox"),
    Output("stacked-bar-chart-tooltip", "children"),
    [Input("stacked-bar-chart", "hoverData"),
     Input('year-slider', 'value'),
     Input('disaster-type-checkbox', 'value')]
)
def bar_hover(hover_data, selected_year, selected_disaster_type):
    if hover_data is None:
        # Return default values when there's no hover data
        return False, {"x0": 0, "y0": 0, "x1": 0, "y1": 0}, "No data available"

    # Get hover details
    pt = hover_data["points"][0]
    bbox = pt["bbox"]
    
    # Extract country name from the hover data
    disaster_type = pt.get('customdata', [None])[0]
    disaster_count = pt['y']
    
    # Extract the year based on year slider or input
    if isinstance(selected_year, list):
        year_display = f"{selected_year[0]} - {selected_year[1]}"
    else:
        year_display = f"{selected_year}"
    
    disaster_colors = {
        'Drought': '#4C230A', 'Extreme temperature': '#E34B48', 'Volcanic activity': '#0D160B', 'Wildfire': 'orange', 
        'Earthquake': '#555B6E', 'Mass movement': '#84B59F', 'Flood': '#568EA3', 'Storm' : '#BBE5ED'
    }
    
    type_color = disaster_colors.get(disaster_type, 'black')  # Default to 'black' if type is not found
       
    # Create tooltip content
    children = html.Div([
        html.H5(f"{disaster_type}", style={'margin': '0', 'textAlign': 'left', 'color': type_color}),
        html.H6(year_display, style={'margin': '0', 'textAlign': 'left'}, className = 'text-muted b'),
        html.P(f"{disaster_count} occurences", style={'margin': '0', 'textAlign': 'left'}, className = 'b'),
    ])

    return True, bbox, children

# Line chart: Total death by year
@app.callback(
    Output('casualty-trend', 'figure'),
    Input('store-data', 'data')
)
def plot_line_casualty_trend(data):
    # Convert the data back to DataFrame format
    filtered_data = pd.DataFrame(data)

    # Group by year and country to calculate total deaths
    deaths_by_country_year = filtered_data.groupby(['year'])['total_deaths'].sum().reset_index()
    # Get the mean of global total deaths
    mean_death = deaths_by_country_year['total_deaths'].mean()
    # Convert 'year' to int
    deaths_by_country_year['year'] = deaths_by_country_year['year'].astype(int)

    # Create the line chart for Casualty Trend
    fig = px.area(
        deaths_by_country_year,
        x='year',
        y='total_deaths',
        markers = True,
        color_discrete_sequence=['#FEA50B']
    )
    
    fig.update_traces(
        hovertemplate="<b>%{y}</b> deaths ")

    # Customize the layout of the line chart
    fig.update_layout(
        xaxis=dict(
            title='Year',
            tickvals=[i for i in range(2000, 2025, 4)]
        ),
        yaxis=dict(
            title='Total Deaths',
            showgrid=True, gridwidth=1, gridcolor='lightgrey'
        ),
        plot_bgcolor='white',
        margin=dict(l=40, r=40, t=10, b=40),
        showlegend=False,
    )
    
    # Turn off native hover to use dash tooltip
    fig.update_traces(hoverinfo="none", hovertemplate=None)

    fig.add_hline(
        y = mean_death, line_dash="dash",
        annotation_text=f"Period mean:{format_value(mean_death)}", 
        annotation_position="bottom right")

    return fig

# Line chart tooltip
@app.callback(
    Output("casualty-trend-tooltip", "show"),
    Output("casualty-trend-tooltip", "bbox"),
    Output("casualty-trend-tooltip", "children"),
    [Input("casualty-trend", "hoverData"),
     Input('disaster-type-checkbox', 'value')]
)
def line_hover(hover_data, selected_disaster_type):
    if hover_data is None:
        # Return default values when there's no hover data
        return False, {"x0": 0, "y0": 0, "x1": 0, "y1": 0}, "No data available"

    # Get hover details
    pt = hover_data["points"][0]
    bbox = pt["bbox"]  # This should already have the correct structure
    
    # Extract country name from the hover data
    total_deaths = pt['y']
    year = pt['x']
    
       
    # Create tooltip content
    children = html.Div([
        html.H5(year, style={'margin': '0', 'textAlign': 'left'}),
        html.P(f"Total deaths: {format_value(total_deaths)}", style={'margin': '0', 'textAlign': 'left'}, className = 'b'),
    ])

    return True, bbox, children

# Run the app
# Unhash below to make it automatically open the dashboard in browser when running py app.
# def open_browser():
    # webbrowser.open_new("http://127.0.0.1:8050/")

# Only open the browser if the script is run directly
if __name__ == "__main__":
    # Start the Dash app and open the browser automatically after a slight delay
    # Timer(1, open_browser).start()
    app.run_server(debug=True)
