# PIC-16B-Project

Welcome to our project page!

Our project is designed to help airline travelers get a better estimate of the future status of their flights, more specifically the probability they will be delayed. Using this app, a user will be able to check the delay estimate of a single flight, enter an entire itinerary of flights, and much more!

Below is a brief overview on the project process, discussing each step we took along the way.

Project Selection:

When selecting project topics, several factors contributed to our choice of this topic. Firstly, it was evident rather right away that we would be able to access large amounts of data regarding the flights we were planning on using to create our models. In fact, there was so much information out there that even after all data manipulation and preprocessing, our database ended up being just over three gigabytes.

Data Acquisition:

We started by importing flights data from the US Bureau of Transportation. The data contains all flights that have departure and arrival location in the United States from November of 2022 to November of 2023. We then obtained data on every airport in the United States using an API. This ended up being a very large amount of data (about 6GB). We stored the data in a SQL database to allow us to subset it and access it more easily.

Creating Model:

We wanted to predict whether or not a flight would be delayed by more that 15 minutes. This is a binary classification problem. We started by testing many deep neural network models, but ended up using a random forest model. This model can predict whether a flight will be delayed with 83% accuracy.

Webapp Creation:

Our webapp was built using the Flask framework, as well as implementing visualizations from Dash on top, which are discussed in the following section. The main purpose for the website is to allow our users to access model results for their flights in an easy, intuitive manner. In its simplest form, this is accomplished by the 'Check Flight' page. This page allows a user to input their flight origin, destination, airline, and arrival and departure times to be used by our model. They are then redirected to a page displaying our estimate of their flight delays. Similarly, the itinerary page allows a user to input multiple flights, perhaps for an entire travel day, and are shown a visualization of their travel plan AS WELL AS A MODEL ESTIMATE FOR THEIR FLIGHTS SHOULD THEY DESIRE? Additionally, a logged in user is able to SAVE THEIR ITINERARIES and flights for later, should they wish to come back and revisit them at a later date.

Dash Visuals:

Summarize creation of Dash app

## Database Link:

The SQL database that we used for this project was too large to put in the GitHub, but it can be downloaded using this link:
[Access the Database](https://flightdata16b.s3.us-west-1.amazonaws.com/flight_data.db)
