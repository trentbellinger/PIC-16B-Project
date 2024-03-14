from flask import Flask, render_template, request, flash
from flask import redirect, url_for, abort, session
from db import get_db, close_db
from auth import login, register, auth_bp
from datetime import datetime as dt
import time
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import dash
from dash import Input, Output, callback, dcc, html, State, MATCH, ALL, Dash
import os
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple

# Initializing flask app, allowing configuration from config.py
server = Flask(__name__)
server.config.from_pyfile('config.py')

# Registering pages from auth.py file
server.register_blueprint(auth_bp)

# Creating pandas dataframes from csv files
route_delays = pd.read_csv('route_delays.csv')
airport_coords_df = pd.read_csv('airport_coords_df.csv')
dep_delay = pd.read_csv('dep_delay.csv')
flightInputs = pd.read_csv('airportInput.csv')

# Adjusting dataframe contents
route_delays['route_key'] = route_delays['ORIGIN'] + '_' + route_delays['DEST']
route_delays = route_delays.drop_duplicates(subset='route_key')

# Making dictionaries from dataframes
airport_coordinates = airport_coords_df.set_index('ORIGIN')[['lat', 'lon']].to_dict(orient='index')
flightInputDict = flightInputs.set_index('DEST')['INFO'].to_dict()
# route group dictionary
route_dict = route_delays.set_index('route_key')['Group'].to_dict()
count_dict = dep_delay.set_index('ORIGIN')['flight_count'].to_dict()
dep_del_dict = dep_delay.set_index('ORIGIN')['DEP_DEL15'].to_dict()

# Creating dictionary with airline names as keys and their codes as values
airlineDict = {'Endeavor Air': '9E', 'American Airlines':'AA', 'Alaska Airlines':'A5', 'JetBlue':'B6', 'CommuteAir':'C5', 'Delta Air Lines':'DL', 'Frontier Airlines':'F9', 'Allegiant Air':'G4', 'GoJet Airlines':'G7', 'Hawaiian Airlines':'HA', 'Envoy Air':'MQ', 'Spirit Airlines':'NK','PSA Airlines':'OH', 'SkyWest Airlines':'OO', 'Air Portugal':'PT', 'Horizon Air':'QX', 'United Airlines':'UA', 'Southwest Airlines':'WN', 'Mesa Airlines':'YV', 'Republic Airways':'YX', 'Air Wisconsin':'ZW'}

# Sorting airline dictionary alphabetically for display purposes
dictKeys = list(airlineDict.keys())
dictKeys.sort()
airlineDict = {i: airlineDict[i] for i in dictKeys}

# Initializing our Dash app to be used for visualization
dash1=dash.Dash(__name__, server=server, url_base_pathname='/dashFlight/')
dash1.layout = html.Div()


'''
Creating path and rendering template for main page.
Will add more to HTML page as right now it is just a welcome message. Planning on summarizing some of our project and suggesting they visit other pages. May create another page with more in depth discussion of methods of our project. 
'''
@server.route('/')
def index():
    return render_template('blog/index.html')
    
