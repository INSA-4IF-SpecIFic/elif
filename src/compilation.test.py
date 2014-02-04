
import os
from compilation import Compilation

def test_code(code, return_code):
    comp = Compilation(code)

    assert comp.return_code == return_code

def test_run(code, return_code):
    comp = Compilation(code)
    assert comp.return_code == 0

    comp.run()
    assert comp.return_code == return_code

def test_basic_compilation():
    test_code("int main() { return 0; }\n", 0)
    test_code("int main() { return }\n", 1)
    test_code("int hello() { return 0; }\n", 1)

def test_executable_file():
    comp = Compilation("int main() { return 0; }\n")

    exec_file = comp.exec_file
    assert os.path.isfile(exec_file)

    del comp
    assert not os.path.isfile(exec_file)

def test_basic_run():
    test_run("int main() { return 0; }", 0)
    test_run("int main() { return 255; }", 255)

def test_stdout():
    code = '\n'.join([
        '#include <stdio.h>',
        'int main() {',
        'printf("hello world\\n");',
        'return 0;',
        '}'
    ])

    comp = Compilation(code)
    assert comp.return_code == 0

    comp.run()
    assert comp.return_code == 0

    assert comp.stdout == "hello world\n"


if __name__ == "__main__":
    test_basic_compilation()
    test_executable_file()
    test_basic_run()
    test_stdout()

