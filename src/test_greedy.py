
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

    exercise_test = job.ExerciseTests(exercise=exercise, code=code)
    exercise_test.save()

    greedy_app = greedy.Greedy(db)
    greedy_app.fetch_and_process()

    exercise_test.reload()
    assert exercise_test.info['compilation'] == 'OK'
    assert exercise_test.info['test 0'] == 'PASSED'
    assert exercise_test.info['test 1'] == 'FAILED'
    assert exercise_test.info['test 2'] == 'RETURNED(1)'

if __name__ == '__main__':
    test_exercice_test_job()