'''
Page where user enters a single flight to check the estimate of it being delayed. Page is reached via the link in the navbar and will redirect to /flightDisp page where flight information is to be displayed.
'''
@server.route('/flights', methods = ['GET', 'POST'])
def flights():
    if request.method == 'POST':
        
        # Obtaining flight input from user
        origin = request.form.get('origin')
        destination = request.form.get('destination')
        airline = request.form.get('airline')
        date = request.form.get('date')
        arrivalTime = request.form.get('arrivalTime')
        
        # Altering format of date to make it more readable
        date = dt.strptime(date, '%Y-%m-%dT%H:%M')
        date = date.strftime('%d/%m/%Y %H:%M')
        
        # Altering formate of arrivalTime to make it more readable
        arrivalTime = dt.strptime(arrivalTime, '%Y-%m-%dT%H:%M')
        arrivalTime = arrivalTime.strftime('%d/%m/%Y %H:%M')
        
        # Initializing error to be none
        error = None
        
        # Checking all fields have been filled out, yielding an error if not
        if not origin:
            error = 'Please enter origin.'
        elif not destination:
            error = 'Please enter destination.'
        elif not airline:
            error = 'Please select an airline.'
        elif not date:
            error = 'Please input a departure date and time.'
        elif not arrivalTime:
            error = 'Please enter your estimated arrival time.'
        if error is None:
            # Creating flightList that will be passed to our layout function
            flightList = []
            
            # Initializing flightDict that contains all of the entered flight information
            flightDict = {'origin': origin, 'destination': destination, 'airline': airline, 'depDate':date, 'arrDate':arrivalTime}
            
            # Placing flight information into flightList
            flightList.append(flightDict)
            
            # Calling layoutDash to pass the flight information to Dash app, passed in name of app and flightList
            layoutDash(dash1, flightList)
            
            # Send user to Dash app for visualization
            return redirect('/dashFlight/')
        
        # Flash error if one was present
        flash(error)
    
    #Rendering template, passing in airlineDict and flightInputDict to provide options in the searchable dropdown menus
    return render_template('blog/flights.html', airlineDict = airlineDict, flightInputDict = flightInputDict)
    
'''
MODEL HERE?


Page for displaying flights. As of now displays flight origin, destination, airline, and time. Will have to include our estimate later. NOTE: As of now the user is sent to the Dash app for visualizations of their flight, so model can be included either there or there.
'''
@server.route('/flightDisp', methods=['GET','POST'])
def flightDisp():
    # Obtaining arguments passed form previous page
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    airline = request.args.get('airline')
    date = request.args.get('date')
    arrivalTime = request.args.get('arrivalTime')
    
    # We can input our model here, determining what information we wish to show the user afterwards
    
    #Rendering template, passing in the flight information we acquired from the previous page
    return render_template('blog/flightDisp.html', origin = origin, destination=destination, airline=airline, date=date, arrivalTime = arrivalTime)
    
'''
Page that begins process of inputting an itinerary by getting user input on how many flights are to be inputted. As of now capped at 20 flights. Will redirect to /itinFlights where user will be able to input the details of their flights.
'''
@server.route('/itinNum', methods = ('GET','POST'))
def itineraryInput():
    if request.method == 'POST':
    
        # Getting user input for how many flights to be included in the itinerary
        numFlight = request.form.get('numFlight',type=int)
        
        # Initializing error to be none
        error = None
        
        # Checking to make sure the user input is acceptable for our use
        # Make sure field has been filled
        if not numFlight:
            error = 'An integer number of flights is required.'
            
        # numFlight cannot be zero, wanted different message than not int error
        if numFlight == 0:
            error = 'Number of flights cannot be zero.'
            
        # Check value entered was an integer
        elif isinstance(numFlight, int) != True:
            error = 'Number of flights should be an integer.'
            
        # Check inputted value is positive
        elif numFlight < 1:
            error = 'Number of flights needs to be a postive integer.'
            
        # Set limit at ten flights
        elif numFlight > 10:
            error = 'Number of flights has exceeded maximum limit of ten.'
            
        # Check that there are no errors
        if error is None:
        
            # Send user to /itinFlights page where they will input  information for their flights
            return redirect(url_for("itinFlights", numFlight = numFlight))
            
        # Display error if there is one
        flash(error)
        
    return render_template('blog/itinNum.html')

