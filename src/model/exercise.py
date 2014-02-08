#!/usr/bin/env python
# -*- coding: utf-8 -*-

import mongoengine

class Test(mongoengine.Document):
    input = mongoengine.StringField(required=True)
    output = mongoengine.StringField(required=True)

class Exercise(mongoengine.Document):
    title = mongoengine.StringField(required=True, unique=True)
    description = mongoengine.StringField(required=True)

    boilerplate_code = mongoengine.StringField(default=str)
    reference_code = mongoengine.StringField(required=True)

    tests = mongoengine.ListField(mongoengine.ReferenceField(Test), required=True)

if __name__ == '__main__':
    mongoengine.connect('db_test')

    test = Test(input='a', output='')
    exercise = Exercise(title='Blah Bleh', description='Bleuh', boilerplate_code='b', reference_code='#', tests=[test])
