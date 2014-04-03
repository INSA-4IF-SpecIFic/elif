#!/usr/bin/env python
# -*- coding: utf-8 -*-

import mongoengine

from flask import request, jsonify, Blueprint, g
from model.user import User, ScoreHistory
from model.exercise import Exercise, Test, ExerciseProgress
from job import Submission
import utils

rest_api = Blueprint('rest_api', __name__)

# \ ! / Monkey patching mongoengine to make json dumping easier
mongoengine.Document.to_dict = utils.to_dict

# Utility function for user-restricted API calls
def invalid_user(user):
    return g.user is None or user != g.user and not g.user.editor

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

@rest_api.route('/api/user/<user_pk>/progress/<exercise_id>')
def get_progress(user_pk, exercise_id):

    try:
        user = User.objects.get(pk=user_pk)
        if invalid_user(user):
            return jsonify(ok=False, result="Cannot access information from the requested user")
        exercise = Exercise.objects.get(id=exercise_id)
        progress = ExerciseProgress.objects.get(user=g.user,exercise=exercise)
        return jsonify(ok=True, result=progress.to_dict())
    except mongoengine.DoesNotExist:
        return jsonify(ok=False, result="Requested user or exercise does not exist")

@rest_api.route('/api/user/<user_pk>/score_history')
def user_progress(user_pk):
    try:
        user = User.objects.get(pk=user_pk)
    except mongoengine.DoesNotExist:
        return jsonify(ok=False, result="User doesn't exist")

    if invalid_user(user):
        return jsonify(ok=False, result="Cannot access information from the requested user")

    score_history = [sh.to_dict() for sh in ScoreHistory.objects(user=user)]

    return jsonify(ok=True, result=score_history)

# Tags

@rest_api.route('/api/tags', methods = ["GET"])
def get_tags():
    tags = set(t for e in Exercise.objects for t in e.tags)
    return jsonify(ok=True, result=tags)

@rest_api.route('/api/occurrences', methods = ["GET"])
def get_occurences():
    occurrences = []
    tags = list(set(t for e in Exercise.objects(published=True) for t in e.tags))
    for t in tags :
        occurrences.append(str(len(Exercise.objects(tags=t,published=True))))
    return jsonify(ok=True, tags=tags, occurrences=occurrences)

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
    try:
        user_id = g.user.id
    except:
        user_id = None
    found = set([e for e in exercises for w in find if w in e.title.lower() or w in e.description.lower()])
    found = [f.to_dict() for f in found if f.published or f.author.id == user_id]
    return jsonify(ok=True, result=found, user=user_id)

@rest_api.route('/api/exercise/<exercise_id>/publish', methods=['POST'])
def publish_exercise(exercise_id):
    try:
        exercise = Exercise.objects.get(id=exercise_id)
        exercise.published = True
        exercise.save()
        return jsonify(ok=True, result=utils.dump_exercise(exercise))
    except mongoengine.DoesNotExist as e:
        return jsonify(ok=False, result=e.message)

@rest_api.route('/api/exercise/<exercise_id>/unpublish', methods=['POST'])
def unpublish_exercise(exercise_id):
    try:
        exercise = Exercise.objects.get(id=exercise_id)
        exercise.published = False
        exercise.save()
        return jsonify(ok=True, result=utils.dump_exercise(exercise))
    except mongoengine.DoesNotExist as e:
        return jsonify(ok=False, result=e.message)


@rest_api.route('/api/exercise/<exercise_id>')
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

@rest_api.route('/api/exercise/<exercise_id>', methods=['POST'])
def update_exercise(exercise_id):
    exercise = None
    try:
        exercise = Exercise.objects.get(id=exercise_id)
    except mongoengine.DoesNotExist as e:
        return jsonify(ok=False, result=e.message)

    exercise.title = request.json['title']
    exercise.description = request.json['description']
    exercise.boilerplate_code = request.json['boilerplate_code']
    exercise.reference_code = request.json['reference_code']
    exercise.published = request.json['published']
    exercise.tags = map(lambda t : t.lower(), request.json['tags'].split(','))
    exercise.score = int(request.json['score'])
    exercise.save()

    # Saving the compilation/execution job in the database
    submission = Submission(exercise=exercise, user=exercise.author, code=exercise.reference_code, save_exercise=True)
    submission.save()

    return jsonify(ok=True, result=utils.dump_exercise(exercise))

@rest_api.route('/api/exercise', methods=['DELETE'])
def delete_exercise():
    exercise = None
    try:
        exercise = Exercise.objects.get(id=request.json['exercise_id'])
    except mongoengine.DoesNotExist as e:
        return jsonify(ok=False, result=e.message)

    exercise.delete_exercise()

    return jsonify(ok=True)


# Tests

@rest_api.route('/api/test/', methods=['POST'])
def new_test():
    input = request.json['input']
    output = request.json['output']
    exercise_id = request.json['exercise_id']

    exercise = None
    try:
        exercise = Exercise.objects.get(id=exercise_id)
    except mongoengine.DoesNotExist as e:
        return jsonify(ok=False, result=e.message)

    test = Test(input=input, output=output)
    test.save()
    exercise.tests.append(test)
    exercise.save()

    return jsonify(ok=True, result=utils.dump_exercise(exercise))

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

@rest_api.route('/api/submission/')
def submissions():
    # Dumping TestResult objects to JSON
    for sub in Submission.objects:
        sub.test_results = [test_r.to_dict() for test_r in sub.test_results]
    submissions = [sub.to_dict() for sub in Submission.objects()]
    return jsonify(ok=True, result=submissions)


@rest_api.route('/api/submission/<submission_id>')
def submission_state(submission_id):
    try:
        submission = Submission.objects.get(id=submission_id)
        # User's score. Added because it's helpful to follow the evolution of a user's score
        user_score = g.user.score
        return jsonify(ok=True, result=submission.to_dict(), user_score=user_score)
    except mongoengine.DoesNotExist as e:
        return jsonify(ok=False, result=e.message)