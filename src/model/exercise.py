#!/usr/bin/env python
# -*- coding: utf-8 -*-
import mongoengine
from user import User

class Test(mongoengine.Document):
    input = mongoengine.StringField(required=True)
    output = mongoengine.StringField(required=True)
    cpu_time = mongoengine.FloatField(default=0.0)  # seconds
    memory_used = mongoengine.FloatField(default=0.0)  # kilobytes * ticks-of-execution


class TestResult(mongoengine.Document):
    test = mongoengine.ReferenceField(Test, required=True)
    stdout = mongoengine.StringField(default=str)
    stderr = mongoengine.StringField(default=str)
    passed = mongoengine.BooleanField(default=True)
    return_code = mongoengine.IntField(default=0)
    report = mongoengine.StringField(default=str)
    max_cpu_time = mongoengine.BooleanField(default=False)
    max_duration = mongoengine.BooleanField(default=False)

    cpu_time = mongoengine.FloatField(default=0.0)  # seconds
    memory_used = mongoengine.FloatField(default=0.0)  # kilobytes * ticks-of-execution


class Exercise(mongoengine.Document):
    author = mongoengine.ReferenceField(User, required=True)
    title = mongoengine.StringField(required=True, unique=True)
    description = mongoengine.StringField(required=True)

    boilerplate_code = mongoengine.StringField(default=str)
    reference_code = mongoengine.StringField(required=True)

    tests = mongoengine.ListField(mongoengine.ReferenceField(Test), default=list)

    tags = mongoengine.ListField(mongoengine.StringField())
    score = mongoengine.IntField(default=42)

    def __hash__(self):
        return hash(self.title)

class ExerciseProgress(mongoengine.Document):
    user = mongoengine.ReferenceField(User, required=True)
    exercise = mongoengine.ReferenceField(Exercise, required=True)

    best_results = mongoengine.ListField(mongoengine.ReferenceField(TestResult), default=list)
    score = mongoengine.IntField(default=0)
    completion = mongoengine.FloatField(default=0.0)

    def update_progress(self, last_submission):
        if last_submission.compilation_error:
            return

        last_results = last_submission.test_results
        last_completion = self.calculate_completion(last_results)
        if self.completion < last_completion:
            self.completion = last_completion
            self.score = last_completion * self.exercise.score
            self.best_results = last_results

    def calculate_completion(self, results):
        return  len([t for t in results if t.passed]) / float(len(results))
