#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from functools import wraps

from flask import Flask, request, session, render_template, redirect
import mongoengine

import config
from model.user import User
from model.exercise import Exercise
from utils import test_db
from api import rest_api

# \ ! / Monkey patching mongoengine to make json dumping easier
mongoengine.Document.to_dict = lambda s : json.loads(s.to_json())


# Initializing the web app and the database
app = Flask(__name__)
app.secret_key = config.secret_key
app.config.app_config = config
db = mongoengine.connect(config.db_name)

# Adding the REST API to our web app
app.register_blueprint(rest_api)

# Static tags
tags = ["algorithms", "trees", "sort"]

def requires_login(f):
    """  Decorator for views that requires the user to be logged in """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in', False):
            return redirect('/login')
        else:
            return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_user():
    """ Injects a 'user' variable in templates' context when a user is logged in """
    if session.get('logged_in', False):
        return dict(user=User.objects.get(email=session['email']))
    else:
        return {}

@app.route('/')
def index():
    exercises = Exercise.objects
    return render_template('index.html', exercises=exercises, tags=tags)

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html', error=False)

@app.route('/login', methods=['POST'])
def process_login():
    email, password = request.form['email'], request.form['password']
    user = User.objects(email=email).first()
    if user is None or not user.valid_password(password):
        app.logger.warning("Couldn't login : {}".format(user))
        return render_template('login.html', error=True, email=email)
    else:
        session['logged_in'] = True
        session['email'] = user.email
        return redirect('/')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/')

@app.route('/searchByWords', methods=['POST'])
def search_words():
    words = request.form['recherche']
    words = words.lower()
    find = [words] + words.split()

    exercises = Exercise.objects
    found = list(set([e for e in exercises for w in find if w in e.title.lower() or w in e.description.lower()]))

    return render_template('index.html', exercises=found, tags=tags)

@app.route('/searchByTag/<tag>')
def search_tag(tag):
    exercises = Exercise.objects(tags = tag)
    #found = [e for e in exercises if tag in e.tags]
    return render_template('index.html', exercises=exercises, tags=tags)

@app.route('/exercise/<exercise_id>')
@requires_login
def exercise(exercise_id):
    exercise = Exercise.objects.get(id=exercise_id)
    return render_template('exercise.html', exercise=exercise)

if __name__ == "__main__":
    test_db()
    app.run(debug=True)

