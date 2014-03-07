import datetime
import mongoengine
from model.exercise import Exercise, TestResult, ExerciseProgress
from model.user import User
import compilation

class Job(mongoengine.Document):
    date_created = mongoengine.DateTimeField(default=datetime.datetime.now)
    processed = mongoengine.BooleanField(default=False)

    meta = {'allow_inheritance': True}

    def process(self, sandbox, logger):
        """Process execution code (to be implemented in sub classes)

        Parameters:
            - <sandbox>: the sandbox to play in
            - <logger>: the logger I should use to display messages.
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

    def test_result(self, comp, test, logger):
        """
            Runs a <test> and starts to fill a result

            Parameters:
                - <comp>: the compiled code (Compilation object)
                - <test>: the test to execute
                - <logger>: the logger I should use to report issues
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
            #print 'IS EDITOR !'
            result.stdout = stdout
            result.stderr = stderr

        result.max_cpu_time = ('max_cpu_time' in feedback.report)
        result.max_duration = ('max_duration' in feedback.report)

        if result.max_cpu_time:
            logger.warn("Process of <{}> exceeded the max CPU time".format(self.user.username))

        if result.max_duration:
            logger.warn("Process of <{}> exceeded the max duration".format(self.user.username))

        if not feedback.ended_correctly:
            logger.warn("Process of <{}> was killed by signal {}".format(self.user.username, feedback.killing_signal))

        return result

    def process(self, sandbox, logger):
        """ Processes the Submission job"""

        logger.info("Processing exercise submitted by <{}>".format(self.user.username))
        comp = compilation.create(sandbox, self.code.encode('utf-8'), 'c++')

        if comp.return_code != 0:
            self.compilation_error = True
            self.compilation_log = comp.log
            self.errors = comp.errors
            return

        for test in self.exercise.tests:
            test_result = self.test_result(comp, test, logger)
            test_result.save()
            self.test_results.append(test_result)

        # Updating best performance
        progress,_ = ExerciseProgress.objects.get_or_create(user=self.user, exercise=self.exercise)
        progress.update_progress(self)
        progress.save()

    def to_dict(self):
        result = super(Submission, self).to_dict()
        result['test_results'] = [test_r.to_dict() for test_r in self.test_results]
        return result
