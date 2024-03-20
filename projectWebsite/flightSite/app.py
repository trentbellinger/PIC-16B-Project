from flask import Flask, render_template, request, flash
from flask import redirect, url_for, abort, session
from db import get_db, close_db
from auth import login, register, auth_bp, login_required
from datetime import datetime as dt
import time
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import dash
from dash import Input, Output, callback, dcc, html, State, MATCH, ALL, Dash
import dash_bootstrap_components as dbc
import os
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from sklearn.ensemble import RandomForestClassifier
from joblib import load

# Initializing flask app, allowing configuration from config.py
server = Flask(__name__)
server.config.from_pyfile('config.py')

# Registering pages from auth.py file
server.register_blueprint(auth_bp)

# Creating pandas dataframes from csv files
route_delays = pd.read_csv('route_delays.csv')
airport_coords_df = pd.read_csv('airport_coords_df.csv')
dep_delay = pd.read_csv('dep_delay.csv') #new
flightInputs = pd.read_csv('airportInput.csv')
distances = pd.read_csv('distances.csv')
dep_count = pd.read_csv('dep_count.csv')


# Importing model for flight classification
rf_model = load("flights_rf.joblib")

# Adjusting dataframe contents
route_delays['route_key'] = route_delays['ORIGIN'] + '_' + route_delays['DEST']
route_delays = route_delays.drop_duplicates(subset='route_key') # new

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
@server.route('/', methods=['GET', 'POST'])
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
            #layoutDash(dash1, flightList)
            
            # get airline abbreviation
            airline_abr = airlineDict[airline]
            
            # get day, month, year, and time as integers
            dep_date_split = date.replace('/', ' ').replace(':', ' ').split()
            day_of_month = int(dep_date_split[0])
            month = int(dep_date_split[1])
            year = int(dep_date_split[2])
            dep_time = int(dep_date_split[3] + dep_date_split[4])
            
            # get arrival time
            arr_date_split = arrivalTime.replace('/', ' ').replace(':', ' ').split()
            arr_time = int(arr_date_split[3] + arr_date_split[4])

            # get origin longitude and latitude
            origin_lon = airport_coords_df.loc[airport_coords_df["ORIGIN"] == origin, "lon"].tolist()[0]
            origin_lat = airport_coords_df.loc[airport_coords_df["ORIGIN"] == origin, "lat"].tolist()[0]

            # get destination longitude and latitude
            dest_lon = airport_coords_df.loc[airport_coords_df["ORIGIN"] == destination, "lon"].tolist()[0]
            dest_lat = airport_coords_df.loc[airport_coords_df["ORIGIN"] == destination, "lat"].tolist()[0]

            distance = distances.loc[(distances["ORIGIN"] == origin) & (distances["DEST"] == destination), "AVG_DISTANCE"].tolist()[0]

            if airline in ['PT', 'YX', '9E', 'QX', 'OH', 'OO', 'C5', 'G7', 'MQ']:
                carrier = 0
            elif airline in ['HA', 'ZW', 'YV', 'WN']:
                carrier = 1
            elif airline in ['DL', 'AA', 'G4', 'UA', 'AS']:
                carrier = 2
            else:
                carrier = 3

            X_new = pd.DataFrame({'YEAR':year, 'MONTH':month, 'DAY_OF_MONTH':day_of_month,
                                  'DEP_TIME':dep_time, 'ARR_TIME':arr_time,
                                  'OP_UNIQUE_CARRIER':carrier, 'DISTANCE':distance,
                                  'ORIGIN_LATITUDE':origin_lat, 'ORIGIN_LONGITUDE':origin_lon,
                                  'DEST_LATITUDE':dest_lat, 'DEST_LONGITUDE':dest_lon}, index = [0])

            pred = rf_model.predict(X_new).tolist()[0]

            if pred == 0:
                delay = "our model predicts no delays for your flight."
            elif pred == 1:
                delay = "our model predicts that your flight will be delayed at least fifteen minutes."
            else:
                delay = "our model returned inconclusive results."
            
            # Send user to Dash app for visualization
            #return redirect('/dashFlight/')
            return redirect(url_for("flightDisp", origin=origin, destination=destination, airline=airline, date=date, arrivalTime=arrivalTime, delay=delay, pred = pred))
        
        # Flash error if one was present
        flash(error)
    
    #Rendering template, passing in airlineDict and flightInputDict to provide options in the searchable dropdown menus
    return render_template('blog/flights.html', airlineDict = airlineDict, flightInputDict = flightInputDict)
 
