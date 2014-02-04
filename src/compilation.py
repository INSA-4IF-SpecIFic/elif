
import subprocess
import tempfile

class Compilation(object):

    def __init__(self, code):
        self.source_file = tempfile.mktemp(suffix='.cpp', prefix='elif_code_')
        self.dest_file = tempfile.mktemp(prefix='elif_exec_')

        with open(self.source_file, 'w') as f:
            f.write(code)

        process_arguments = ['g++', '-x', 'c++', '-o', self.dest_file, self.source_file]
        process = subprocess.Popen(process_arguments, stderr=subprocess.PIPE)
        process.wait()

        self.return_code = process.returncode
        self.stderr = ''

        for l in process.stderr:
            self.stderr += l

        print self.stderr


if __name__ == "__main__":
    code = "int main() { return a; }\n"

    comp = Compilation(code)

