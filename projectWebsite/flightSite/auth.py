import functools
from flask import (Blueprint, flash, g, redirect, render_template, request, url_for, session)
from werkzeug.security import check_password_hash, generate_password_hash
from db import get_db

#Creating blueprint that will be used to send methods to 'app.py'
#Sets URL prefix to '/auth' for all functions using blueptrint
auth_bp = Blueprint('auth', __name__, url_prefix = '/auth')

'''
Page used for registering new users into the database. Takes in user input for username and password, ensuring username is not already taken, before rerouting to login page.
'''
@auth_bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        #getting user input for their desired username and password
        username = request.form.get('username')
        password = request.form.get('password')
        #opening connection with the database
        db = get_db()
        error = None
        
        #checks to make sure username and password are filled out
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        
        
        if error is None:
            #inserts user information into database
            try:
                db.execute("INSERT INTO user (username, password) VALUES (?,?)", (username, generate_password_hash(password)),
                )
                db.commit()
            #checks if username already exists
            except db.IntegrityError:
                error = f"Username {username} is already registered."
            else:
                #sends user to login page where they can login with their newly created account
                return redirect(url_for("auth.login"))
        #error shown to user if there is one
        flash(error)
    return render_template('auth/register.html')

'''
Page where users are able to log back in.
'''
@auth_bp.route('/login', methods = ('GET', 'POST'))
def login():
    if request.method == 'POST':
        #user enters their username and password
        username = request.form.get('username')
        password = request.form.get('password')
        #opens connection with database
        db = get_db()
        error = None
        #checks for username in database
        user = db.execute('SELECT * FROM user WHERE username = ?', (username,)).fetchone()
        #gives error if username not found
        if user is None:
            error = 'Incorrect username.'
        #checks username password against inputted password
        elif not check_password_hash(user['password'],password):
            error = 'Incorrect password.'
        #resets session and sets user id to user who just logged in
        if error is None:
            session.clear()
            session['user_id'] = user['id']
            #sends us back to main page, now as a logged in user
            return redirect(url_for('index'))
        #flashes error if one exists
        flash(error)
    return render_template('auth/login.html')

'''
Page allowing user to log out, terminating their session. Only able to be reached if someone is currently logged in.
'''
@auth_bp.route('/logout')
def logout():
    #clears session, removing user id
    session.clear()
    #redirects back to main page
    return redirect(url_for('index'))

'''
Attempts to load in previous user if they never logged out. Does nothing if user logged out or if there was no logged in user in the first place.
'''
@auth_bp.before_app_request
def load_logged_in_user():
    #gets user_id from session
    user_id = session.get('user_id')
    #if user_id is none, it means no one was logged in
    if user_id is None:
        g.user = None
    else:
        #setting user to previously logged in user if one is found
        g.user = get_db().execute('SELECT * FROM user WHERE id = ?', (user_id,)).fetchone()

'''
Function checks if there is a login user, and sends user back to login page if not. To be used for pages that only logged in users can access.
'''
def login_required(view):
    @functools.wraps(view)
    #checks if there is a login user
    def wrapped_view(**kwargs):
        if g.user is None:
            #redirects to login page if no user is logged in
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view
