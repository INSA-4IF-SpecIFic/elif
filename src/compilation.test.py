
from compilation import Compilation

def test_code(code, return_code):
    comp = Compilation(code)

    assert return_code == comp.return_code

def test_basic_compilation():
    test_code("int main() { return 0; }\n", 0)
    test_code("int main() { return }\n", 1)
    test_code("int hello() { return 0; }\n", 1)

if __name__ == "__main__":
    test_basic_compilation()

