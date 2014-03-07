import os
import subprocess
import tempfile

class Compilation(object):
    """Code compilation object"""

    def __init__(self, sandbox):
        """Compiles the code"""

        self.sandbox = sandbox
        self.exec_file = None
        self.errors = None
        self.log = ''

    def __del__(self):
        if self.exec_file == None:
            return

        if os.path.isfile(self.exec_file):
            os.remove(self.exec_file)


class ClangCompilation(Compilation):
    """Code compilation object"""

    language_cmds = {
        'c': ['clang', '-x', 'c'],
        'c++': ['clang++', '-x', 'c++'],
    }

    def __init__(self, sandbox, code, language):
        """Compiles the code

        Parameters:
            - code must be encoded in UTF8
        """
        assert language in ClangCompilation.language_cmds

        Compilation.__init__(self, sandbox)

        self.source_file = tempfile.mktemp(suffix='.cpp', prefix='elif_code_')
        self.exec_file = self.sandbox.mktemp(prefix='exec_')

        with open(self.source_file, 'w') as f:
            f.write(code)

        cmd = list()
        cmd.extend(ClangCompilation.language_cmds[language])
        cmd.append('-o')
        cmd.append(self.exec_file)
        cmd.append(self.source_file)

        if self._launch_process(cmd) == 0:
            self.sandbox.clone_bin_dependencies(self.exec_file)

        else:
            self.errors = self.parse_output()

        os.remove(self.source_file)

    def _launch_process(self, cmd):
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        process.wait()

        self.return_code = process.returncode
        self.log = process.stdout.read()

        return self.return_code

    def run(self, params=list(), stdin=None):
        """Runs the code in the sandbox and return its process's feedback"""
        assert self.return_code == 0

        cmd = [self.sandbox.to_sandbox_basis(self.exec_file)]
        cmd.extend(params)

        return self.sandbox.process(cmd, stdin=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def parse_output(self):
        """Parses clang/clang++ compilation log"""

        error_lines = (line for line in self.log.split('\n')
                            if line.startswith(self.source_file) and len(line.split(':')) == 5)
        errors = list()
        for error_line in error_lines:
            line, column, type, message = map(str.strip, error_line.split(':', 4)[1:])
            errors.append(dict(row=line, column=column, type=type, message=message))

        return errors

def create(sandbox, code, language):
    assert sandbox != None
    assert isinstance(code, str)

    if language == 'c' or language == 'c++':
        return ClangCompilation(sandbox, code, language)

    assert False
