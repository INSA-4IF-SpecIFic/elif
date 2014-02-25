import mongoengine

import config
import greedy
import job
import model.exercise
import model.user
import utils

def test_exercice_test_job():
    config.db_name = 'test'

    db = mongoengine.connect(config.db_name)
    db.drop_database(config.db_name)

    user = utils.sample_user()
    user.save()

    exercise = model.exercise.Exercise(author=user, title='Blah Bleh', description='Bleuh', boilerplate_code='b', reference_code='#')

    test = model.exercise.Test(input='1\n', output='1')
    test.save()
    exercise.tests.append(test)

    test = model.exercise.Test(input='2\n', output='1')
    test.save()
    exercise.tests.append(test)

    test = model.exercise.Test(input='3\n', output='2')
    test.save()
    exercise.tests.append(test)

    exercise.save()


    code = '\n'.join([
        '#include <iostream>',
        '',
        'int main() {',
        'int i;',
        'std::cin >> i;',
        'std::cout << i;',
        'if (i > 2) return 1;',
        'return 0;',
        '}'
    ])

    user = model.user.User(email='test@{}'.format(config.email_domain), username='test', secret_hash='hash', salt='salt')
    user.save()

    submission = job.Submission(exercise=exercise, code=code, user=user)
    submission.save()

    greedy_app = greedy.Greedy(db)
    greedy_app.fetch_and_process()

    submission.reload()

    assert not submission.compilation_error

    assert submission.test_results[0].passed == True
    assert submission.test_results[0].return_code == 0
    # assert not submission.test_results[0].stdout
    # assert not submission.test_results[0].stderr

    assert submission.test_results[1].passed == False
    assert submission.test_results[1].return_code == 0
    # assert not submission.test_results[1].stdout
    # assert not submission.test_results[1].stderr

    assert submission.test_results[2].passed == False
    assert submission.test_results[2].return_code == 1
    # assert not submission.test_results[2].stdout
    # assert not submission.test_results[2].stderr

    # submission = job.SubmissionProf(tests=[exercise.tests[0], exercise.tests[2]], code=code)
    # submission.save()

    # greedy_app.fetch_and_process()

    # submission.reload()

    # assert not submission.compilation_error

    # assert submission.test_results[0].passed == True
    # assert submission.test_results[0].return_code == 0
    # assert submission.test_results[0].stdout == '1'

    # assert submission.test_results[1].passed == False
    # assert submission.test_results[1].return_code == 1
    # assert submission.test_results[1].stdout == '3'


if __name__ == '__main__':
    test_exercice_test_job()

