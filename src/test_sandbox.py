
import os
import shutil
import subprocess
import pwd
import signal
from sandbox import which, Sandbox, Profile


def test_which():
    assert which('sh') == '/bin/sh'
    assert which('ls') == '/bin/ls'
    assert which('cat') == '/bin/cat'
    assert which('echo') == '/bin/echo'
    assert which('id') == '/usr/bin/id'

def test_root_dir():
    s = Sandbox()
    root_dir = s.root_directory

    assert os.path.isdir(root_dir)
    del s
    assert not os.path.isdir(root_dir)

def test_basises():
    s = Sandbox()
    sandbox_basis = '/bin/ls'

    main_basis = s.to_main_basis(sandbox_basis)

    assert main_basis == s.root_directory[:-1] + sandbox_basis
    assert s.to_sandbox_basis(main_basis) == sandbox_basis
    assert len(main_basis.split('//')) == 1

    try:
        s.to_main_basis('bin/ls')

    except AssertionError:
        assert True

    else:
        assert False

def test_sandbox_which():
    s = Sandbox()

    assert s.which('sh') == None
    assert s.which('id') == None

    s.clone_bin('sh')
    s.clone_bin('id')

    assert s.isfile('/bin/sh')
    assert s.isfile('/usr/bin/id')
    assert s.which('sh') == '/bin/sh'
    assert s.which('id') == '/usr/bin/id'

    feedback = s.process(["id", "-u"])
    assert feedback.ended_correctly
    assert feedback.return_code == 0

    del s

def test_basic_stdout():
    s = Sandbox()
    s.clone_bin("ls")

    feedback = s.process(["ls", "/"], stdout=subprocess.PIPE)
    assert feedback.stdout
    assert not feedback.stderr
    stdout = feedback.stdout.read()
    assert feedback.ended_correctly
    assert feedback.return_code == 0
    assert "bin" in stdout
    assert "tmp" in stdout
    assert "usr" in stdout

    feedback = s.process(["ls", "/hello"], stdout=subprocess.PIPE)
    stdout = feedback.stdout.read()
    assert feedback.ended_correctly
    assert feedback.return_code != 0
    assert not "/hello" in stdout

    del s

def test_basic_stderr():
    s = Sandbox()
    s.clone_bin("ls")

    feedback = s.process(["ls", "/"], stderr=subprocess.PIPE)
    assert not feedback.stdout
    assert feedback.stderr
    stderr = feedback.stderr.read()
    assert feedback.ended_correctly
    assert feedback.return_code == 0
    assert "" == stderr

    feedback = s.process(["ls", "/hello"], stderr=subprocess.PIPE)
    stderr = feedback.stderr.read()
    assert feedback.ended_correctly
    assert feedback.return_code != 0
    assert "/hello" in stderr

    del s

