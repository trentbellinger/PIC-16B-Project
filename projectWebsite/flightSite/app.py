from flask import Flask, render_template, request, flash
from flask import redirect, url_for, abort
from db import get_db, close_db
from auth import login, register, auth_bp
from datetime import datetime as dt
import plotly.express as px
import pandas as pd
import dash
from dash import Input, Output, callback, dcc, html
import os
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from dashApp1 import create_dash_application
from dashApp2 import create_dash_application_2

server = Flask(__name__)
server.config.from_pyfile('config.py')

#registering pages from auth.py file
server.register_blueprint(auth_bp)

#initializing flask apps
create_dash_application(server)
create_dash_application_2(server)
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
        #obtaining input from user
        origin = request.form.get('origin')
        destination = request.form.get('destination')
        airline = request.form.get('airline')
        date = request.form.get('date')
        #changing format of date to make it more readable
        date = dt.strptime(date, '%Y-%m-%dT%H:%M')
        date = date.strftime('%d/%m/%Y %H:%M')
        
        error = None
        
        #Checking all fields have been filled out
        if not origin:
            error = 'Please enter origin.'
        elif not destination:
            error = 'Please enter destination.'
        elif not airline:
            error = 'Please select an airline.'
        elif not date:
            error = 'Please input a date and time.'
        if error is None:
            #sending user to page where flight information is displayed, eventually our estimate as well and potentially dash plot
            return redirect(url_for('flightDisp', origin = origin, destination=destination, airline=airline, date=date))
        #flashing error if one was present
        flash(error)
    
    return render_template('blog/flights.html')
    
'''
Page for displaying flights. As of now displays flight origin, destination, airline, and time. Will have to include our estimate later. Is called after user enters flight information from /flight page
'''
@server.route('/flightDisp', methods=['GET','POST'])
def flightDisp():
    #acquiring arguments passed form previous page to be displayed
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    airline = request.args.get('airline')
    date = request.args.get('date')
    #need to add estimate as well as possible Dash plot to give user an idea of why flight may be ranked the way it is
    return render_template('blog/flightDisp.html', origin = origin, destination=destination, airline=airline, date=date)
    
'''
Page that begins process of inputting an itinerary by getting user input on how many flights are to be inputted. As of now capped at 20 flights. Will redirect to /itinFlights where user will be able to input the details of their flights.
'''
@server.route('/itinNum', methods = ('GET','POST'))
def itineraryInput():
    if request.method == 'POST':
        #getting user input for how many flights to be included in the itinerary
        numFlight = request.form.get('numFlight',type=int)
        error = None
        #ensuring entry is suitable to be used for itinerary
        #making sure field has been filled
        if not numFlight:
            error = 'An integer number of flights is required.'
        #numFlight cannot be zero, wanted different message than not int error
        if numFlight == 0:
            error = 'Number of flights cannot be zero.'
        #ensuring value entered was an integer
        elif isinstance(numFlight, int) != True:
            error = 'Number of flights should be an integer.'
        #checking inputted value is positive
        elif numFlight < 1:
            error = 'Number of flights needs to be a postive integer.'
        #setting cap at twenty
        elif numFlight > 20:
            error = 'Number of flights has exceeded maximum limit of twenty.'
        if error is None:
            #sending user to /itinFlights page where they will input the information for all their flights
            return redirect(url_for("itinFlights", num = numFlight))
        #displaying error if there is one
        flash(error)
        
    return render_template('blog/itinNum.html')

'''
Page where user is able to input the information for the number of flights they specified on the /itinNum page. Page will forward to /itinDisp page where the complete itinerary is to be displayed.
Still need to write the code to save user input.
'''
@server.route('/itinFlights')
def itinFlights():
    #getting numFlight variable passed from previous page, to be used by HTML file
    numFlight = request.args.get('num')
    #rendering template while passing the numFlight value to be used
    #will redirect to /itinDisp page
    return render_template('blog/itinFlights.html', numFlight = int(numFlight))

'''
Page in which the complete itinerary is displayed, coming from /itinFlights page. Offers to save itinerary if user is logged in, or go back to main.
Still need to write code and finish HTML file.
'''
@server.route('/itinDisp', methods=('GET', 'POST'))
def itinerarydisp():
    return render_template('blog/itineraryDisp.html')

'''
Page displays a single itinerary of their choosing from page /allItins. Will have a 'Back to my itineraries' and 'Back to main' buttons.
Still need to write code and finish HTML file.
'''
@server.route('/myItin')
def myItin():
    return render_template('blog/myItin.hmtl')

'''
Saves a created itinerary and then reroutes to /allItins page. Only possible to be called if user is logged in.
Still need to write code and finish HTML file.
'''
@server.route('/saveItin')
def saveItin():
    #write code to enter itinerary into database
    return redirect(url_for('allItins'))

'''
Displays all itinerary that the logged in user has saved. Need to be logged in to access this page.
Still need to write code and finish HTML file.
'''
@server.route('/allItins')
def allItins():
    return render_template('blog/allItinDisp.html')
  
  
