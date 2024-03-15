from dash import Dash, html, dash_table, dcc, callback, Output, Input, State, MATCH, ALL
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
from flight_database import get_flight_data

route_delays = pd.read_csv('route_delays.csv')
airport_coords_df = pd.read_csv('airport_coords_df.csv')
dep_delay = pd.read_csv('dep_delay.csv')
dep_count = pd.read_csv('dep_count.csv')
airport_coordinates = airport_coords_df.set_index('ORIGIN')[['lat', 'lon']].to_dict(orient='index')

route_delays['route_key'] = route_delays['ORIGIN'] + '_' + route_delays['DEST']
route_delays = route_delays.drop_duplicates(subset='route_key')
# route group dictionary
route_dict = route_delays.set_index('route_key')['Group'].to_dict()
count_dict = dep_delay.set_index('ORIGIN')['flight_count'].to_dict()
dep_del_dict = dep_delay.set_index('ORIGIN')['DEP_DEL15'].to_dict()

# Initialize the app
#app = Dash(__name__)
app = Dash(__name__, suppress_callback_exceptions=True)

# App layout
# <div> defines a division or section 
app.layout = html.Div([
    # Markdown text block at the top
    dcc.Markdown("""
        ## Flight Routes Information

        This app allows you to visualize flight routes between airports and the average proportion of delays. Enter the airport codes for 
        departures and arrivals, and press "Plot Routes" to see the routes on the map.

        Each number in the legend is a group number that represents the proportion of delayed flights on average for each route.

        Here is what each number in the legend means:
        - 0: delay proportion <= 0.1
        - 1: 0.1 < delay proportion <= 0.15
        - 2: 0.15 < delay proportion <= 0.2
        - 3: 0.2 < delay proportion <= 0.25
        - 4: 0.25 < delay proportion <= 0.3
        - 5: delay proportion > 0.3
        
        ## Heatmap Information

        The heatmap illustrates U.S. airport departures, highlighting flight volume and delay frequency. 
        Larger circles denote more flights; color intensity reflects higher delay percentages.

        ## Rush Hour Information

        This app offers insights into the frequency and peak hours of flight departures from specific airports. 
        By inputting an airport code and a flight's departure time, users can generate a bar chart that reveals the airport's busiest periods, aiding in understanding rush hour trends. 
    """, style={'margin': '20px', 'padding': '20px', 'border': '1px solid #ddd', 'borderRadius': '5px'}),
    dcc.RadioItems(
        id='vis-mode-selector',
        options=[
            {'label': 'Flight Routes', 'value': 'routes'},
            {'label': 'Heatmap', 'value': 'heatmap'},
            {'label': 'Rush Hour', 'value': 'hour'}
        ],
        value='routes',  # Default value
        labelStyle={'display': 'block'}
    ),
    # NEW EDIT
    html.Div(id='page-content')
])

@app.callback(
    Output('page-content', 'children'),
    [Input('vis-mode-selector', 'value')]
)

def display_page(vis_mode):
    # Return layout corresponding to the selected mode 
    if vis_mode == 'routes':
        return html.Div([
            html.Div([
        # Container for the first column (inputs and the button)
            html.Div([
                # Sub-container for just the inputs
                html.Div([
                    html.Div([
                        dcc.Input(id={'type': 'departure-input', 'index': i}, type='text', placeholder=f'Departure {i}'),
                        dcc.Input(id={'type': 'arrival-input', 'index': i}, type='text', placeholder=f'Arrival {i}')
                    ], style={'padding': '10px'})
                    for i in range(1, 11)
                ]),
                # Button to plot routes
                html.Button('Plot Routes', id='plot-button', n_clicks=0, style={'width':'50%', 'margin': '10px auto'}),
            ], style={'display': 'flex', 'flexDirection': 'column', 'marginRight': '20px'}),  # marginRight added to separate the columns
        
            # Container for the second column (the map)
            html.Div([
                dcc.Graph(id='map', figure=go.Figure(layout={'title': 'Please select departure and arrival locations and click "Plot Routes"'}))
            ], style={'flex': 2}),
        ], style={'display': 'flex', 'width': '100%'}),
        ], style={'alignItems': 'flex-start', 'justifyContent': 'center', 'height': '100vh'}, id='content-route')

    elif vis_mode == 'heatmap':
        return html.Div([
            dcc.Graph(id='heat-map', figure=create_composite_map())
        ], id = 'content_heatmap', style={'display': 'flex', 'flexDirection': 'column', 'marginRight': '20px'})
    elif vis_mode == 'hour':
        return html.Div([
            html.Div([
                    dcc.Input(id='origin-input', type='text', placeholder= 'Departure'),
                    dcc.Input(id='hour-input', type='text', placeholder= 'Hour')
                ], style={'padding': '10px'}),
            html.Button('Update', id='update-button', n_clicks=0),
            dcc.Graph(id='hist', figure = go.Figure(layout={'title': 'Please enter departure location and hour and click "Update"'}))
        ], id='content-hour')
    else:
        return html.Div("Select a visualization mode.", id='default-view')


