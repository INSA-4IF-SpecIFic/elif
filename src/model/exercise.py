#!/usr/bin/env python
# -*- coding: utf-8 -*-

import mongoengine

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

    cpu_time = mongoengine.FloatField(default=0.0)  # seconds
    memory_used = mongoengine.FloatField(default=0.0)  # kilobytes * ticks-of-execution


class Exercise(mongoengine.Document):
    title = mongoengine.StringField(required=True, unique=True)
    description = mongoengine.StringField(required=True)

    boilerplate_code = mongoengine.StringField(default=str)
    reference_code = mongoengine.StringField(required=True)

    tests = mongoengine.ListField(mongoengine.ReferenceField('Test'), required=True)

    tags = mongoengine.ListField(mongoengine.StringField())
