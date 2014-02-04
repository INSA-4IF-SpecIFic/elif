
import os
import subprocess
import tempfile

class Compilation(object):

    def __init__(self, code, compilor_cmd='g++'):
        source_file = tempfile.mktemp(suffix='.cpp', prefix='elif_code_')
        self.exec_file = tempfile.mktemp(prefix='elif_exec_')

        with open(source_file, 'w') as f:
            f.write(code)

        self._launch_process([compilor_cmd, '-x', 'c++', '-o', self.exec_file, source_file])

        os.remove(source_file)

    def __del__(self):
        if os.path.isfile(self.exec_file):
            os.remove(self.exec_file)

    def _launch_process(self, cmd):
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()

        self.return_code = process.returncode

        self.stdout = ''
        for l in process.stdout:
            self.stdout += l

        self.stderr = ''
        for l in process.stderr:
            self.stderr += l

        return self.return_code

    def run(self, params=list()):
        assert self.return_code == 0

        run_cmd = [self.exec_file]
        run_cmd.extend(params)

        return self._launch_process(run_cmd)

