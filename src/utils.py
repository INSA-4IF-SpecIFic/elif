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

def sample_exercise():
    exercise = Exercise(title="#{} - Sample exercise".format(len(Exercise.objects)),
                    description="## Just double the freaking number !\n\n* You get a\n* Print a x 2\n![Alt text](/static/img/cat.jpeg)",
                    boilerplate_code='#include <iostream>\nint main() {\n  int a;\n  std::cin >> a;\n  return 0;\n}',
                    reference_code='int main() {}',
                    tags=['algorithms'])
    test = Test(input="1\n", output="42", cpu_time="100", memory_used="100").save()
    exercise.tests.append(test)
    test = Test(input="2\n", output="43", cpu_time="100", memory_used="100").save()
    exercise.tests.append(test)
    return exercise


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
    exercise = Exercise(title="Return n*2",
                    description="## Just double the freaking number !\n\n* You get a\n* Print a x 2\n![Alt text](/static/img/cat.jpeg)",
                    boilerplate_code='#include <iostream>\nint main() {\n  int a;\n  std::cin >> a;\n}',
                    reference_code='int main() {}',
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
                  username="dummy_username", password="123456", editor=False).save()

    # Editor user
    User.new_user(email="editor@{}".format(config.email_domain),
              username="editor_user", password="123456", editor=True).save()
    return exercise