'''
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
    delay = request.args.get('delay')
    pred = request.args.get('pred')
    # We can input our model here, determining what information we wish to show the user afterwards
    if request.method == 'POST':
        if request.form.get('action') == "See my flight":
            flightList = []
            date = dt.strptime(date, '%d/%m/%Y %H:%M')
            date = date.strftime('%Y-%m-%dT%H:%M')
            sesDate = dt.strptime(date, '%Y-%m-%dT%H:%M')
            arrivalTime = dt.strptime(arrivalTime, '%d/%m/%Y %H:%M')
            arrivalTime = arrivalTime.strftime('%Y-%m-%dT%H:%M')
            flightDict = {'origin': origin, 'destination': destination, 'airline': airline, 'depDate':date, 'arrTime':arrivalTime}
            flightList.append(flightDict)
            session['dateDash'] = sesDate.hour
            session['dashboard_id'] = flightList
            return redirect(url_for("/dashFlight/"))
        if request.form.get('action') == "Save as itinerary":
            flightList = []
            date = dt.strptime(date, '%d/%m/%Y %H:%M')
            date = date.strftime('%Y-%m-%dT%H:%M')
            arrivalTime = dt.strptime(arrivalTime, '%d/%m/%Y %H:%M')
            arrivalTime = arrivalTime.strftime('%Y-%m-%dT%H:%M')
            flightDict = {'origin': origin, 'destination': destination, 'airline': airline, 'depDate':date, 'arrTime':arrivalTime}
            flightList.append(flightDict)
            session['dashboard_id'] = flightList
            return redirect(url_for('saveItin'))
        if request.form.get('action') == "Back to main":
            return redirect(url_for("index"))
    #Rendering template, passing in the flight information we acquired from the previous page
    return render_template('blog/flightDisp.html', origin=origin, destination=destination, airline=airline, date=date, arrivalTime=arrivalTime, delay=delay)
  
  
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
'''
@server.route('/itinFlights', methods = ('GET', 'POST'))
def itinFlights():
    # Get the number of flights passed from previous page
    numFlight = int(request.args.get('numFlight'))
    
    if request.method=='POST':
        # Instructions if user selects the 'See itinerary' button
        if request.form.get('action') == "See itinerary":
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
                flightDict = {'origin': origin, 'destination': destination, 'airline': airline, 'depDate':date, 'arrTime':arrivalTime}
                
                # Adding information from each flight to flightList
                flightList.append(flightDict)
            
            
            # Calling layoutDash to pass in the user's flight information to Dash app, passing in app name and flightList
            
            #layoutDash(dash1, flightList)
            
            # Converting first depDate to a datetime object that we will be able to extract the hour value
            sesDate = dt.strptime(flightList[0]['depDate'], '%Y-%m-%dT%H:%M')
            
            # Saving variables to session so that the Dash app will be able to access them
            session['dateDash'] = sesDate.hour
            session['dashboard_id'] = flightList
            session['numFlight'] = numFlight
            
            # Sending user to Dash app for visualization
            return redirect(url_for('/dashFlight/', flightList = flightList))
        
        # Instructions if user clicks 'Save itinerary' button
        elif request.form.get('action') == "Save itinerary":
        
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
                flightDict = {'origin': origin, 'destination': destination, 'airline': airline, 'depDate':date, 'arrTime':arrivalTime}
                
                # Adding information from each flight to flightList
                flightList.append(flightDict)
            
            
            # Calling layoutDash to pass in the user's flight information to Dash app, passing in app name and flightList
            
            #layoutDash(dash1, flightList)
            
            # Converting sesDate to a datetime object
            sesDate = dt.strptime(flightList[0]['depDate'], '%Y-%m-%dT%H:%M')
            
            # Saving certain variables to session so they can be used by next page
            session['dateDash'] = sesDate.hour
            session['dashboard_id'] = flightList
            session['numFlight'] = numFlight
            
            # Redirecting to save page
            return redirect(url_for('saveItin'))
    
    # Rendering template, passing in numFlight for iterative purposes, as well as two dictionaries that the searchable dropdowns will access for their options
    return render_template('blog/itinFlights.html', numFlight = numFlight, airlineDict=airlineDict, flightInputDict = flightInputDict)


