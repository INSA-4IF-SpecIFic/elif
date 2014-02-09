import json
import time

from flask import Flask, render_template, request
import mongoengine

import config
from job import ExerciseTests
from model.exercise import Exercise, Test

app = Flask(__name__)
db = mongoengine.connect(config.db_name)

def test_db():
    db = mongoengine.connect(config.db_name)
    db.drop_database(config.db_name)

    exercise = Exercise(title='Blah Bleh', description='Bleuh', boilerplate_code='b', reference_code='#')

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
    return render_template('index.html', exercises=exercises)


@app.route('/exercise/<exercise_id>')
def exercise(exercise_id):
    exercise = Exercise.objects.get(id=exercise_id)
    return render_template('exercise.html', exercise=exercise)


@app.route('/api/compile')
def compile(ws):
    code = request.json['code']
    exercise = Exercise.objects.first()

    # Saving the compilation/execution job in the database
    submission = ExerciseTests(exercise=exercise, code=code)
    submission.save()

    # Polling the database while the job hasn't been done
    while not submission.processed:
        time.sleep(0.5)
        submission.reload()

    ws.send(submission.to_json())


if __name__ == "__main__":
    test_db()
    app.run(debug=True)

