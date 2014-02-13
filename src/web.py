#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from flask import Flask, render_template, request
import mongoengine

import config
from model.exercise import Exercise
from utils import test_db
from api import rest_api

# \ ! / Monkey patching mongoengine to make json dumping easier
mongoengine.Document.to_dict = lambda s : json.loads(s.to_json())


# Initializing the web app and the database
app = Flask(__name__)
db = mongoengine.connect(config.db_name)

# Adding the REST API to our web app
app.register_blueprint(rest_api)

#Static tags
tags = ["algorithms", "trees", "sort"]

@app.route('/')
def index():
    exercises = Exercise.objects
    return render_template('index.html', exercises=exercises, tags=tags)

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
def exercise(exercise_id):
    exercise = Exercise.objects.get(id=exercise_id)
    return render_template('exercise.html', exercise=exercise)

if __name__ == "__main__":
    test_db()
    app.run(debug=True)

