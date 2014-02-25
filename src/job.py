import datetime
import mongoengine
from model.exercise import Exercise, TestResult
from model.user import User
from compilation import Compilation

class Job(mongoengine.Document):
    date_created = mongoengine.DateTimeField(default=datetime.datetime.now)
    processed = mongoengine.BooleanField(default=False)

    meta = {'allow_inheritance': True}

    def process(self, sandbox):
        """Process execution code (to be implemented in sub classes)

        Parameters:
            - <sandbox>: the sandbox to play in
        """
        raise NotImplemented

    def __repr__(self):
        return '<{} : created at {}>'.format(self.__class__.__name__, self.date_created)

    __str__ = __repr__


class Submission(Job):
    """Abtract submission class factorising compilation and test execution"""

    exercise = mongoengine.ReferenceField(Exercise, required=True)
    code = mongoengine.StringField(required=True)
    user = mongoengine.ReferenceField(User, required=True)

    compilation_error = mongoengine.BooleanField(default=False)
    compilation_log = mongoengine.StringField(default=None)
    errors = mongoengine.ListField(mongoengine.DictField(), default=list)

    test_results = mongoengine.ListField(mongoengine.ReferenceField(TestResult), default=list)

    def test_result(self, comp, test):
        """
            Runs a <test> and starts to fill a result

            Parameters:
                - <comp>: the compiled code (Compilation object)
                - <test>: the test to execute
        """

        feedback = comp.run(stdin=str(test.input))

        result = TestResult(test=test)
        result.cpu_time = feedback.resources.ru_utime
        result.memory_used = feedback.resources.ru_ixrss + feedback.resources.ru_idrss
        result.return_code = feedback.return_code
        stdout = feedback.stdout.read()
        stderr = feedback.stdout.read()

        result.passed = True

        if not feedback.ended_correctly:
            result.passed = False
            result.report = "Process has exited unexpectedly (killed by signal {})".format(feedback.killing_signal)
        elif feedback.return_code != 0:
            result.passed = False
            result.report = "Program didn't return 0: returned {}".format(feedback.return_code)
        elif stdout != test.output:
            result.passed = False
            result.report = "Program's output didn't match expected output"

        if self.user.editor:
            print 'IS EDITOR !'
            result.stdout = stdout
            result.stderr = stderr

        result.max_cpu_time = ('max_cpu_time' in feedback.report)
        result.max_duration = ('max_duration' in feedback.report)

        return result

    def process(self, sandbox):
        """ Processes the Submission job"""

        comp = Compilation(sandbox, self.code.encode('utf-8'))

        if comp.return_code != 0:
            self.compilation_error = True
            self.compilation_log = comp.log
            self.errors = comp.errors
            return

        for test in self.exercise.tests:
            test_result = self.test_result(comp, test)

            self.test_results.append(test_result)

    def to_dict(self):
        result = super(Submission, self).to_dict()
        result['test_results'] = [test_r.to_dict() for test_r in self.test_results]
        return result

    def save(self):
        """Overloads mongoengine.Document.save()"""

        for result in self.test_results:
            result.save()

        super(Submission, self).save()
