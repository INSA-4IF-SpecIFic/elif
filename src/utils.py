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
    exercise.published = True
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

    # Dummy users
    User.new_user(email="dummy@{}".format(config.email_domain),
                  username="dummy_user", password="123456", editor=False).save()

    # Other dummmy users
    for i in xrange(8):
        User.new_user(email="dummy{}@{}".format(i + 1, config.email_domain),
                      username="dummy_user{}".format(i+1), password="123456", editor=False).save()

    # Editor user
    editor = User.new_user(email="editor@{}".format(config.email_domain),
              username="editor_user", password="123456", editor=True).save()

    # Other editor users
    for i in xrange(8):
        User.new_user(email="editor{}@{}".format(i + 1, config.email_domain),
                      username="editor_user{}".format(i+1), password="123456", editor=True).save()


    # Dummy exercises
    for i in xrange(8):
        test1 = Test(input='1\n', output='1').save()
        test2 = Test(input='2\n', output='2').save()
        test3 = Test(input='2\n', output='2').save()

        exercise = Exercise(author=editor, title="Dummy exercise {}".format(i),
                            description="## This is an exercise\n\n" +
                                        "* You get a single number as an input\n" +
                                        "* Simply return that number as an output\n",
                            boilerplate_code=config.default_boilerplate_code, reference_code=config.default_boilerplate_code, tags=['sort','trees'])

        exercise.tests = [test1, test2, test3]
        exercise.published = True
        exercise.save()

    # "Doable" exercise
    exercise = Exercise(author=editor, title="Return n²",
                    description="### Return the given number to the 2 !\n\n" +
                                "* You get a\n" +
                                "* Print a²\n" +
                                "![Alt text](/static/img/cat.jpeg)",
                    boilerplate_code=config.default_boilerplate_code,
                    reference_code=config.default_boilerplate_code,
                    tags=['algorithms'])
    test1 = Test(input='1\n', output='1').save()
    test2 = Test(input='2\n', output='4').save()
    test3 = Test(input='-2\n', output='4').save()
    exercise.tests = [test1, test2, test3]
    exercise.published = True
    exercise.save()

    # Palindrome exercise
    reference_code = """
#include <iostream>
#include <stack>
#include <sstream>
using namespace std;

struct node {
    node* next;
    int data;
    explicit node(int data):node(nullptr,data){}
    node(node* head,int data):next(head),data(data){}
};

node* insert(node* head,int data){
    return new node(head,data);
}

bool is_palindrome(node* head){
    auto temp = head;
    std::stack<node*> s;
    while(nullptr != temp){
        s.push(temp);
        temp = temp->next;
    }
    while(!s.empty()){
        if(head->data != s.top()->data){
            return false;
        }
        s.pop();
        head = head->next;
    }
    return true;
}

int main() {
    string line;
    while(getline(cin,line)){
        istringstream iss(line);
        int value;
        if(iss >> value){
            auto l = insert(nullptr,value);
            while(iss >> value){
                l = insert(l,value);
            }
            cout << is_palindrome(l) << endl;
        }
    }
    return 0;
}
    """

    boilerplate_code = """
#include <iostream>
#include <stack>
#include <sstream>
using namespace std;

struct node {
    node* next;
    int data;
    explicit node(int data):node(nullptr,data){}
    node(node* head,int data):next(head),data(data){}
};

node* insert(node* head,int data){
    return new node(head,data);
}

bool is_palindrome(node* head){
    // Your code here
}

int main() {
    string line;
    while(getline(cin,line)){
        istringstream iss(line);
        int value;
        if(iss >> value){
            auto l = insert(nullptr,value);
            while(iss >> value){
                l = insert(l,value);
            }
            cout << is_palindrome(l) << endl;
        }
    }
    return 0;
}
    """

    exercise = Exercise(author=editor, title="Palindrome",
                description="### Trouver les plaindromes !\n\n" +
                            "* Chaque ligne de l'entrée standard comprend des entiers séparés par des espaces.\n" +
                            "* Il faut transformer chaque ligne en une liste chaînée et déterminer si c'est un palindrome.\n" +
                            "* A chaque ligne de l'entrée standard doit correspondre une ligne de la sortie standard avec un 1 dans le cas d'un palindrome et un 0 sinon.\n" +

                            "![Alt text](http://onapo.files.wordpress.com/2009/04/palyndrome1.gif)",
                boilerplate_code=boilerplate_code,
                reference_code=reference_code,
                tags=['algorithms', 'strings', 'data-structures'],
                score=42)

    test1 = Test(input='lol', output='1\n').save()
    test2 = Test(input='car\nracecar', output='0\n1\n').save()
    test3 = Test(input='car\nracecar'*100, output='0\n1\n'*100).save()
    exercise.tests = [test1, test2, test3]
    exercise.published = True
    exercise.save()

    return exercise

if __name__ == '__main__':
    test_db()
