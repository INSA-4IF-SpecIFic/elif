import datetime
import mongoengine
import model.exercise
import model.user
import compilation
import json

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

    code = mongoengine.StringField(required=True)
    compilation_log = mongoengine.StringField(default=None)
    compilation_error = mongoengine.BooleanField(default=False)
    test_results = mongoengine.ListField(mongoengine.ReferenceField(model.exercise.TestResult), default=list)

    def process(self, sandbox):
        """Code compilation stage (Overloads Job.process())"""

        comp = compilation.Compilation(sandbox, self.code)

        if comp.return_code != 0:
            self.compilation_error = True
            self.compilation_log = comp.log
            return

        self.process_tests(comp)

    def process_tests(self, comp):
        """Tests execution stage (to be implemented in sub classes)"""
        raise NotImplemented

    def test_result(self, comp, test):
        """Runs a <test> and starts to fill a result

        Parameters:
            - <comp>: the compiled code
            - <test>: the test to execute
        """

        feedback = comp.run(stdin=str(test.input))

        result = model.exercise.TestResult(test=test)
        result.cpu_time = feedback.resources.ru_utime
        result.memory_used = feedback.resources.ru_ixrss + feedback.resources.ru_idrss
        result.return_code = feedback.return_code

        if not feedback.ended_correctly:
            result.passed = False
            result.report = "Process has exited unexpectly (killed by signal {})".format(feedback.killing_signal)

        elif feedback.return_code != 0:
            result.passed = False
            result.report = "Return code is not 0 : got {}".format(feedback.return_code)

        self.test_results.append(result)

        return result, feedback

    def to_dict(self):
        result = super(Submission, self).to_dict()
        result['test_results'] = [test_r.to_dict() for test_r in self.test_results]
        return result

    def save(self):
        """Overloads mongoengine.Document.save()"""

        for result in self.test_results:
            result.save()

        super(Submission, self).save()


class SubmissionStudent(Submission):
    """Submission to compile and execute tests on a student code"""

    exercise = mongoengine.ReferenceField(model.exercise.Exercise, required=True)

    def process_tests(self, comp):
        """Overloads Submission.process_tests()"""

        for test in self.exercise.tests:
            result, feedback = self.test_result(comp, test)

            if result.passed and feedback.stdout.read() != test.output:
                # to prevent output leaks, we don't save stdout and stderr
                result.passed = False
                result.report = "Invalid output"


class SubmissionProf(Submission):
    """Submission to let teachers tests specifics input"""

    tests = mongoengine.ListField(mongoengine.ReferenceField(model.exercise.Test), default=list)

    def process_tests(self, comp):
        """Overloads Submission.process_tests()"""

        for test in self.tests:
            result, feedback = self.test_result(comp, test)

            result.stdout = feedback.stdout.read()
            result.stderr = feedback.stdout.read()