'''
Page displays all the itineraries for the logged in user.
'''
@server.route('/dispItins', methods =('GET', 'POST'))
@login_required
def itinsDisp():
    # Opening connection with database
    db = get_db()
    
    # Getting list of all flights in itineraries created by current user
    flights = db.execute(
        'SELECT f.id, f.itin_id, author_id, origin, destination, airline, depTime, arrTime'
        ' FROM itineraries f WHERE author_id = ?', (session['user_id'],)
    ).fetchall()
    
    # Initializing empty list that will contain flight information
    flights_list = []
    # Converting information for flights from database into a dictionary for each flight
    for flight in flights:
        flight_dict = {
            'id': flight['id'],
            'itin_id': flight['itin_id'],
            'author_id': flight['author_id'],
            'origin': flight['origin'],
            'destination': flight['destination'],
            'airline': flight['airline'],
            'depTime': flight['depTime'],
            'arrTime': flight['arrTime']
        }
        
        # Adding flight dictionaries to flights_list
        flights_list.append(flight_dict)
             
    # Obtaining all unique itinerary ids in user's itineraries
    itin_ids=[]
    for flight in flights:
        if flight['itin_id'] not in itin_ids:
            itin_ids.append(flight['itin_id'])
    
    
    if request.method=='POST':
        dashList = []
        # Run through number of buttons
        for i in range(0,len(itin_ids)+1):
            
            if request.form.get('action') == f'See Itinerary {i}':
                # Get itinID for selected itinerary
                retItinID = itin_ids[i-1]
                # Compile all flights in that itinerary
                for el in flights_list:
                    if el['itin_id']==retItinID:
                        dashList.append(el)
                        
                # Assign session variables to be used by the dash app
                sesDate = dt.strptime(dashList[0]['depTime'], '%d/%m/%Y %H:%M')
                session['dashboard_id'] = dashList
                session['dateDash'] = sesDate.hour
                # Redirecting to Dash app
                return redirect(url_for('/dashFlight/'))
                        
    return render_template('blog/itinsDisp.html', flights = flights)


'''
Saves a created itinerary and then reroutes to /allItins page. Only possible to be called if user is logged in.
Still need to write code and finish HTML file.
NOTE: May or may not be implemented
'''
@server.route('/saveItin')
@login_required
def saveItin():
    # Opening database connection
    db = get_db()
    # Using dummy variable to help assign itinerary ids
    dumVar = 'textCount'
    # Adding dummy variable to itineraryCounter table so we can figure out how many itineraries we have
    db.execute(
        'INSERT INTO itineraryCounter (counter) VALUES (?)',
        (dumVar,))
    # Commiting insertion into itineraryCounter
    db.commit()
    # Finding max itin_id from table and incrementing our variable by one for new itinerary
    itin_id = db.execute('SELECT MAX(itin_id) FROM itineraries').fetchone()[0]
    if itin_id is None:
        itin_id = 1
    else:
        itin_id += 1
    
    # Changing format of time for disply
    for i in range(0, len(session['dashboard_id'])):
        session['dashboard_id'][i]['depDate'] = dt.strptime(session['dashboard_id'][i]['depDate'], '%Y-%m-%dT%H:%M')
        session['dashboard_id'][i]['depDate'] = session['dashboard_id'][i]['depDate'].strftime("%d/%m/%Y %H:%M")
        session['dashboard_id'][i]['arrTime'] = dt.strptime(session['dashboard_id'][i]['arrTime'], '%Y-%m-%dT%H:%M')
        session['dashboard_id'][i]['arrTime'] = session['dashboard_id'][i]['arrTime'].strftime("%d/%m/%Y %H:%M")
    
    # Placing information into database for each flight in itinerary, all with same itin_id
    for i in range (0, len(session['dashboard_id'])):
        db.execute(
            'INSERT INTO itineraries (itin_id, author_id, origin, destination, airline, depTime, arrTime) VALUES (?,?,?,?,?,?,?)',
            (itin_id, session['user_id'], session['dashboard_id'][i]['origin'], session['dashboard_id'][i]['destination'], session['dashboard_id'][i]['airline'], session['dashboard_id'][i]['depDate'], session['dashboard_id'][i]['arrTime']))
    # Commit and close the database
    db.commit()
    db.close()
    # Sending user to itinerary page where they can see their newly saved itinerary
    return redirect(url_for('itinsDisp'))
    
