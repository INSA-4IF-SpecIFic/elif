import os
import subprocess
import tempfile
from collections import namedtuple

ErrorStruct = namedtuple('ErrorStruct', 'line column type message')

class Compilation(object):

    def __init__(self, sandbox, code, compiler_cmd='clang'):
        self.sandbox = sandbox

        self.source_file = tempfile.mktemp(suffix='.cpp', prefix='elif_code_')
        self.exec_file = self.sandbox.mktemp(prefix='exec_')

        with open(self.source_file, 'w') as f:
            f.write(code)

        self.errors = None
        if self._launch_process([compiler_cmd, '-x', 'c++', '-o', self.exec_file, self.source_file]) == 0:
            self.sandbox.clone_bin_dependencies(self.exec_file)
        else:
            self.errors = self.parse_output()

        os.remove(self.source_file)

    def __del__(self):
        if os.path.isfile(self.exec_file):
            os.remove(self.exec_file)

    def _launch_process(self, cmd):
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()

        self.return_code = process.returncode
        self.stdout = process.stdout.read()
        self.stderr = process.stderr.read()

        return self.return_code

    def run(self, params=list(), stdin=None):
        assert self.return_code == 0

        cmd = [self.sandbox.to_sandbox_basis(self.exec_file)]
        cmd.extend(params)

        process = self.sandbox.process(cmd, stdin=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.return_code = process.returncode
        self.stdout = process.stdout.read()
        self.stderr = process.stderr.read()

        return process.returncode

    def parse_output(self):
        error_lines = (line for line in self.stderr.split('\n') if line.startswith(self.source_file) and len(line.split(':')) == 5)
        return [ErrorStruct(*map(str.strip, error_line.split(':', 4)[1:])) for error_line in error_lines]
