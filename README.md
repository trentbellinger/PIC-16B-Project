# PIC-16B-Project

Welcome to our project page!

Our project is designed to help airline travelers get a better estimate of the future status of their flights, more specifically the probability they will be delayed. Using this app, a user will be able to check the delay estimate of a single flight, enter an entire itinerary of flights, and much more!

Below is a brief overview on the project process, discussing each step we took along the way.

## Project Selection:

When selecting project topics, several factors contributed to our choice of this topic. Firstly, it was evident rather right away that we would be able to access large amounts of data regarding the flights we were planning on using to create our models. In fact, there was so much information out there that even after all data manipulation and preprocessing, our database ended up being just over three gigabytes.

## Data Acquisition:

We started by importing flights data from the US Bureau of Transportation. The data contains all flights that have departure and arrival location in the United States from November of 2022 to November of 2023. We then obtained data on every airport in the United States using an API. This ended up being a very large amount of data (about 6GB). We stored the data in a SQL database to allow us to subset it and access it more easily.

## Creating Model:

We wanted to predict whether or not a flight would be delayed by more that 15 minutes. This is a binary classification problem. We started by testing many deep neural network models, but ended up using a random forest model. This model can predict whether a flight will be delayed with 83% accuracy.

## Webapp Creation:

Our webapp was built using the Flask framework, as well as implementing visualizations from Dash on top, which are discussed in the following section. The main purpose for the website is to allow our users to access model results for their flights in an easy, intuitive manner. In its simplest form, this is accomplished by the 'Check Flight' page. This page allows a user to input their flight origin, destination, airline, and arrival and departure times to be used by our model. They are then redirected to a page displaying our estimate of their flight delays. Similarly, the itinerary page allows a user to input multiple flights, perhaps for an entire travel day, and are shown a visualization of their travel plan AS WELL AS A MODEL ESTIMATE FOR THEIR FLIGHTS SHOULD THEY DESIRE? Additionally, a logged in user is able to SAVE THEIR ITINERARIES and flights for later, should they wish to come back and revisit them at a later date.

## Dash Visuals:

We created a Plotly Dash app that has interactive visuals to help users understand and get insight to flight delays. The app is equipped to handle data transformations and plotting, making it a comprehensive tool for travelers looking to optimize their itineraries.

It features three core visualizations:

1. Flight Routes Visualization: Users can input up to ten pairs of departure and arrival airport codes to plot the routes on a map. The routes are color-coded by average delay proportions, helping users identify which routes typically experience more delays.

2. Heatmap: This displays a heatmap overlay on a U.S. map, showing the volume of flights departing from each airport (denoted by the size of the circles) and the proportion of those flights that are delayed (indicated by the color intensity).

3. Rush Hour Analysis: By entering an airport code and a specific hour, users can generate a bar chart that reveals the busiest times for departures at that airport, providing insights into peak travel hours and potential rush times.

The app's layout includes a markdown block at the top that explains the functionalities and how to use the app. A RadioItems selection lets users choose between the flight routes, heatmap, or rush hour visualizations, dynamically updating the display content based on their choice.

## Database Link:

The SQL database that we used for this project was too large to put in the GitHub, but it can be downloaded using this link:
[Access the Database](https://flightdata16b.s3.us-west-1.amazonaws.com/flight_data.db)

## Guide on How to Use:

1. Download the SQL database.
2. Run the code in the FlightModel.ipynb after the "Model to Predict Flight Delay" section header. (the model creation and saving may take a few minutes to run)
3. Add the flights_rf.joblib file to the flightSite folder.
4. Run the flask app found in the flightSite folder.
