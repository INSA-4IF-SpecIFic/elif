
import time
import mongoengine
import sandbox
import config
import job


class Greedy(object):
    """Greedy application instance polling and executing job from the database"""

    def __init__(self, db):
        self.sandbox = sandbox.Sandbox()
        self.db = db

    def fetch_and_process(self):
        count = 0

        for j in job.Job.objects(proceed=False):
            j.process(self.sandbox)
            j.proceed = True
            j.save()

            count +=1

        return count

    def run(self):
        while True:
            try:
                time.sleep(1)

            except KeyboardInterrupt:
                break

            self.fetch_and_process()

    def __del__(self):
        del self.sandbox


if __name__ == "__main__":
    db = mongoengine.connect(config.db_name)

    greedy = Greedy(db)
    greedy.run()

