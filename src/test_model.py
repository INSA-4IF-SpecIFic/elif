import pytest
import mongoengine

import model.user
import model.exercise
import config
from greedy import Greedy
import job
import utils

# Connecting to a test db
config.db_name = 'test_db'

def test_hashing():
    password = "123LoLiLol"
    salt = model.user.generate_salt()
    hashed = model.user.hash_password(password, salt)

    assert model.user.hash_password(password, salt) == hashed
    assert model.user.hash_password(password.lower(), salt) != hashed

def test_user():
    mongoengine.connect(config.db_name)

    with pytest.raises(mongoengine.ValidationError):
        model.user.User.new_user(username="hAlflIngs", email="DiosdXSIOJDsq", password="KikOo").save()

    with pytest.raises(mongoengine.ValidationError):
        model.user.User.new_user(username="hAlflIngs", email="truc@bla{}".format(config.email_domain), password="KikOo").save()


    u = model.user.User.new_user(username="hAlflIngs", email="MonMel@{}".format(config.email_domain), password="KikOo").save()
    assert u.username == 'halflings'
    assert u.email == 'monmel@{}'.format(config.email_domain)
    assert u.valid_password('KikOo')
    assert not u.valid_password('Lolilol')
    assert not u.valid_password('kikoo')

def test_exercise_progress():

    db = mongoengine.connect(config.db_name)
    db.drop_database(config.db_name)

    # Editor user
    u = utils.sample_user()
    u.save()
    
    exe = model.exercise.Exercise(author=u, title="An exercise's title", description="## This is an exercise\n\n* El1\n* El2",
                        boilerplate_code='b', reference_code='#', tags=['sort','trees'])

    test = model.exercise.Test(input='1\n', output='1')
    test.save()
    exe.tests.append(test)

    test = model.exercise.Test(input='2\n', output='2')
    test.save()
    exe.tests.append(test)

    test = model.exercise.Test(input='3\n', output='3')
    test.save()
    exe.tests.append(test)

    exe.save()

    wrong_code = '\n'.join([
        '#include <iostream>',
        '',
        'int main() {',
        'int i;',
        'std::cin >> i;',
        'if (i > 2) std::cout << i;',
        'return 0;',
        '}'
    ])

    working_code = '\n'.join([
        '#include <iostream>',
        '',
        'int main() {',
        'int i;',
        'std::cin >> i;',
        'std::cout << i;',
        'return 0;',
        '}'
    ])

    u = model.user.User(email='test@{}'.format(config.email_domain), username='test', secret_hash='hash', salt='salt')
    u.save()

    submission = job.Submission(exercise=exe, code=wrong_code, user=u)
    submission.save()

    submission = job.Submission(exercise=exe, code=working_code, user=u)
    submission.save()

    submission = job.Submission(exercise=exe, code="nothing at all", user=u)
    submission.save()

    greedy_app = Greedy(db)
    greedy_app.fetch_and_process()

    # Progression for this user
    progress, created = model.exercise.ExerciseProgress.objects.get_or_create(user=u, exercise=exe)

    assert progress.best_results[0].passed == True
    assert progress.best_results[1].passed == True
    assert progress.best_results[2].passed == True

    assert progress.score == 42

if __name__ == '__main__':
    test_exercise_progress()