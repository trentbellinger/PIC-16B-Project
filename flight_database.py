import sqlite3
import pandas as pd

def query_flight_database(db_file):

    with sqlite3.connect(db_file) as conn: 
        # conn is automatically closed when this block ends
        cmd = \
        f"""
        SELECT DISTANCE, counts, sin_hour, cos_hour, sin_day, cos_day, target
        FROM air_2023
        """
        df = pd.read_sql_query(cmd, conn)
    return df
