
import os
import subprocess
import tempfile

class Compilation(object):

    def __init__(self, code):
        source_file = tempfile.mktemp(suffix='.cpp', prefix='elif_code_')
        self.exec_file = tempfile.mktemp(prefix='elif_exec_')

        with open(source_file, 'w') as f:
            f.write(code)

        process_arguments = ['g++', '-x', 'c++', '-o', self.exec_file, source_file]
        process = subprocess.Popen(process_arguments, stderr=subprocess.PIPE)
        process.wait()

        self.return_code = process.returncode
        self.stderr = ''

        for l in process.stderr:
            self.stderr += l

        os.remove(source_file)

    def __del__(self):
        if os.path.isfile(self.exec_file):
            os.remove(self.exec_file)

