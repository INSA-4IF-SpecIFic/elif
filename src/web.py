#!/usr/bin/env python
# -*- coding: utf-8 -*-
from functools import wraps

from flask import Flask, request, session, render_template, redirect
import mongoengine

import config
from model.user import User
from model.exercise import Exercise
import utils
from api import rest_api

# \ ! / Monkey patching mongoengine to make json dumping easier
mongoengine.Document.to_dict = utils.to_dict

# Initializing the web app and the database
app = Flask(__name__)
app.secret_key = config.secret_key
app.config.app_config = config
db = mongoengine.connect(config.db_name)

# Adding the REST API to our web app
app.register_blueprint(rest_api)

def requires_login(f):
    """  Decorator for views that requires the user to be logged in """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in', None):
            return redirect('/login')
        else:
            return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_user():
    """ Injects a 'user' variable in templates' context when a user is logged in """
    if session.get('logged_in', None):
        return dict(user=User.objects.get(email=session['logged_in']))
    else:
        return dict(user=None)

@app.context_processor
def inject_configuration():
    return dict(config=config)

@app.route('/')
def index():
    occurrences = {}
    tags = set(t for e in Exercise.objects for t in e.tags)
    for t in tags :
        occurrences[t] = str(len(Exercise.objects(tags=t)))
    return render_template('index.html', occurrences=occurrences)

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html', error=None)

@app.route('/login', methods=['POST'])
def process_login():
    email, password = request.form['email'].lower(), request.form['password']
    user = User.objects(email=email).first()
    if user is None or not user.valid_password(password):
        app.logger.warning("Couldn't login : {}".format(user))
        return render_template('login.html', error="Wrong password or username.", email=email)
    else:
        session['logged_in'] = user.email
        return redirect('/')

@app.route('/signup', methods=['GET'])
def signup():
    return render_template('signup.html')

@app.route('/signup', methods=['POST'])
def process_signup():
    # TODO : create a new user
    return render_template('signup.html')

@app.route('/welcome')
def welcome():
    return render_template('welcome.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/')

@app.route('/exercise/<exercise_id>')
@requires_login
def exercise(exercise_id):
    exercise = Exercise.objects.get(id=exercise_id)
    return render_template('exercise.html', exercise=exercise)

@app.route('/new_exercise', methods=['POST'])
def new_exercise():
    sample_exercise = utils.sample_exercise()
    sample_exercise.save()
    return render_template('exercise.html', exercise=sample_exercise)


if __name__ == "__main__":
    utils.test_db()
    app.run(debug=True)

