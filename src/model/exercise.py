#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime

import mongoengine

from user import User, ScoreHistory

class Test(mongoengine.Document):
    input = mongoengine.StringField(required=True)
    output = mongoengine.StringField(required=True)
    cpu_time = mongoengine.FloatField(default=0.0)  # seconds
    memory_used = mongoengine.FloatField(default=0.0)  # kilobytes * ticks-of-execution


class TestResult(mongoengine.Document):
    test = mongoengine.ReferenceField(Test, required=True, reverse_delete_rule=mongoengine.CASCADE)
    stdout = mongoengine.StringField(default=str)
    stderr = mongoengine.StringField(default=str)
    passed = mongoengine.BooleanField(default=True)
    return_code = mongoengine.IntField(default=0)
    report = mongoengine.StringField(default=str)
    max_cpu_time = mongoengine.BooleanField(default=False)
    max_duration = mongoengine.BooleanField(default=False)

    cpu_time = mongoengine.FloatField(default=0.0)  # seconds
    memory_used = mongoengine.FloatField(default=0.0)  # kilobytes * ticks-of-execution

    @property
    def ratio(self):
        """
            Compute's the result's 'ratio'.
            Ex: 0.75 means the user should get 75% of the test's score
        """
        if not self.passed:
            return 0.0

        time_score = 0.0
        memory_score = 0.0

        if self.cpu_time == 0 or self.test.cpu_time == 0:
            time_score = 1.0
        else:
            time_score = min(float(self.test.cpu_time) / float(self.cpu_time), 1.0)

        if self.memory_used == 0:
            memory_score = 1.0
        else:
            memory_score = min(float(self.test.memory_used) / float(self.memory_used), 1.0)

        return time_score * memory_score


class Exercise(mongoengine.Document):
    title = mongoengine.StringField(required=True, unique=True)
    description = mongoengine.StringField(required=True)
    author = mongoengine.ReferenceField(User, required=True)

    boilerplate_code = mongoengine.StringField(default=str)
    reference_code = mongoengine.StringField(required=True)
    code_language = mongoengine.StringField(required=True, default='c++')

    tests = mongoengine.ListField(mongoengine.ReferenceField(Test, reverse_delete_rule=mongoengine.NULLIFY), required=True)

    tags = mongoengine.ListField(mongoengine.StringField())
    score = mongoengine.IntField(default=42)

    published = mongoengine.BooleanField(default=False);

    def __hash__(self):
        return hash(self.title)

    def delete_exercise(self):
        for t in self.tests:
            t.delete()
        self.delete()

class ExerciseProgress(mongoengine.Document):
    user = mongoengine.ReferenceField(User, required=True)
    exercise = mongoengine.ReferenceField(Exercise, required=True, reverse_delete_rule=mongoengine.CASCADE)

    best_results = mongoengine.ListField(mongoengine.ReferenceField(TestResult), default=list)
    score = mongoengine.IntField(default=0)
    completion = mongoengine.FloatField(default=0.0)

    def update_progress(self, new_submission):
        if new_submission.compilation_error:
            return

        new_results = new_submission.test_results
        new_completion = self.calculate_completion(new_results)
        new_score = self.compute_score(new_results)

        if new_score > self.score:
            self.completion = new_completion
            self.best_results = new_results
            self.score = new_score
            # Saving the current progress so it's taken into account when calculating the user's score
            self.save()

            self.user.score = sum(exercise_p.score for exercise_p in ExerciseProgress.objects(user=self.user))
            self.user.save()

            ScoreHistory(user=self.user, date=datetime.now(), score=self.user.score).save()

    def calculate_completion(self, results):
        passed_results = [r for r in results if r.passed]

        if passed_results:
            return float(len(passed_results)) / len(self.exercise.tests)
        else:
            return 0.0

    def compute_score(self, results):
        score_ratio = float(self.exercise.score) / len(self.exercise.tests)
        return sum(r.ratio * score_ratio for r in results)