'''
This function defines the layout for our Dash app once the information to be displayed has been read in. This was easiest way to pass information from Flask to Dash.
Function takes in the name of the app we wish to define the layout for, as well as a list containing the flight information for one or more flights.
NOTE: Going to add navbar from Flask app to allow user to get back to main site. Need to finish formatting.
'''
def layoutDash(dashName, flightDict):
        
        # Applying styling to Dash app
        dashName.index_string = '''
            <!DOCTYPE html>
            <html>
                <head>
                    {%metas%}
                    <title>{%title%}</title>
                    {%favicon%}
                    {%css%}
                    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.0.0/dist/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
                </head>
                
            </section>
                <body>
                    <script src="https://code.jquery.com/jquery-3.2.1.slim.min.js" integrity="sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN" crossorigin="anonymous"></script>
                    <script src="https://cdn.jsdelivr.net/npm/popper.js@1.12.9/dist/umd/popper.min.js" integrity="sha384-ApNbgh9B+Y1QKtv3Rn7W3mgPxhU9K/ScQsAP7hUibX39j7fakFPskvXusvfa0b4Q" crossorigin="anonymous"></script>
                    <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.0.0/dist/js/bootstrap.min.js" integrity="sha384-JZR6Spejh4U02d8jOt6vLEHfe/JQGiRRSQQxSfFWpi1MquVdAyjUar5+76PVCmYl" crossorigin="anonymous"></script>
                        <div></div>
                    {%app_entry%}
                    <footer>
                        {%config%}
                        {%scripts%}
                        {%renderer%}
                    </footer>
                    <div></div>
                </body>
            </html>
            '''
        dashName.layout = html.Div([
        
        # Creating Navbar to allow user to travel back to main app
        dbc.Navbar(
        children=[
            html.A(
                    className="navbar-brand",
                    children=[
                        html.Img(src="/assets/airplaneBrand3.png", height="30px"),
                        "My Dashboard"
                    ],
                    href="#"
                ),
            dbc.NavItem(dbc.NavLink("Home", href="/", external_link=True)),
            dbc.NavItem(dbc.NavLink("Check Flight", href="/flights", external_link=True)),
            dbc.NavItem(dbc.NavLink("Create Itinerary", href="/itinNum", external_link=True)),
            
            dbc.NavItem(dbc.DropdownMenu(
                children=[
                    dbc.DropdownMenuItem("Account", header=True),
                    dbc.DropdownMenuItem("Register", href="/auth/register", external_link=True),
                    dbc.DropdownMenuItem("Login", href="/auth/login", external_link=True)
                ],
                nav=True,
                in_navbar=True,
                label="More",
            )),
        ],
        brand=html.Div(
            [
                html.Img(src="/assets/airplaneBrand3.png", height="30px"),
                html.Span("Project Site", style={"margin-left": "10px", "vertical-align": "middle"})
            ],
            style={"display": "flex", "align-items": "center"}
        ),
        brand_external_link = True,
        brand_href="/",
        color="primary",
        dark=True,
        fluid=True,
        ),
        
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
                {'label': 'Heatmap', 'value': 'heatmap'},
                {'label': 'Rush Hour', 'value': 'hour'}
            ],
            value='routes',  # Default value
            labelStyle={'display': 'block'}
        ),
            # NEW EDIT
        html.Div(id='page-content')
    ])

        # Main container for the layout below the markdown text block
        html.Div([
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
                dcc.Graph(id='map', figure=go.Figure(layout={'title': 'Please select departure and arrival locations and click "Plot Routes"'}))
            ], style={'flex': 2}),
        ], style={'display': 'flex', 'width': '100%'}),
        ], style={'alignItems': 'flex-start', 'justifyContent': 'center', 'height': '100vh'}, id ='content-route')








