import sqlite3
import pandas as pd

def get_flight_model_data():
    '''
    Returns a pandas dataframe of all the necessary predictors to predict flight delay.
    (note: must have the flights.db database)
    Args:
        none
    Returns:
        a pandas dataframe with all necessary predictors
    '''
    with sqlite3.connect("flights.db") as conn:
        cmd = \
        """
        SELECT 
            flights.YEAR, flights.MONTH, flights.DAY_OF_MONTH, flights.DEP_TIME, flights.ARR_TIME, flights.OP_UNIQUE_CARRIER, flights.ORIGIN, flights.DEST, flights.DISTANCE, flights.DEP_DEL15, airports.LATITUDE "ORIGIN_LATITUDE", airports.LONGITUDE "ORIGIN_LONGITUDE"
        FROM 
            flights
        INNER JOIN 
            airports ON flights.ORIGIN = airports.AIRPORT_ID
        """
        df = pd.read_sql_query(cmd, conn)
    with sqlite3.connect("flights.db") as conn:
        cmd = \
        """
        SELECT 
            flights.DEST, airports.LATITUDE "DEST_LATITUDE", airports.LONGITUDE "DEST_LONGITUDE"
        FROM 
            flights
        INNER JOIN 
            airports ON flights.DEST = airports.AIRPORT_ID
        """
        df_dest = pd.read_sql_query(cmd, conn)
    df["DEST_LATITUDE"] = df_dest["DEST_LATITUDE"]
    df["DEST_LONGITUDE"] = df_dest["DEST_LONGITUDE"]
    return df