
import os
import shutil
import subprocess
import pwd
from sandbox import Sandbox, Profile

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

def test_basic_stdout():
    s = Sandbox()
    s.clone_bin("/bin/ls")

    feedback = s.process(["/bin/ls", "/"], stdout=subprocess.PIPE)
    assert feedback.stdout
    assert not feedback.stderr
    stdout = feedback.stdout.read()
    assert feedback.ended_correctly
    assert feedback.return_code == 0
    assert "bin" in stdout
    assert "tmp" in stdout
    assert "usr" in stdout

    feedback = s.process(["/bin/ls", "/hello"], stdout=subprocess.PIPE)
    stdout = feedback.stdout.read()
    assert feedback.ended_correctly
    assert feedback.return_code != 0
    assert not "/hello" in stdout

    del s

def test_basic_stderr():
    s = Sandbox()
    s.clone_bin("/bin/ls")

    feedback = s.process(["/bin/ls", "/"], stderr=subprocess.PIPE)
    assert not feedback.stdout
    assert feedback.stderr
    stderr = feedback.stderr.read()
    assert feedback.ended_correctly
    assert feedback.return_code == 0
    assert "" == stderr

    feedback = s.process(["/bin/ls", "/hello"], stderr=subprocess.PIPE)
    stderr = feedback.stderr.read()
    assert feedback.ended_correctly
    assert feedback.return_code != 0
    assert "/hello" in stderr

    del s

def test_basic_stderr_in_stdout():
    s = Sandbox()
    s.clone_bin("/bin/ls")

    feedback = s.process(["/bin/ls", "/"], stderr=subprocess.STDOUT)
    assert feedback.stdout
    assert not feedback.stderr
    stdout = feedback.stdout.read()
    assert feedback.ended_correctly
    assert feedback.return_code == 0
    assert stdout == ""

    feedback = s.process(["/bin/ls", "/hello"], stderr=subprocess.STDOUT)
    assert feedback.stdout
    assert not feedback.stderr
    stdout = feedback.stdout.read()
    assert feedback.ended_correctly
    assert feedback.return_code != 0
    assert "/hello" in stdout

    feedback = s.process(["/bin/ls", "/"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    assert feedback.stdout
    assert not feedback.stderr
    stdout = feedback.stdout.read()
    assert feedback.ended_correctly
    assert feedback.return_code == 0
    assert "bin" in stdout
    assert "tmp" in stdout
    assert "usr" in stdout

    feedback = s.process(["/bin/ls", "/hello"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    assert feedback.stdout
    assert not feedback.stderr
    stdout = feedback.stdout.read()
    assert feedback.ended_correctly
    assert feedback.return_code != 0
    assert "/hello" in stdout

    del s

def test_jail_security():
    s = Sandbox()
    s.clone_bin("/bin/cat")

    feedback = s.process(["/bin/cat", "/bin/cat"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert feedback.ended_correctly
    assert feedback.return_code == 0

    feedback = s.process(["/bin/cat", os.path.abspath(__file__)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert feedback.ended_correctly
    assert feedback.return_code != 0

    del s

def test_jail_whoami():
    profile = Profile({'max_processes': 10})
    s = Sandbox()
    s.clone_bin("/usr/bin/id")

    feedback = s.process(["/usr/bin/id", "-u"], profile=profile, stdout=subprocess.PIPE)
    stdout = feedback.stdout.read()
    assert feedback.ended_correctly
    assert feedback.return_code == 0
    assert stdout == "{}\n".format(pwd.getpwnam(s.user_name).pw_uid)

    del s

def test_jail_pwd():
    s = Sandbox()
    s.clone_bin("/bin/pwd")

    feedback = s.process(["/bin/pwd"], stdout=subprocess.PIPE)
    stdout = feedback.stdout.read()
    assert feedback.ended_correctly
    assert feedback.return_code == 0
    assert stdout == "/\n"

    del s

def test_clobbering():
    s = Sandbox()
    s.clone_bin("/bin/echo")
    s.clone_bin("/bin/cat")
    s.clone_bin("/bin/sh")

    cat_size = os.stat(s.to_main_basis('/bin/cat'))

    with s.open("/sandbox_clobber.sh", 'w') as f:
        f.write('\n'.join([
            '#!/bin/sh',
            'echo "clobbering $1 ..."',
            'echo "$0 $*" > $1',
            'echo "$?"'
        ]))

    feedback = s.process(["/bin/sh", "/sandbox_clobber.sh", "/bin/cat"], stdout=subprocess.PIPE)
    stdout = feedback.stdout.read()
    assert feedback.ended_correctly
    assert feedback.return_code == 0
    assert stdout == "clobbering /bin/cat ...\n1\n"
    assert os.stat(s.to_main_basis('/bin/cat')) == cat_size

    del s

def test_infinte_loop():
    profile = Profile({'max_cpu_time': 1})
    s = Sandbox()

    s.clone_bin("/bin/sh")
    shutil.copy(os.path.join(os.path.dirname(__file__), "test_scripts/sandbox_infinite.sh"), s.to_main_basis("/sandbox_infinite.sh"))

    feedback = s.process(["/bin/sh", "/sandbox_infinite.sh"], profile=profile)

    assert feedback.killing_signal != 0
    assert not feedback.ended_correctly
    assert feedback.return_code == 0
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


if __name__ == "__main__":
    pass

