
import mongoengine
import greedy
import job
import config
import model.exercise


def test_exercice_test_job():
    config.db_name = 'test'

    db = mongoengine.connect(config.db_name)
    db.drop_database(config.db_name)

    exercise = model.exercise.Exercise(title='Blah Bleh', description='Bleuh', boilerplate_code='b', reference_code='#')

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

    submission = job.Submission(exercise=exercise, code=code)
    submission.save()

    greedy_app = greedy.Greedy(db)
    greedy_app.fetch_and_process()

    submission.reload()
    print submission.compilation_log
    for t in submission.test_results:
        print t

    assert not submission.compilation_error

    assert submission.test_results[0]['success'] == True
    assert submission.test_results[0]['return_code'] == 0
    #assert submission.test_results[0]['output'] == '1'

    assert submission.test_results[1]['success'] == False
    assert submission.test_results[1]['return_code'] == 0
    #assert submission.test_results[1]['output'] == '2'

    assert submission.test_results[2]['success'] == False
    assert submission.test_results[2]['return_code'] == 1
    #assert submission.test_results[2]['output'] == '3'

if __name__ == '__main__':
    test_exercice_test_job()

