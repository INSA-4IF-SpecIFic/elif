#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append('..')

import mongoengine

import config

class User(mongoengine.Document):
    email = mongoengine.StringField(primary_key=True)
    username = mongoengine.StringField(required=True)
    secret_hash = mongoengine.StringField(required=True)

    editor = mongoengine.BooleanField(default=False)

    def clean(self):
        if config.email_restricted_domain and not self.email.endswith('@{}'.format(config.email_restricted_domain)):
            raise mongoengine.ValidationError(dict(email="Email doesn't pass the email restriction"))

if __name__ == '__main__':
    mongoengine.connect('db_test')

    user = User(email="ahmed.kachkach@insa-lyon.fr", username='halflings', secret_hash='IFODJI2973')
    user.save()

    print User.objects.to_json()
