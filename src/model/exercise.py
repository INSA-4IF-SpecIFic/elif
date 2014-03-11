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
    def score(self):
        """Compute the test score"""
        if not self.passed:
            return 0.0

        time_score = 0.0
        memory_score = 0.0

        if self.cpu_time == 0:
            time_score = 1.0
        else:
            time_score = min(float(self.test.cpu_time) / float(self.cpu_time), 1.0)

        if self.memory_used == 0:
            memory_score = 1.0
        else:
            memory_score = min(float(self.test.memory_used) / float(self.memory_used), 1.0)

        return time_score * memory_score


class Exercise(mongoengine.Document):
    author = mongoengine.ReferenceField(User, required=True)
    title = mongoengine.StringField(required=True, unique=True)
    description = mongoengine.StringField(required=True)

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

    def update_progress(self, last_submission):
        if last_submission.compilation_error:
            return

        last_results = last_submission.test_results
        last_completion = self.calculate_completion(last_results)
        last_score = self.compute_score(last_results)

        if last_completion > self.completion or (last_completion == self.completion and last_score > self.score):
            self.completion = last_completion
            self.best_results = last_results
            self.score = last_score

        # if last_score > self.score:
        #     self.completion = last_completion
        #     self.best_results = last_results
        #     self.score = last_score

        #     self.user.score = sum(exercise_p.score for exercise_p in ExerciseProgress.objects(user=self.user))
        #     self.user.save()

        #     # ScoreHistory(user=self.user, date=datetime.now(), score=self.user.score).save()

    def calculate_completion(self, results):
        if not results:
            return 0.0

        assert len(results) <= len(self.exercise.tests)

        completion = 0.0

        for r in results:
            if r.passed:
                completion += 1.0

        return completion / float(len(self.exercise.tests))

    def compute_score(self, results):
        if not results:
            return 0.0

        assert len(results) <= len(self.exercise.tests)

        score = 0.0

        for r in results:
            score += r.score

        return float(self.exercise.score) * score / float(len(self.exercise.tests))
