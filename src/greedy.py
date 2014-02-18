import time
import utils
import threading
import multiprocessing
import mongoengine

import config
import sandbox
import job

# Initializing Greedy's logger
logger = utils.get_logger('greedy')

class Thread(threading.Thread):
    """Greedy thread"""

    def __init__(self, greedy):
        threading.Thread.__init__(self)

        self.sandbox = sandbox.Sandbox()
        self.dirty_sandbox = False
        self.greedy = greedy
        self.job = None

        logger.info("Creating thread {}".format(self.sandbox.root_directory))

    def __del__(self):
        logger.info("Deleting thread {}".format(self.sandbox.root_directory))
        del self.sandbox

    def get_job(self):
        self.greedy.job_queue_sem.acquire()

        self.greedy.mutex.acquire()

        if self.job:
            self.greedy.processing.remove(self.job)

        if self.greedy.quiting:
            self.job = None

        else:
            self.job = self.greedy.job_queue[0]
            self.greedy.job_queue = self.greedy.job_queue[1:]

            self.greedy.processing.append(self.job)

        self.greedy.mutex.release()

        return self.job

    def process_job(self, j):
        logger.info("Processing {}".format(j))

        j.process(self.sandbox)
        j.processed = True
        j.save()

        logger.info("{} processed !".format(j))

    def run(self):
        logger.info("Running thread {}".format(self.sandbox.root_directory))

        while True:
            j = self.get_job()

            if j == None:
                break

            self.process_job(j)

        logger.info("Stoping thread {}".format(self.sandbox.root_directory))

        return True


class Greedy(object):
    """Greedy application instance polling and executing job from the database"""

    def __init__(self, db):
        self.db = db
        self.mutex = threading.Lock()
        self.job_queue = list()
        self.job_queue_sem = threading.Semaphore(0)
        self.processing = list()
        self.quiting = False

    def fetch_and_process(self):
        s = sandbox.Sandbox()

        count = 0

        for j in job.Job.objects(processed=False):
            logger.info("Processing {}".format(j))

            j.process(s)
            j.processed = True
            j.save()

            logger.info("{} processed !".format(j))

            count += 1

        del s

        return count

    def fetch(self):
        count = 0

        query = job.Job.objects(processed=False)

        if len(query) == 0:
            return 0;

        self.mutex.acquire()

        for j in job.Job.objects(processed=False):
            if j in self.processing:
                continue

            elif j in self.job_queue:
                continue

            logger.info("Fetching {}".format(j))
            self.job_queue.append(j)
            self.job_queue_sem.release()

            count += 1

        self.mutex.release()

        return count

    def run(self):
        logger.info("Running greedy ...")

        assert len(self.processing) == 0

        threads = list()
        thread_count = multiprocessing.cpu_count()
        thread_count = 1

        for i in range(0, thread_count):
            t = Thread(self)
            t.start()
            threads.append(t)

        try:
            while True:
                time.sleep(0.01)

                self.fetch()

        except KeyboardInterrupt:
            print

        self.mutex.acquire()
        self.quiting = True
        self.mutex.release()

        for i in range(0, len(threads)):
            self.job_queue_sem.release()

        for t in threads:
            t.join()
            del t

        self.quiting = False

        assert len(self.processing) == 0

        return True


if __name__ == "__main__":
    db = mongoengine.connect(config.db_name)

    greedy = Greedy(db)
    greedy.run()

    del greedy
