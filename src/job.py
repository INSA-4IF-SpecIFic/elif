import datetime
import mongoengine
import model.exercise
import compilation


class Job(mongoengine.Document):
    date_created = mongoengine.DateTimeField(default=datetime.datetime.now)
    processed = mongoengine.BooleanField(default=False)

    meta = {'allow_inheritance': True}

    def process(self, sandbox):
        pass

class Submission(Job):
    exercise = mongoengine.ReferenceField(model.exercise.Exercise, required=True)
    code = mongoengine.StringField(required=True)
    compilation_log = mongoengine.StringField(default=None)
    compilation_error = mongoengine.BooleanField(default=False)
    test_results = mongoengine.ListField(default=list)

    @property
    def compilation_successful(self):
        return self.processed and self.compilation_log == None

    def process(self, sandbox):
        comp = compilation.Compilation(sandbox, self.code)

        if comp.return_code != 0:
            self.compilation_error = True
            self.compilation_log = comp.stderr
            return

        for test in self.exercise.tests:
            comp.run(stdin=str(test.input))

            status = 'PASSED'

            if comp.return_code != 0:
                status = 'RETURNED({})'.format(comp.return_code)

            elif comp.stdout != test.output:
                status = 'FAILED'

            self.test_results.append(status)