def test_basic_stderr_in_stdout():
    s = Sandbox()
    s.clone_bin("ls")

    feedback = s.process(["ls", "/"], stderr=subprocess.STDOUT)
    assert feedback.stdout
    assert not feedback.stderr
    stdout = feedback.stdout.read()
    assert feedback.ended_correctly
    assert feedback.return_code == 0
    assert stdout == ""

    feedback = s.process(["ls", "/hello"], stderr=subprocess.STDOUT)
    assert feedback.stdout
    assert not feedback.stderr
    stdout = feedback.stdout.read()
    assert feedback.ended_correctly
    assert feedback.return_code != 0
    assert "/hello" in stdout

    feedback = s.process(["ls", "/"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    assert feedback.stdout
    assert not feedback.stderr
    stdout = feedback.stdout.read()
    assert feedback.ended_correctly
    assert feedback.return_code == 0
    assert "bin" in stdout
    assert "tmp" in stdout
    assert "usr" in stdout

    feedback = s.process(["ls", "/hello"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    assert feedback.stdout
    assert not feedback.stderr
    stdout = feedback.stdout.read()
    assert feedback.ended_correctly
    assert feedback.return_code != 0
    assert "/hello" in stdout

    del s

def test_environment():
    s = Sandbox()
    s.clone_bin("echo")
    s.clone_bin("sh")

    assert s.shell_environment['USER'] == s.user_name
    assert s.user_name != 'root'
    assert pwd.getpwnam(s.user_name).pw_uid != 0

    with s.open("/sandbox_env.sh", 'w') as f:
        f.write('\n'.join([
            '#!/bin/sh',
            'echo $HOME',
            'echo $USER',
            'echo $PATH',
            'echo $SHELL'
        ]))

    feedback = s.process(["sh", "/sandbox_env.sh"], stdout=subprocess.PIPE)
    assert feedback.ended_correctly
    assert feedback.return_code == 0

    i = 0
    for l in feedback.stdout:
        assert i != 0 or l.startswith(s.shell_environment['HOME'])
        assert i != 1 or l.startswith(s.shell_environment['USER'])
        assert i != 2 or l.startswith(s.shell_environment['PATH'])
        assert i != 3 or l.startswith(s.shell_environment['SHELL'])
        i += 1

    del s

def test_jail_security():
    s = Sandbox()
    s.clone_bin("cat")

    feedback = s.process(["cat", "/bin/cat"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert feedback.ended_correctly
    assert feedback.return_code == 0

    feedback = s.process(["cat", os.path.abspath(__file__)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert feedback.ended_correctly
    assert feedback.return_code != 0

    del s

def test_jail_whoami():
    profile = Profile({'max_processes': 10})
    s = Sandbox()
    s.clone_bin("id")

    feedback = s.process(["id", "-u"], profile=profile, stdout=subprocess.PIPE)
    stdout = feedback.stdout.read()
    assert feedback.ended_correctly
    assert feedback.return_code == 0
    assert stdout == "{}\n".format(pwd.getpwnam(s.user_name).pw_uid)

    del s

def test_jail_pwd():
    s = Sandbox()
    s.clone_bin("pwd")

    feedback = s.process(["pwd"], stdout=subprocess.PIPE)
    stdout = feedback.stdout.read()
    assert feedback.ended_correctly
    assert feedback.return_code == 0
    assert stdout == "/\n"

    del s

def test_clobbering():
    s = Sandbox()
    s.clone_bin("echo")
    s.clone_bin("cat")
    s.clone_bin("sh")

    cat_size = os.stat(s.to_main_basis('/bin/cat'))

    with s.open("/sandbox_clobber.sh", 'w') as f:
        f.write('\n'.join([
            '#!/bin/sh',
            'echo "clobbering $1 ..."',
            'echo "$0 $*" > $1',
            'echo "$?"'
        ]))

    feedback = s.process(["sh", "/sandbox_clobber.sh", "/bin/cat"], stdout=subprocess.PIPE)
    assert feedback.ended_correctly
    assert feedback.return_code == 0

    i = 0
    for l in feedback.stdout:
        assert i != 0 or l == "clobbering /bin/cat ...\n"
        assert i != 1 or int(l) != 0
        i += 1

    assert os.stat(s.to_main_basis('/bin/cat')) == cat_size

    del s

def test_infinite_loop():
    profile = Profile({'max_cpu_time': 1, 'max_duration': 10})
    s = Sandbox()
    s.clone_bin("sh")

    with s.open("/sandbox_infinite.sh", 'w') as f:
        f.write('\n'.join([
            '#!/bin/sh',
            'while :',
            'do',
            '    echo "hello"',
            'done'
        ]))

    feedback = s.process(["sh", "/sandbox_infinite.sh"], profile=profile)
    assert feedback.killing_signal != 0
    assert not feedback.ended_correctly
    assert feedback.return_code == 0
    #assert 'max_cpu_time' in feedback.report  # commented for non determinist behavior on linux
    assert 'max_duration' not in feedback.report
    del s

def test_sleep_abort():
    profile = Profile({'max_cpu_time': 10, 'max_duration': 1, 'max_processes': 32})
    s = Sandbox()
    s.clone_bin("sh")
    s.clone_bin("sleep")

    with s.open("/sandbox_sleep.sh", 'w') as f:
        f.write('\n'.join([
            '#!/bin/sh',
            'sleep 5'
        ]))

    feedback = s.process(["sh", "/sandbox_sleep.sh"], profile=profile)
    assert feedback.killing_signal == signal.SIGKILL
    assert not feedback.ended_correctly
    assert feedback.return_code == 0
    assert 'max_cpu_time' not in feedback.report
    assert 'max_duration' in feedback.report
    del s

def test_subprocess():
    profile = Profile({'max_processes': 32})
    s = Sandbox()
    s.clone_bin("sh")
    s.clone_bin("echo")
    s.clone_bin("cat")

    with s.open("/sandbox_subprocess.sh", 'w') as f:
        f.write('\n'.join([
            '#!/bin/sh',
            'echo "visible";',
            'cat $0;',
            'echo "hidden";'
        ]))

    feedback = s.process(["sh", "/sandbox_subprocess.sh"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout = feedback.stdout.read()
    assert 'visible' in stdout
    assert 'hidden' not in stdout
    assert 'fork' in feedback.stderr.read()
    assert feedback.ended_correctly
    assert feedback.return_code != 0

    feedback = s.process(["sh", "/sandbox_subprocess.sh"], profile=profile, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout = feedback.stdout.read()
    assert 'visible' in stdout
    assert 'hidden' in stdout
    assert 'fork' not in feedback.stderr.read()
    assert feedback.ended_correctly
    assert feedback.return_code == 0

    del s

    return True

def test_subprocess_series():
    profile = Profile({'max_processes': 5})
    s = Sandbox()
    s.clone_bin("sh")
    s.clone_bin("echo")
    s.clone_bin("cat")

    with s.open("/sandbox_content.txt", 'w') as f:
        f.write('\n'.join([
            'hello',
            ''
        ]))

    with s.open("/sandbox_subprocess.sh", 'w') as f:
        f.write('\n'.join([
            '#!/bin/sh',
        ]))

        for i in range(0, 10):
            f.write('\n'.join([
                '#!/bin/sh',
                'cat /sandbox_content.txt &',
            ]))

    feedback = s.process(["sh", "/sandbox_subprocess.sh"], profile=profile, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout = feedback.stdout.read()
    assert len(stdout.split('hello')) <= (5 + 1)
    assert feedback.ended_correctly
    assert feedback.return_code != 0

    del s

    return True

def test_fork_bombe():
    # we do not launch the fork bomb if the subprocess test is not working
    assert test_subprocess()
    assert test_subprocess_series()
    assert Profile.default_values['max_processes'] == 0
    assert Profile()['max_processes'] == 0

    s = Sandbox()
    s.clone_bin("sh")
    s.clone_bin("echo")

    with s.open("/sandbox_subprocess.sh", 'w') as f:
        f.write('\n'.join([
            '#!/bin/sh',
            'echo "visible";',
            'sh $1 &',
            'echo "hidden";'
        ]))

    feedback = s.process(["sh", "/sandbox_subprocess.sh"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout = feedback.stdout.read()
    assert 'visible' in stdout
    assert 'hidden' not in stdout
    assert 'fork' in feedback.stderr.read()
    assert feedback.ended_correctly
    assert feedback.return_code != 0

    del s

def test_run_time_context():
    r0 = Profile({'max_cpu_time': 1})
    r1 = Profile(inherited=[r0])

    assert r0['max_cpu_time'] == 1
    assert r1['max_cpu_time'] == 1

    r0['max_cpu_time'] = 2
    assert r0['max_cpu_time'] == 2
    assert r1['max_cpu_time'] == 2

    r1['max_heap_size'] = 2
    assert r0['max_heap_size'] == Profile.default_values['max_heap_size']
    assert r1['max_heap_size'] == 2

def test_sigpipe():
    s = Sandbox()
    s.clone_bin("wc")

    stdin = 'hello world !!\n' * 1000000

    feedback = s.process(["wc"], stdin=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert True # no crashes

    del s



if __name__ == "__main__":
    pass