'''
Page where user is able to input the information for the number of flights they specified on the /itinNum page. Page will forward to /itinDisp page where the complete itinerary is to be displayed.
Still need to write the code to save user input.
'''
@server.route('/itinFlights', methods = ('GET', 'POST'))
def itinFlights():
    # Get the number of flights passed from previous page
    numFlight = int(request.args.get('numFlight'))
    if request.method=='POST':
    
        # Initializing flightList that will contain the data for all of our flights
        flightList=[]
        
        # Run through loop for number of flights requested by user
        for i in range(0,numFlight):
        
            # Taking in user inputs for each flight
            origin = request.form.get(f'origin{i}')
            destination = request.form.get(f'destination{i}')
            airline = request.form.get(f'airline{i}')
            date = request.form.get(f'date{i}')
            arrivalTime = request.form.get(f'arrivalTime{i}')
            
            # Creating a dictionary for each flight, containing user's information
            flightDict = {'origin': origin, 'destination': destination, 'airline': airline, 'depDate':date}
            
            # Adding information from each flight to flightList
            flightList.append(flightDict)
        
        # Calling layoutDash to pass in the user's flight information to Dash app, passing in app name and flightList
        layoutDash(dash1, flightList)
        
        # Sending user to Dash app for visualization
        return redirect('/dashFlight')
    
    # Rendering template, passing in numFlight for iterative purposes, as well as two dictionaries that the searchable dropdowns will access for their options
    return render_template('blog/itinFlights.html', numFlight = numFlight, airlineDict=airlineDict, flightInputDict = flightInputDict)

'''
Page displays a single itinerary of their choosing from page /allItins. Will have a 'Back to my itineraries' and 'Back to main' buttons.
Still need to write code and finish HTML file.
NOTE: May or may not be implemented
'''
@server.route('/myItin')
def myItin():
    return render_template('blog/myItin.hmtl')

'''
Saves a created itinerary and then reroutes to /allItins page. Only possible to be called if user is logged in.
Still need to write code and finish HTML file.
NOTE: May or may not be implemented
'''
@server.route('/saveItin')
def saveItin():
    #write code to enter itinerary into database
    return redirect(url_for('allItins'))

'''
This function defines the layout for our Dash app once the information to be displayed has been read in. This was easiest way to pass information from Flask to Dash.
Function takes in the name of the app we wish to define the layout for, as well as a list containing the flight information for one or more flights.
NOTE: Going to add navbar from Flask app to allow user to get back to main site. Need to finish formatting.
'''
def layoutDash(dashName, flightDict):
        dashName.layout = html.Div([
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
        dcc.RadioItems(
            id='vis-mode-selector',
            options=[
                {'label': 'Flight Routes', 'value': 'routes'},
                {'label': 'Heatmap', 'value': 'heatmap'}
            ],
            value='routes',  # Default value
            labelStyle={'display': 'block'}
        ),

        # Main container for the layout below the markdown text block
        html.Div([
            # Container for the first column (inputs and the button)
            html.Div([
                # Sub-container for just the inputs
                html.Div([
                    html.Div([
                        dcc.Input(id={'type': 'departure-input', 'index': i}, type='text', placeholder=f'Departure {i}', value=flightDict[i]['origin']),
                        dcc.Input(id={'type': 'arrival-input', 'index': i}, type='text', placeholder=f'Arrival {i}', value=flightDict[i]['destination'])
                    ], style={'padding': '10px'})
                    for i in range(0, len(flightDict))
                ]),
                html.Div([
                    html.Div([
                        dcc.Input(id={'type': 'departure-input', 'index': i}, type='text', placeholder=f'Departure {i}'),
                        dcc.Input(id={'type': 'arrival-input', 'index': i}, type='text', placeholder=f'Arrival {i}')
                    ], style={'padding': '10px'})
                    for i in range(len(flightDict)+1, 11)
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

'''
Dash1 Callback Function
'''
# Callback to update the map based on the inputs

@dash1.callback(
    Output('map', 'figure'),
    [Input('plot-button', 'n_clicks'),
     Input('vis-mode-selector', 'value')],
    [State({'type': 'departure-input', 'index': ALL}, 'value'),
     State({'type': 'arrival-input', 'index': ALL}, 'value')]
)


def update_map(n_clicks, vis_mode, departures, arrivals):
    routes = []

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
    

    # Now, use the 'routes' list to plot on the map
    if vis_mode == 'heatmap':
        fig = create_composite_map()
    elif vis_mode == 'routes':
        fig = create_figure_with_routes(routes)  # Adjust this function to create the figure based on your routes list
    else:
        # Default case if neither mode is selected
        fig = go.Figure()

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

