
import subprocess
import sandbox


def test_python_env():
    s = sandbox.Sandbox()

    print 'sandbox size: {} bytes'.format(s.size())

    s.add_running_env(sandbox.python_env)

    source_file = s.to_sandbox_basis(s.mktemp(prefix='code_', suffix='.py'))

    with s.open(source_file, 'w') as f:
        f.write('\n'.join([
            'print "hello"'
        ]))

    feedback = s.process(['python', source_file], stdout=subprocess.PIPE)
    stdout = feedback.stdout.read()

    assert feedback.ended_correctly == True
    assert feedback.return_code == 0
    assert stdout == 'hello\n'

    print 'sandbox size (with python): {} bytes'.format(s.size())


if __name__ == "__main__":
    test_python_env()
