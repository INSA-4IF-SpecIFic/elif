#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging

import mongoengine
from model.exercise import Exercise, Test
from model.user import User

import config


log_format = '%(asctime)s :: %(levelname)s - %(message)s'
log_formatter = logging.Formatter(log_format)
logging.basicConfig(level=logging.DEBUG, format=log_format)

def get_logger(name):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(os.path.join(config.logs_dir, '{}.log'.format(name)))
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    handler.setFormatter(log_formatter)

    return logger



def test_db():
    """ Wipes the database and initializes it with some dummy data """
    db = mongoengine.connect(config.db_name)
    db.drop_database(config.db_name)

    # Ex 1
    exercise = Exercise(title="An exercise's title", description="## This is an exercise\n\n* El1\n* El2",
                        boilerplate_code='b', reference_code='#', tags=['sort','trees'])

    test = Test(input='1\n', output='1').save()
    exercise.tests.append(test)

    test = Test(input='3\n', output='2').save()
    exercise.tests.append(test)

    exercise.save()

    # Ex 2
    exercise = Exercise(title="Another exercise's title",
                    description="## This is an exercise\n\n* El1\n* El2\n![Alt text](/static/img/cat.jpeg)",
                    boilerplate_code='int main() {\n}', reference_code='int main() {    // lol   }',
                    tags=['algorithms','trees'])

    test = Test(input='1\n', output='1').save()
    exercise.tests.append(test)

    test = Test(input='3\n', output='2').save()
    exercise.tests.append(test)

    exercise.save()


    # Ex 3
    exercise = Exercise(title="Double the given number",
                    description="## Just double the freaking number !\n\n* You get a\n* Print a x 2\n![Alt text](/static/img/cat.jpeg)",
                    boilerplate_code='#include <iostream>\nint main() {\n}', reference_code='int main() {    // lol   }',
                    tags=['algorithms'])

    test = Test(input='1\n', output='1').save()
    exercise.tests.append(test)

    test = Test(input='2\n', output='4').save()
    exercise.tests.append(test)

    test = Test(input='-2\n', output='4').save()
    exercise.tests.append(test)

    exercise.save()

    # Dummy user
    User.new_user(email="dummy@{}".format(config.email_domain),
                  username="dummy_username", password="123456", editor=True).save()

    return exercise
