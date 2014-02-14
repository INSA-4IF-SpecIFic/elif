import sys
sys.path.append('..')

import pytest
import mongoengine

from user import User, generate_salt, hash_password
import config

# Connecting to a test db
config.db_name = 'test_db'

def test_hashing():
    password = "123LoLiLol"
    salt = generate_salt()
    hashed = hash_password(password, salt)

    assert hash_password(password, salt) == hashed
    assert hash_password(password.lower(), salt) != hashed

def test_user():
    mongoengine.connect(config.db_name)

    with pytest.raises(mongoengine.ValidationError):
        User.new_user(username="hAlflIngs", email="DiosdXSIOJDsq", password="KikOo").save()

    with pytest.raises(mongoengine.ValidationError):
        User.new_user(username="hAlflIngs", email="truc@bla{}".format(config.email_domain), password="KikOo").save()


    user = User.new_user(username="hAlflIngs", email="MonMel@{}".format(config.email_domain), password="KikOo").save()
    assert user.username == 'halflings'
    assert user.email == 'monmel@{}'.format(config.email_domain)
    assert user.valid_password('KikOo')
    assert not user.valid_password('Lolilol')
    assert not user.valid_password('kikoo')