dash1.index_string = '''
    <!DOCTYPE html>
    <html>
        <head>
            {%metas%}
            <title>{%title%}</title>
            {%favicon%}
            {%css%}
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.0.0/dist/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
        </head>
        
    </section>
        <body>
            <script src="https://code.jquery.com/jquery-3.2.1.slim.min.js" integrity="sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN" crossorigin="anonymous"></script>
            <script src="https://cdn.jsdelivr.net/npm/popper.js@1.12.9/dist/umd/popper.min.js" integrity="sha384-ApNbgh9B+Y1QKtv3Rn7W3mgPxhU9K/ScQsAP7hUibX39j7fakFPskvXusvfa0b4Q" crossorigin="anonymous"></script>
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.0.0/dist/js/bootstrap.min.js" integrity="sha384-JZR6Spejh4U02d8jOt6vLEHfe/JQGiRRSQQxSfFWpi1MquVdAyjUar5+76PVCmYl" crossorigin="anonymous"></script>
                <div></div>
            {%app_entry%}
            <footer>
                {%config%}
                {%scripts%}
                {%renderer%}
            </footer>
            <div></div>
        </body>
    </html>
    '''
dash1.layout = html.Div([

# Creating Navbar to allow user to travel back to main app
dbc.NavbarSimple(

children=[
    html.A(
        className="navbar-brand",
        children=[
            html.Img(src="/static/airplaneBrand3.png", height="30px"),
            "Project Site"
        ],
        href="/"
    ),
    dbc.NavItem(dbc.NavLink("Home", href="/", external_link=True)),
    dbc.NavItem(dbc.NavLink("Check Flight", href="/flights", external_link=True)),
    dbc.NavItem(dbc.NavLink("Create Itinerary", href="/itinNum", external_link=True)),
    
    dbc.NavItem(dbc.DropdownMenu(
        children=[
            dbc.DropdownMenuItem("Account", header=True),
            dbc.DropdownMenuItem("Register", href="/auth/register", external_link=True),
            dbc.DropdownMenuItem("Login", href="/auth/login", external_link=True)
        ],
        nav=True,
        in_navbar=True,
        label="More",
    )),
],
#brand="Project Site",
#brand_external_link = True,
#brand_href="/",
color="primary",
dark=True,
fluid=True,
),

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
        {'label': 'Heatmap', 'value': 'heatmap'},
        {'label': 'Rush Hour', 'value': 'hour'}
    ],
    value='routes',  # Default value
    labelStyle={'display': 'block'}
),
    # NEW EDIT
html.Div(id='page-content')
])

# Main container for the layout below the markdown text block
html.Div([
html.Div([
    # Container for the first column (inputs and the button)
    html.Div([
        # Sub-container for just the inputs
        html.Div([
            html.Div([
                dcc.Input(id={'type': 'departure-input', 'index': i}, type='text', placeholder=f'Departure {i}'),
                dcc.Input(id={'type': 'arrival-input', 'index': i}, type='text', placeholder=f'Arrival {i}')
            ], style={'padding': '10px'})
            for i in range(0, 10)
        ]),
        # Button to plot routes
        html.Button('Plot Routes', id='plot-button', n_clicks=0, style={'margin-top': '20px'}),
    ], style={'display': 'flex', 'flexDirection': 'column', 'marginRight': '20px'}),  # marginRight added to separate the columns
    
    # Container for the second column (the map)
    html.Div([
        dcc.Graph(id='map', figure=go.Figure(layout={'title': 'Please select departure and arrival locations and click "Plot Routes"'}))
    ], style={'flex': 2}),
], style={'display': 'flex', 'width': '100%'}),
], style={'alignItems': 'flex-start', 'justifyContent': 'center', 'height': '100vh'}, id ='content-route')
'''
Dash1 Callback Function
'''
# Callback to update the map based on the inputs
@dash1.callback(
    Output('page-content', 'children'),
    [Input('vis-mode-selector', 'value')],
    prevent_initial_call=False
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
                        dcc.Input(id={'type': 'departure-input', 'index': i}, type='text', placeholder=f'Departure {i}', value=session.get('dashboard_id', None)[i]['origin']),
                        dcc.Input(id={'type': 'arrival-input', 'index': i}, type='text', placeholder=f'Arrival {i}', value=session.get('dashboard_id', None)[i]['destination'])
                    ], style={'padding': '10px'})
                    for i in range(0, int(len(session.get('dashboard_id', None))))
                ]),
                html.Div([
                    html.Div([
                        dcc.Input(id={'type': 'departure-input', 'index': i}, type='text', placeholder=f'Departure {i}'),
                        dcc.Input(id={'type': 'arrival-input', 'index': i}, type='text', placeholder=f'Arrival {i}')
                    ], style={'padding': '10px'})
                    for i in range(int(len(session.get('dashboard_id', None)))+1, 11)
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
                    dcc.Input(id='origin-input', type='text', placeholder= 'Departure', value = session.get('dashboard_id', None)[0]['origin']),
                    dcc.Input(id='hour-input', type='text', placeholder= 'Hour', value = session.get('dateDash', None))
                ], style={'padding': '10px'}),
            html.Button('Update', id='update-button', n_clicks=0),
            dcc.Graph(id='hist', figure = go.Figure(layout={'title': 'Please enter departure location and hour and click "Update"'}))
        ], id='content-hour')
    else:
        return html.Div("Select a visualization mode.", id='default-view')


