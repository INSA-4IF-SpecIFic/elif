#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append('..')
import os
import hashlib
import re

import mongoengine
from datetime import datetime

import config

def generate_salt():
    return os.urandom(16).encode('base_64')

def hash_password(password, salt):
    return hashlib.sha512(salt + password).hexdigest()

class User(mongoengine.Document):
    email = mongoengine.StringField(primary_key=True)
    username = mongoengine.StringField(required=True, unique=True)

    secret_hash = mongoengine.StringField(required=True)
    salt = mongoengine.StringField(required=True)

    score = mongoengine.IntField(default=0)

    editor = mongoengine.BooleanField(default=False)

    def __hash__(self):
        return hash(self.email)

    @staticmethod
    def new_user(email, username, password, editor=False):
        user = User(email=email, username=username, editor=editor)

        user.salt = generate_salt()
        user.secret_hash = hash_password(password, user.salt)

        # Initializing the user's score history
        ScoreHistory(user=user, date=datetime.now(), score=0).save()

        return user

    def clean(self):
        # Emails and usernames are case insensitive
        self.username = self.username.lower()
        self.email = self.email.lower()

        reg = "^[a-z0-9_]+$"
        if not re.match(reg, self.username):
            raise mongoengine.ValidationError(dict(username="Username doesn't pass the username restriction"))
        if len(self.username) > config.length_limit:
            raise mongoengine.ValidationError(dict(username="Username is too long (maximum length: {})".format(config.length_limit)))
        if len(self.email) > config.length_limit:
            raise mongoengine.ValidationError(dict(email="Email is too long (maximum length: {})".format(config.length_limit)))

        if config.email_domain and not self.email.endswith('@{}'.format(config.email_domain)):
            raise mongoengine.ValidationError(dict(email="Email doesn't pass the email restriction"))

    def valid_password(self, password):
        return hash_password(password, self.salt) == self.secret_hash


class ScoreHistory(mongoengine.Document):
    user = mongoengine.ReferenceField(User, required=True)
    date = mongoengine.DateTimeField(default=datetime.now())
    score = mongoengine.IntField(required=True)


if __name__ == '__main__':
    mongoengine.connect('db_test')
    User.drop_collection()

    user = User(email="ahmed.kachkach@insa-lyon.fr", username='halflings', secret_hash='IFODJI2973', salt='2')
    user.save()


    print User.objects.to_json()
