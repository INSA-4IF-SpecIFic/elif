#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append('..')
import os
import hashlib

import mongoengine

import config

def generate_salt():
    return os.urandom(16).encode('base_64')

def hash_password(password, salt):
    return hashlib.sha512(password + salt).hexdigest()

class User(mongoengine.Document):
    email = mongoengine.StringField(primary_key=True)
    username = mongoengine.StringField(required=True)

    secret_hash = mongoengine.StringField(required=True)
    salt = mongoengine.StringField(required=True)

    editor = mongoengine.BooleanField(default=False)

    @staticmethod
    def new_user(email, username, password, editor=False):
        user = User(email=email, username=username, editor=editor)

        user.salt = generate_salt()
        user.secret_hash = hash_password(password, user.salt)

        return user

    def clean(self):
        # Emails and usernames are case insensitive
        self.username = self.username.lower()
        self.email = self.email.lower()

        if config.email_domain and not self.email.endswith('@{}'.format(config.email_domain)):
            raise mongoengine.ValidationError(dict(email="Email doesn't pass the email restriction"))

    def valid_password(self, password):
        return hash_password(password, self.salt) == self.secret_hash

if __name__ == '__main__':
    mongoengine.connect('db_test')
    User.drop_collection()

    user = User(email="ahmed.kachkach@insa-lyon.fr", username='halflings', secret_hash='IFODJI2973', salt='2')
    user.save()


    print User.objects.to_json()
