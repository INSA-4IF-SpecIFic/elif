#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import logging
import sys

import mongoengine
from model.exercise import Exercise, Test
from model.user import User

from rainbow_logging_handler import RainbowLoggingHandler

import config

log_format = '[%(asctime)s] %(levelname)s - %(message)s'
log_formatter = logging.Formatter(log_format)
logging.basicConfig(level=logging.DEBUG, format=log_format)
logging.getLogger().handlers = []

def to_dict(self):
    return json.loads(self.to_json())

def dump_exercise(exercise):
    s_json = json.loads(exercise.to_json())

    s_json['tests'] = [json.loads(test.to_json()) for test in exercise.tests]

    return s_json


def get_logger(name):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    handler = logging.FileHandler(os.path.join(config.logs_dir, '{}.log'.format(name)))
    handler.setFormatter(log_formatter)
    handler.setLevel(logging.DEBUG)

    handler2 = RainbowLoggingHandler(
            sys.stdout,
            '%Y-%m-%d %H:%M:%S',
            color_asctime=('white', None, False)
    )
    handler2.setFormatter(log_formatter)
    handler2.setLevel(logging.DEBUG)

    logger.addHandler(handler)
    logger.addHandler(handler2)

    return logger

def sample_exercise(author):
    exercise = Exercise(author=author,
                    title="#{} - New exercise".format(len(Exercise.objects)),
                    description=config.default_description,
                    boilerplate_code=config.default_boilerplate_code,
                    reference_code=config.default_boilerplate_code,
                    tags=['algorithms'])

    test = Test(input="1\n", output="42", cpu_time="100", memory_used="100").save()
    exercise.tests.append(test)
    test = Test(input="2\n", output="43", cpu_time="100", memory_used="100").save()
    exercise.tests.append(test)

    return exercise

def sample_user():
    user = User(email='dummy{}@{}'.format(len(User.objects), config.email_domain),
                username='imadummy{}'.format(len(User.objects)),
                secret_hash='hashhash',
                salt='salty',
                editor=True)

    return user

def test_db():
    """ Wipes the database and initializes it with some dummy data """
    db = mongoengine.connect(config.db_name)
    db.drop_database(config.db_name)

    # Dummy user
    User.new_user(email="dummy@{}".format(config.email_domain),
                  username="dummy_username", password="123456", editor=False).save()

    # Other dummmy users
    User.new_user(email="dummy1@{}".format(config.email_domain),
                  username="dummy_username1", password="123456", editor=False).save()

    User.new_user(email="dummy2@{}".format(config.email_domain),
                  username="dummy_username2", password="123456", editor=False).save()

    User.new_user(email="dummy3@{}".format(config.email_domain),
                  username="dummy_username3", password="123456", editor=False).save()

    # Editor user
    editor = User.new_user(email="editor@{}".format(config.email_domain),
              username="editor_user", password="123456", editor=True).save()
    # Ex 1
    test1 = Test(input='1\n', output='1').save()
    test2 = Test(input='2\n', output='4').save()

    exercise = Exercise(author=editor, title="An exercise's title", description="## This is an exercise\n\n* El1\n* El2",
                        boilerplate_code=config.default_boilerplate_code, reference_code=config.default_boilerplate_code, tags=['sort','trees'])
    exercise.tests.append(test1)
    exercise.tests.append(test2)
    exercise.save()

    # Ex 2
    params = dict(author=editor, title="Another exercise's title",
                    description="## This is an exercise\n\n* El1\n* El2\n![Alt text](/static/img/cat.jpeg)",
                    boilerplate_code=config.default_boilerplate_code, reference_code=config.default_boilerplate_code,
                    tags=['algorithms','trees'])
    exercise = Exercise(**params)
    exercise.tests.append(test1)
    exercise.tests.append(test2)
    exercise.save()

    # Ex 3
    params['title'] = "Yet another exercise"
    exercise = Exercise(**params)
    exercise.tests.append(test1)
    exercise.tests.append(test2)
    exercise.save()

    # Ex 4
    params['title'] = "And here's another exercise !"
    exercise = Exercise(**params)
    exercise.tests.append(test1)
    exercise.tests.append(test2)
    exercise.save()

    # Ex 5
    params['title'] = "And a last random exercise"
    exercise = Exercise(**params)
    exercise.tests.append(test1)
    exercise.tests.append(test2)
    exercise.save()

    # Ex 6
    exercise = Exercise(author=editor, title="Return n^2",
                    description="## Return the given number to the 2 !\n\n* You get a\n* Print a²11\n![Alt text](/static/img/cat.jpeg)",
                    boilerplate_code=config.default_boilerplate_code,
                    reference_code=config.default_boilerplate_code,
                    tags=['algorithms'])

    test = Test(input='1\n', output='1').save()
    exercise.tests.append(test)

    test = Test(input='2\n', output='4').save()
    exercise.tests.append(test)

    test = Test(input='-2\n', output='4').save()
    exercise.tests.append(test)

    exercise.save()


    return exercise
