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

    def __repr__(self):
        return '<{} : created at {}>'.format(self.__class__.__name__, self.date_created)

    __str__ = __repr__

class Submission(Job):
    exercise = mongoengine.ReferenceField(model.exercise.Exercise, required=True)
    code = mongoengine.StringField(required=True)
    compilation_log = mongoengine.StringField(default=None)
    compilation_error = mongoengine.BooleanField(default=False)
    test_results = mongoengine.ListField(default=list)

    def process(self, sandbox):
        comp = compilation.Compilation(sandbox, self.code)

        if comp.return_code != 0:
            self.compilation_error = True
            self.compilation_log = comp.log
            return

        for i, test in enumerate(self.exercise.tests):
            feedback = comp.run(stdin=str(test.input))

            status = { }

            status['index'] = i
            status['success'] = True
            status['return_code'] = feedback.return_code
            status['reason'] = str()
            status['cpu_time'] = feedback.resources.ru_utime
            status['memory_used'] = feedback.resources.ru_ixrss + feedback.resources.ru_idrss
            #status['test_id'] = test.id

            if not feedback.ended_correctly:
                status['success'] = False
                status['reason'] = "Process has exited unexpectly (killed by signal {})".format(feedback.killing_signal)

            elif feedback.return_code != 0:
                status['success'] = False
                status['reason'] = "Return code is not 0 : got {}".format(feedback.return_code)

            elif feedback.stdout.read() != test.output:
                status['success'] = False
                status['reason'] = "Invalid output"

            self.test_results.append(status)
