#!/usr/bin/env python
# coding=utf8

import os
import sandbox
from compilation import Compilation

def tutil_code(code, return_code):
    s = sandbox.Sandbox()
    comp = Compilation(s, code)

    assert comp.return_code == return_code

def tutil_run(code, return_code):
    s = sandbox.Sandbox()

    comp = Compilation(s, code)
    assert comp.return_code == 0

    feedback = comp.run()
    assert feedback.ended_correctly
    assert feedback.return_code == return_code

def test_basic_compilation():
    tutil_code("int main() { return 0; }\n", 0)
    tutil_code("int main() { return }\n", 1)
    tutil_code("int hello() { return 0; }\n", 1)

def test_utf8_compilation():
    code = '\n'.join([
        '#include <stdio.h>',
        'int main() {',
        'printf("héllo world\\n");',
        'return 0;',
        '}'
    ])

    tutil_code(code.decode('utf-8'), 0)

def test_executable_file():
    s = sandbox.Sandbox()
    comp = Compilation(s, "int main() { return 0; }\n")

    exec_file = comp.exec_file
    assert os.path.isfile(exec_file)
    assert os.access(exec_file, os.X_OK)

    del comp
    assert not os.path.isfile(exec_file)

def test_basic_run():
    tutil_run("int main() { return 0; }", 0)
    tutil_run("int main() { return 255; }", 255)

def test_stdout():
    code = '\n'.join([
        '#include <stdio.h>',
        'int main() {',
        'printf("hello world\\n");',
        'return 0;',
        '}'
    ])

    s = sandbox.Sandbox()
    comp = Compilation(s, code)
    assert comp.return_code == 0

    feedback = comp.run()
    assert feedback.ended_correctly
    assert feedback.return_code == 0
    assert feedback.stdout.read() == "hello world\n"


if __name__ == "__main__":
    test_basic_compilation()
    test_executable_file()
    test_basic_run()
    test_stdout()

