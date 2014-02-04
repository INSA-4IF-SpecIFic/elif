
import subprocess
import tempfile

class Compilation(object):

    def __init__(self, code):
        self.source_file = tempfile.mktemp(suffix='.cpp', prefix='elif_code_')
        self.dest_file = tempfile.mktemp(prefix='elif_exec_')

        with open(self.source_file, 'w') as f:
            f.write(code)

        process_arguments = ['g++', '-x', 'c++', '-o', self.dest_file, self.source_file]

        self.process = subprocess.Popen(process_arguments) #, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.process.wait()

    @property
    def return_code(self):
        return self.process.returncode

if __name__ == "__main__":
    code = "int main() { return 0; }\n"

    comp = Compilation(code)

    print comp.return_code

