#!/usr/bin/env python
# -*- coding: utf-8 -*-

import mongoengine

from flask import request, session, jsonify, Blueprint, g
from model.user import User
from model.exercise import Exercise, Test
from job import Submission
import utils

rest_api = Blueprint('rest_api', __name__)

# \ ! / Monkey patching mongoengine to make json dumping easier
mongoengine.Document.to_dict = utils.to_dict

@rest_api.before_request
def load_user():
    """ Injects the current logged in user (if any) to the request context """
    g.user = User.objects(email=session.get('logged_in')).first()

# Users

@rest_api.route('/api/user', methods=['POST'])
def create_user():
    email, username, password = request.json['email'], request.json['username'], request.json['password']
    try:
        user = User.new_user(email=email, username=username, password=password).save()
        # TODO : restrict information returned ? (security)
        return jsonify(ok=True, result=user.to_dict())
    except mongoengine.ValidationError as e:
        return jsonify(ok=False, result=e.message)

# Exercises

@rest_api.route('/api/exercise/search', methods=['POST'])
def search_words():
    words = request.json['words']
    tags = request.json['tags'].split()
    words = words.lower()
    find = [words] + words.split()
    if tags == [] :
        exercises = Exercise.objects
    else :
        exercises = Exercise.objects(tags__in=tags)
    found = list(set([e for e in exercises for w in find if w in e.title.lower() or w in e.description.lower()]))
    found = [f.to_dict() for f in found]
    return jsonify(ok=True, result=found)

@rest_api.route('/api/exercise/<exercise_id>', methods=['GET'])
def exercise(exercise_id):
    exercise = None
    try:
        exercise = Exercise.objects.get(id=exercise_id)
    except mongoengine.DoesNotExist as e:
        return jsonify(ok=False, result=e.message)

    if request.method == 'GET':
        return jsonify(ok=True, result=utils.dump_exercise(exercise))
    #elif request.method == 'DELETE':
        #pass

# Tests
@rest_api.route('/api/test/<test_id>', methods=['DELETE'])
def test(test_id):
    test = None
    try:
        test = Test.objects.get(id=test_id)
    except mongoengine.DoesNotExist as e:
        return jsonify(ok=False, result=e.message)

    if request.method == 'DELETE':
        exercise = None
        try:
            exercise = Exercise.objects.get(id=request.json['exercise_id'])
        except mongoengine.DoesNotExist as e:
            return jsonify(ok=False, result=e.message)

        exercise.tests.remove(test)
        exercise.save()

        test.delete()

        return jsonify(ok=True, result=utils.dump_exercise(exercise))

# Submissions

@rest_api.route('/api/submission', methods=['POST'])
def submit_code():
    code = request.json['code']
    exercise_id = request.json['exercise_id']
    exercise = Exercise.objects.get(id=exercise_id)
    user = g.user

    # Saving the compilation/execution job in the database
    submission = Submission(exercise=exercise, user=user, code=code)
    submission.save()

    return jsonify(ok=True, result=submission.to_dict())

@rest_api.route('/api/submission/', methods=['GET'])
def submissions():
    # Dumping TestResult objects to JSON
    for sub in Submission.objects:
        sub.test_results = [test_r.to_dict() for test_r in sub.test_results]
    submissions = [sub.to_dict() for sub in Submission.objects()]
    return jsonify(ok=True, result=submissions)


@rest_api.route('/api/submission/<submission_id>', methods=['GET'])
def submission_state(submission_id):
    try:
        submission = Submission.objects.get(id=submission_id)
        return jsonify(ok=True, result=submission.to_dict())
    except mongoengine.DoesNotExist as e:
        return jsonify(ok=False, result=e.message)
