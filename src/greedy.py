import time
import utils

import mongoengine

import config
import sandbox
import job

# Initializing Greedy's logger
logger = utils.get_logger('greedy')

class Greedy(object):
    """Greedy application instance polling and executing job from the database"""

    def __init__(self, db):
        self.sandbox = sandbox.Sandbox()
        self.dirty_sandbox = False
        self.db = db

    def fetch_and_process(self):
        count = 0

        for j in job.Job.objects(processed=False):
            logger.info("Processing {}".format(j))

            j.process(self.sandbox)
            j.processed = True
            j.save()

            logger.info("{} processed !".format(j))

            count += 1

        return count

    def run(self):
        logger.info("Greedy started !")

        while True:
            try:
                time.sleep(0.01)
            except KeyboardInterrupt:
                break

            if self.fetch_and_process() == 0:
                if self.dirty_sandbox:
                    self.sandbox.recover()
                    self.dirty_sandbox = False

                    logger.info("Sandbox recovered !")

            else:
                self.dirty_sandbox = True


    def __del__(self):
        del self.sandbox


if __name__ == "__main__":
    db = mongoengine.connect(config.db_name)

    greedy = Greedy(db)
    greedy.run()

