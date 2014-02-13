#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from flask import Flask, render_template, request
import mongoengine

import config
from model.exercise import Exercise, Test

# Initializing the web app and the database
app = Flask(__name__)
db = mongoengine.connect(config.db_name)

# \ ! / Monkey patching mongoengine to make json dumping easier
mongoengine.Document.to_dict = lambda s : json.loads(s.to_json())


# Adding the REST API to our web app
from api import rest_api
app.register_blueprint(rest_api)

#Static tags
tags = ["algorithms", "trees", "sort"]

def test_db():
    """ Wipes the database and initializes it with some dummy data """
    db = mongoengine.connect(config.db_name)
    db.drop_database(config.db_name)

    # Ex 1
    exercise = Exercise(title="An exercise's title", description="## This is an exercise\n\n* El1\n* El2",
                        boilerplate_code='b', reference_code='#', tags=['sort','trees'])

    test = Test(input='1\n', output='1')
    test.save()
    exercise.tests.append(test)

    test = Test(input='3\n', output='2')
    test.save()
    exercise.tests.append(test)

    exercise.save()

    # Ex 2
    exercise = Exercise(title="Another exercise's title",
                    description="## This is an exercise\n\n* El1\n* El2\n![Alt text](/static/img/cat.jpeg)",
                    boilerplate_code='int main() {\n}', reference_code='int main() {    // lol   }',
                    tags=['algorithms','trees'])

    test = Test(input='1\n', output='1')
    test.save()
    exercise.tests.append(test)

    test = Test(input='3\n', output='2')
    test.save()
    exercise.tests.append(test)

    exercise.save()

    return exercise

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