@dash1.callback(
    Output('hist', 'figure'),
    [Input('vis-mode-selector', 'value'),
     Input('update-button', 'n_clicks')],
    [State('origin-input', 'value'), State('hour-input', 'value')],
    prevent_initial_call = False
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
@dash1.callback(
    #Output('content-route', 'children'),
    Output('map', 'figure'),
    [Input('vis-mode-selector', 'value'),
     Input('plot-button', 'n_clicks')],
    [State({'type': 'departure-input', 'index': ALL}, 'value'),
     State({'type': 'arrival-input', 'index': ALL}, 'value'),
    ]
    #prevent_initial_call = True
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


@dash1.callback(
    Output('content-heatmap', 'children'),
    Input('vis-mode-selector', 'value'),
    prevent_initial_call=False
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


'''
{% extends 'base.html'%}

{% block header%}
    <h1>{%block title%}Your itinerary{%endblock%}
{%endblock%}

{%block content%}
    {% for itinerary_id, itinerary_flights in flights|groupby('itin_id') %}
        <h2>Itinerary {{loop.index}}</h2>
        <table>
            <tbody>
                {% for flight in itinerary_flights %}
                <tr>
                    <th>Flight {{loop.index}}</th>
                    <td> </td>
                </tr>
                <tr>
                    <th>Origin:</th>
                    <td>{{ flight.origin }}</td>
                </tr>
                <tr>
                    <th>Destination:</th>
                    <td>{{ flight.destination }}</td>
                </tr>
                <tr>
                    <th>Airline:</th>
                    <td>{{ flight.airline }}</td>
                </tr>
                <tr>
                    <th>Departure Time:</th>
                    <td>{{ flight.depTime }}</td>
                </tr>
                <tr>
                    <th>Arrival Time:</th>
                    <td>{{ flight.arrTime }}</td>
                </tr>
                <tr>
                    <td colspan="2">&nbsp;</td> <!-- Empty row -->
                </tr>
                {% endfor %}
            </tbody>
        </table>
    {% endfor %}
    
    <form method="post">
        
        <button id="Enter" type="button" onclick="window.location.href = '{{ url_for('index') }}' ; " class="button">Main</button>

{%endblock%}

'''

'''
{% extends 'base.html'%}

{% block header %}
    <h1>Your itinerary</h1>
{% endblock %}

{% block content %}
    {% for groups in flights %}
        <h2>Itinerary {{loop.index}}</h2>
        <table>
            <tbody>
                {% for entry in groups %}
                    <tr>
                        <th>Origin:</th>
                        <td>{{entry.origin}}</td>
                    </tr>
                    <tr>
                        <th>Destination:</th>
                        <td>{{ entry['destination'] }}</td>
                    </tr>
                    <tr>
                        <th>Airline:</th>
                        <td>{{ entry['airline'] }}</td>
                    </tr>
                    <tr>
                        <th>Departure Time:</th>
                        <td>{{ entry['depTime'] }}</td>
                    </tr>
                    <tr>
                        <th>Arrival Time:</th>
                        <td>{{ entry['arrTime'] }}</td>
                    </tr>
                    <tr>
                        <td colspan="2">&nbsp;</td> <!-- Empty row -->
                    </tr>
                {% endfor %}
            </tbody>
        </table>
    {% endfor %}
    
    <form method="post">
        <button id="Enter" type="button" onclick="window.location.href = '{{ url_for('index') }}' ; " class="button">Main</button>
    </form>
{% endblock %}

'''
