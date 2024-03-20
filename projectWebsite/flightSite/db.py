import sqlite3
from flask import current_app, g


'''
Opens up connection with the database, creating the necessary tables if they have not already been created.
'''
def get_db():
    if 'db' not in g:
        #connecting to database
        g.db = sqlite3.connect("webProj.sqlite")
        #creating cursor so we can interact with database
        cursor = g.db.cursor()
        #execute creation of tables using (CREATE TABLE IF NOT EXISTS)
        #creatin table for user login information
        cursor.execute("CREATE TABLE IF NOT EXISTS user ( id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL)")
        #creating table for itinerary identification
        cursor.execute("CREATE TABLE IF NOT EXISTS itineraryCounter ( id INTEGER PRIMARY KEY AUTOINCREMENT, counter TEXT)")
        #creating table holding information to be stored in itineraries (ex. flight info), to be tied back to each itinerary in previous table via itin_id value
        cursor.execute("CREATE TABLE IF NOT EXISTS itineraries ( id INTEGER PRIMARY KEY AUTOINCREMENT, itin_id INTEGER NOT NULL, author_id TEXT, origin TEXT, destination TEXT, airline TEXT, depTime TEXT, arrTime TEXT)")
        #allowing us to access columns by their name
        g.db.row_factory = sqlite3.Row
        #commiting cursor changes
        g.db.commit()
    return g.db

'''
Function that closes the database for us if there is an open connection
'''
def close_db(e=None):
    #checking for database connection
    db = g.pop('db',None)
    #closes database connection if one is open
    if db is not None:
        db.close()
        
