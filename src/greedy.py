import time
import logging
import os

import mongoengine

import config
import sandbox
import job

# Initializing Greedy's logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
handler = logging.FileHandler(os.path.join(config.logs_dir, 'greedy.log'))
handler.setLevel(logging.INFO)
logger.addHandler(handler)

class Greedy(object):
    """Greedy application instance polling and executing job from the database"""

    def __init__(self, db):
        self.sandbox = sandbox.Sandbox()
        self.db = db

    def fetch_and_process(self):
        count = 0

        for j in job.Job.objects(processed=False):
            logger.info("Processing job #{}".format(count))

            j.process(self.sandbox)
            j.processed = True
            j.save()

            count += 1

        return count

    def run(self):
        logger.info("Greedy started !")
        while True:
            try:
                time.sleep(0.2)
            except KeyboardInterrupt:
                break

            self.fetch_and_process()

    def __del__(self):
        del self.sandbox


if __name__ == "__main__":
    db = mongoengine.connect(config.db_name)

    greedy = Greedy(db)
    greedy.run()

