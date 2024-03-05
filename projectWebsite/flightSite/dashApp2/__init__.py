import dash
from dash import callback, Input, Output, html, dcc, dash_table, Dash
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import dash_mantine_components as dmc

def create_dash_application_2(flask_app):
    
    dash2 = dash.Dash(__name__, server=flask_app, url_base_pathname='/about/')
    dash2.index_string = '''
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
    
    

    
    dash2.layout = dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Home", href="/", external_link=True)),
            dbc.NavItem(dbc.NavLink("Check Flight", href="/flights", external_link=True)),
            dbc.NavItem(dbc.NavLink("Create Itinerary", href="/itinNum", external_link=True)),
            dbc.NavItem(dbc.NavLink("Project Info", href="/about/", external_link=True)),
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
        brand="Project Site",
        brand_external_link = True,
        brand_href="/",
        color="primary",
        dark=True,
        )
    
    return dash2