@app.callback(
    Output('hist', 'figure'),
    [Input('vis-mode-selector', 'value'),
     Input('update-button', 'n_clicks')],
    [State('origin-input', 'value'), State('hour-input', 'value')]
)
def update_hourly_activity(n_clicks, vis_mode, selected_origin, selected_hour):
    # This function should generate the histogram figure based on the selected origin and hour
    # You would write the logic here to filter your DataFrame based on the selected origin and hour,
    # then create a histogram of flight counts for each hour of the day.

    if selected_origin is not None:
        selected_origin = selected_origin.upper()
    
    # Otherwise, generate the histogram for the selected origin and hour
    filtered_df = dep_count[dep_count['ORIGIN'] == selected_origin]
    
    # Create a barplot of flights by hour
    # First, we create the text that will be displayed on each bar
    filtered_df['text'] = 'Airport: ' + filtered_df['ORIGIN'] \
                      + '<br>Hour: ' + filtered_df['dep_hour'].astype(str) \
                      + '<br>Flights: ' + filtered_df['dep_count'].astype(str)

    # Now we can create the bar plot
    fig = px.bar(filtered_df, x='dep_hour', y='dep_count', title='Hourly Flight Activity') 

    fig.update_layout(xaxis_title='Departure Hour', yaxis_title='Numer of Flights')
    # To add hover text, you can use the hover_data parameter
    fig.update_traces(hovertemplate=filtered_df['text'])

    # Highlight the selected hour if one is selected
    
    try:
        selected_hour = int(selected_hour)
        if 0 <= selected_hour <= 23:
            fig.add_vline(x=selected_hour, line_color="red", annotation_text="Selected Hour")
    except (ValueError, TypeError):
        pass

    return fig


# Callback to update the map based on the inputs
@app.callback(
    #Output('content-route', 'children'),
    Output('map', 'figure'),
    [Input('vis-mode-selector', 'value'),
     Input('plot-button', 'n_clicks')
    ],
    [State({'type': 'departure-input', 'index': ALL}, 'value'),
     State({'type': 'arrival-input', 'index': ALL}, 'value'),
    ]
)


def update_map(n_clicks, vis_mode, departures, arrivals):
    routes = []

    departures = [dep.upper() for dep in departures if dep is not None]
    arrivals = [arr.upper() for arr in arrivals if arr is not None]

    # loop through each pair of depature and arrival inputs
    for dep, arr in zip(departures, arrivals):
        if dep and arr:  # Ensure both inputs are provided
            # Generate the composite key for the current route
            route_key = f"{dep}_{arr}"
            # Look up the group for the current route
            group = route_dict.get(route_key)  
            count = count_dict.get(route_key)
            delay_proportion = dep_del_dict.get(route_key)
            dep_coords = airport_coordinates.get(dep)
            arr_coords = airport_coordinates.get(arr)

            # Proceed only if coordinates for both airports are found
            if dep_coords and arr_coords:
                # Construct the route data structure
                route = {
                    "departure_airport": dep,
                    "arrival_airport": arr,
                    "departure_lat": dep_coords['lat'],
                    "departure_lon": dep_coords['lon'],
                    "arrival_lat": arr_coords['lat'],
                    "arrival_lon": arr_coords['lon'],
                    "delay_proportion": delay_proportion,
                    "group": group,
                    "flight_count": count
                }
                routes.append(route)
    
    fig = create_figure_with_routes(routes)  

    return fig

def create_figure_with_routes(routes):
    fig = go.Figure()
    # Define a color scheme for the different groups
    group_colors = {
        0: "#1f77b4",  # Muted blue
        1: "#ff7f0e",  # Safety orange
        2: "#2ca02c",  # Cooked asparagus green
        3: "#d62728",  # Brick red
        4: "#9467bd",  # Muted purple
        5: "#8c564b",  # Chestnut brown
    }
    # Loop through each route and add it to the figure with the respective color
    for route in routes:
        # Get the color for the current group or default to black if not found
        route_color = group_colors.get(route["group"])

        fig.add_trace(
            go.Scattergeo(
                lon = [route["departure_lon"], route["arrival_lon"]],
                lat = [route["departure_lat"], route["arrival_lat"]],
                text = [f"{route['departure_airport']}", f"{route['arrival_airport']}"],
                hoverinfo='text',
                mode = "lines+markers",
                line = dict(width = 2, color = route_color),
                marker = dict(size = 4, color = route_color),
                name = route["group"],
            )
        )
        # Update layout of the map
    fig.update_layout(
        title_text = "Flight Routes and Delay Proportions",
        showlegend = True,
        geo = dict(
            projection_type = "albers usa",
            showland = True,
            landcolor = "rgb(200, 200, 200)",
            countrycolor = "rgb(204, 204, 204)",
            showsubunits=True,  # Show state lines and other subunits
            subunitwidth=1  # Width of the subunit lines (state lines)
        ),
    )
    return fig

# Assuming 'routes' is a DataFrame with columns for departure and arrival coordinates,
# number of flights, and delay proportions


@app.callback(
    Output('content-heatmap', 'children'),
    Input('vis-mode-selector', 'value')
)

def create_composite_map():

    fig = go.Figure(data=go.Scattergeo(
        lon = dep_delay['ORIGIN_LONGITUDE'],
        lat = dep_delay['ORIGIN_LATITUDE'],
        text = dep_delay['ORIGIN'],
        customdata = dep_delay[['flight_count', 'DEP_DEL15']],  # Add flight count and delay proportions to the custom data
        hovertemplate = (
            "<b>%{text}</b><br>"
            "Flight Count: %{customdata[0]}<br>"
            "Delay Proportion: %{customdata[1]:.2f}<extra></extra>"  # Format delay proportion to show two decimal places
        ),
        marker = dict(
            size = dep_delay['DEP_DEL15'] * 50,  # Scale the points based on delay proportion
            color = dep_delay['DEP_DEL15'],
            colorscale = 'Viridis',
            showscale = True,
            colorbar_title = 'Delay Proportion'
        )
    ))

    fig.update_layout(
        title = 'Heatmap of Flight Delay Proportions',
        geo = dict(
            scope = 'usa',
            projection_type = 'albers usa',
            showland = True,
            landcolor = 'rgb(217, 217, 217)',
            subunitcolor = "rgb(255, 255, 255)"
        )
    )
    
    

    return fig



# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)