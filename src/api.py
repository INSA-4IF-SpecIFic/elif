#!/usr/bin/env python
# -*- coding: utf-8 -*-

import mongoengine

from flask import request, jsonify, Blueprint
from model.user import User
from model.exercise import Exercise
from job import Submission
import utils

rest_api = Blueprint('rest_api', __name__)

# \ ! / Monkey patching mongoengine to make json dumping easier
mongoengine.Document.to_dict = utils.to_dict

@rest_api.route('/api/user', methods=['POST'])
def create_user():
    email, username, password = request.json['email'], request.json['username'], request.json['password']
    try:
        user = User.new_user(email=email, username=username, password=password).save()
        # TODO : restrict information returned ? (security)
        return jsonify(ok=True, result=user.to_dict())
    except mongoengine.ValidationError as e:
        return jsonify(ok=False, result=e.message)

@rest_api.route('/api/submission', methods=['POST'])
def submit_code():
    code = request.json['code']
    exercise_id = request.json['exercise_id']
    exercise = Exercise.objects.get(id=exercise_id)

    # Saving the compilation/execution job in the database
    submission = Submission(exercise=exercise, code=code)
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
