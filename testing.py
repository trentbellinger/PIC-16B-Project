from dash import Dash, html, dash_table, dcc, callback, Output, Input, State, MATCH, ALL
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
from flight_database import get_flight_data

route_delays = pd.read_csv('route_delays.csv')
airport_coords_df = pd.read_csv('airport_coords_df.csv')
airport_coordinates = airport_coords_df.set_index('ORIGIN')[['lat', 'lon']].to_dict(orient='index')

route_delays['route_key'] = route_delays['ORIGIN'] + '_' + route_delays['DEST']
route_delays = route_delays.drop_duplicates(subset='route_key')
# route group dictionary
route_dict = route_delays.set_index('route_key')['Group'].to_dict()

# Initialize the app
app = Dash(__name__)

# App layout
# <div> defines a division or section 
app.layout = html.Div([
    # Markdown text block at the top
    dcc.Markdown("""
        ## Flight Route Information

        This app allows you to visualize flight routes between airports and the average proportion of delays. Enter the airport codes for 
        departures and arrivals, and press "Plot Routes" to see the routes on the map.

        - Use the input fields to enter airport codes.
        - Click "Plot Routes" to display the routes.

        Each number in the legend is a group number that represents the proportion of delayed flights on average for each route.
        
        Here is what each number in the legend means:
        - 0: delay proportion <= 0.1
        - 1: 0.1 < delay proportion <= 0.15
        - 2: 0.15 < delay proportion <= 0.2
        - 3: 0.2 < delay proportion <= 0.25
        - 4: 0.25 < delay proportion <= 0.3
        - 5: delay proportion > 0.3
    """, style={'margin': '20px', 'padding': '20px', 'border': '1px solid #ddd', 'borderRadius': '5px'}),

    # Main container for the layout below the markdown text block
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
            html.Button('Plot Routes', id='plot-button', n_clicks=0, style={'margin-top': '20px'}),
        ], style={'display': 'flex', 'flexDirection': 'column', 'marginRight': '20px'}),  # marginRight added to separate the columns
        
        # Container for the second column (the map)
        html.Div([
            dcc.Graph(id='map')
        ], style={'flex': 2}),
    ], style={'display': 'flex', 'width': '100%'}),
], style={'alignItems': 'flex-start', 'justifyContent': 'center', 'height': '100vh'})



# Callback to update the map based on the inputs
@app.callback(
    Output('map', 'figure'),
    [Input('plot-button', 'n_clicks')],
    [State({'type': 'departure-input', 'index': ALL}, 'value'),
     State({'type': 'arrival-input', 'index': ALL}, 'value')]
)


def update_map(n_clicks, departures, arrivals):
    routes = []

    # loop through each pair of depature and arrival inputs
    for dep, arr in zip(departures, arrivals):
        if dep and arr:  # Ensure both inputs are provided
            # Generate the composite key for the current route
            route_key = f"{dep}_{arr}"
            # Look up the group for the current route
            group = route_dict.get(route_key)  
            dep_coords = airport_coordinates.get(dep)
            arr_coords = airport_coordinates.get(arr)

            # Proceed only if coordinates for both airports are found
            if dep_coords and arr_coords:
                # Construct the route data structure
                route = {
                    "departure_lat": dep_coords['lat'],
                    "departure_lon": dep_coords['lon'],
                    "arrival_lat": arr_coords['lat'],
                    "arrival_lon": arr_coords['lon'],
                    "group": group
                }
                routes.append(route)

    # Now, use the 'routes' list to plot on the map
    fig = create_figure_with_routes(routes)  # Adjust this function to create the figure based on your routes list

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


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)