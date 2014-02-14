#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mongoengine import Document, StringField, ListField, ReferenceField

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
