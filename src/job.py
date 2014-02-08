
import datetime
import mongoengine
import model.exercise
import compilation


class Job(mongoengine.Document):
    date_created = mongoengine.DateTimeField(default=datetime.datetime.now)
    proceed = mongoengine.BooleanField(default=False)

    meta = {'allow_inheritance': True}

    def process(self, sandbox):
        pass

class ExerciseTests(Job):
    exercise = mongoengine.ReferenceField(model.exercise.Exercise, required=True)
    code = mongoengine.StringField(required=True)
    info = mongoengine.DictField(default=dict)
    log = mongoengine.StringField(default=str)


    def process(self, sandbox):
        comp = compilation.Compilation(sandbox, self.code)

        if comp.return_code != 0:
            self.log = comp.stdout
            return

        self.info['compilation'] = 'OK'

        test_id = -1

        for test in self.exercise.tests:
            test_id += 1
            test_name = 'test {}'.format(test_id)

            comp.run(stdin=str(test.input))

            succed = True

            if comp.return_code != 0:
                self.info[test_name] = 'RETURNED({})'.format(comp.return_code)

            elif comp.stdout != test.output:
                self.info[test_name] = 'FAILED'

            else:
                self.info[test_name] = 'PASSED'

