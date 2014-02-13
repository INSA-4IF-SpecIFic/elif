#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mongoengine import *

class Test(Document):
    input = StringField(required=True)
    output = StringField(required=True)

class Exercise(Document):
    title = StringField(required=True, unique=True)
    description = StringField(required=True)

    boilerplate_code = StringField(default=str)
    reference_code = StringField(required=True)

    tests = ListField(ReferenceField('Test'), required=True)

    tags = ListField(StringField())

if __name__ == '__main__':
    db = connect('db_test')
    db.drop_database('db_test')
    test = Test(input='a', output='')
    test.save()
    exercise = Exercise(title='Blah Bleh', description='Bleuh', boilerplate_code='b', reference_code='#', tests=[test])
    exercise.save()

    exercise.tags.append('sort')
    exercise.save()
