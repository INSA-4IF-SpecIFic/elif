#!/usr/bin/env python
# -*- coding: utf-8 -*-
from functools import wraps

from flask import Flask, request, session, render_template, redirect, g
import mongoengine

import config
from model.user import User
from model.exercise import Exercise, ExerciseProgress
from job import Submission
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

# Decorators and instructions used to inject info into the context
def requires_login(f):
    """  Decorator for views that requires the user to be logged-in """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in', None):
            return redirect('/login')
        else:
            return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_user():
    """ Injects a 'user' variable in templates' context when a user is logged-in """
    if session.get('logged_in', None):
        return dict(user=User.objects.get(email=session['logged_in']))
    else:
        return dict(user=None)

@app.before_request
def load_user():
    """ Injects the current logged-in user (if any) to the request context """
    g.user = User.objects(email=session.get('logged_in')).first()

@app.context_processor
def inject_configuration():
    return dict(config=config)

# Pages
@app.route('/')
def index():
    if g.user:
        return redirect('/exercises')
    breadcrumbs = [('Welcome page', None)]
    return render_template('index.html', breadcrumbs=breadcrumbs)

@app.route('/exercises')
@requires_login
def exercises():
    breadcrumbs = [('Home', '/'), ('Exercises', None)]
    return render_template('exercises.html', breadcrumbs=breadcrumbs)

@app.route('/login', methods=['GET'])
def login():
    breadcrumbs = [('Home', '/'), ('Login', None)]
    return render_template('login.html', error=None, breadcrumbs=breadcrumbs)

@app.route('/signup', methods=['GET'])
def signup():
    breadcrumbs = [('Home', '/'), ('Sign-up', None)]
    return render_template('signup.html', error=None, breadcrumbs=breadcrumbs)

@app.route('/monitoring')
@requires_login
def monitoring():
    if not g.user.editor:
        redirect('/')

    users = User.objects(editor=False)
    exercises = Exercise.objects()
    progress = {user: {p.exercise: p for p in ExerciseProgress.objects(user=user)} for user in users}

    breadcrumbs = [('Home', '/'), ('Monitoring', None)]
    return render_template('monitoring.html', users=users, exercises=exercises, progress=progress, breadcrumbs=breadcrumbs)

@app.route('/profile')
@requires_login
def profile():
    exercises_tried = len([e_p for e_p in ExerciseProgress.objects(user=g.user)])
    exercises_completed = len([e_p for e_p in ExerciseProgress.objects(user=g.user) if e_p.completed])
    rank = list(User.objects.order_by('-score')).index(g.user) + 1
    total_exercises = len(Exercise.objects)

    breadcrumbs = [('Home', '/'), ('Profile', None)]
    return render_template('profile.html', exercises_tried=exercises_tried, exercises_completed=exercises_completed,
                                           rank=rank, total_exercises=total_exercises, breadcrumbs=breadcrumbs)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/')

@app.route('/exercise/<exercise_id>')
@requires_login
def exercise_page(exercise_id):
    exercise = Exercise.objects.get(id=exercise_id)
    submission = Submission.objects(user=g.user,exercise=exercise).order_by('-date_created').first()
    sub_code = submission.code if submission else ""

    breadcrumbs = [('Home', '/'), ('Exercises', '#'), (exercise.title, None)]
    return render_template('exercise.html', exercise=exercise, last_submission_code=sub_code, breadcrumbs=breadcrumbs)

@app.route('/exercise/delete/<exercise_id>')
def delete_exercise(exercise_id):
    exercise = None
    try:
        exercise = Exercise.objects.get(id=exercise_id)
    except mongoengine.DoesNotExist:
        return render_template('exercise.html', ok=False)

    exercise.delete()
    return render_template('exercise.html', ok=True)

@app.route('/new_exercise', methods=['POST'])
def new_exercise():
    sample_exercise = utils.sample_exercise(g.user)
    sample_exercise.save()
    breadcrumbs = [('Home', '/'), ('New exercise', None)]
    return render_template('exercise.html', exercise=sample_exercise, breadcrumbs=breadcrumbs)

# Processing login/signup

@app.route('/login', methods=['POST'])
def process_login():
    email, password = request.form['email'].lower(), request.form['password']
    user = User.objects(email=email).first()
    if user is None or not user.valid_password(password):
        app.logger.warning("Couldn't login : {}".format(user))
        return render_template('login.html', error="Wrong password or username.", email=email)
    else:
        session['logged_in'] = user.email
        inject_user()
        load_user()
        return redirect('/')

@app.route('/signup', methods=['POST'])
def process_signup():
    email, username, password = request.form['email'].lower(), request.form['username'], request.form['password']
    user = User.new_user(email=email, username=username, password=password, editor=False)
    try:
        user.save()
        session['logged_in'] = user.email
        inject_user()
        load_user()
        return redirect('/')
    except mongoengine.ValidationError as e:
        return render_template('signup.html', error=e.to_dict())


if __name__ == "__main__":
    app.run(debug=True)

