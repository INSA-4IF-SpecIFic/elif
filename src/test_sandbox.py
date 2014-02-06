
import os
import shutil
import subprocess
from sandbox import Sandbox, RunTimeContext

def test_root_dir():
    s = Sandbox()
    root_dir = s.root_directory

    assert os.path.isdir(root_dir)
    del s
    assert not os.path.isdir(root_dir)

def test_basic_ls():
    s = Sandbox()

    s.fetch_bin("/bin/ls")
    p = s.process([s.root_directory + "bin/ls", "/"], stdout=subprocess.PIPE)
    p.wait()

    assert p.returncode == 0

    stdout = p.stdout.read()
    assert "bin" in stdout
    assert "tmp" in stdout
    assert "usr" in stdout
    del s

def test_jail_security():
    s = Sandbox()

    s.fetch_bin("/bin/cat")
    p = s.process([s.root_directory + "bin/cat", os.path.abspath(__file__)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()

    assert p.returncode != 0
    del s

def test_infinte_loop():
    s = Sandbox(cpu_time_limit=1)

    s.fetch_bin("/bin/sh")
    shutil.copy(os.path.join(os.path.dirname(__file__), "test_scripts/sandbox_infinite.sh"), s.root_directory + "sandbox_infinite.sh")

    p = s.process([s.root_directory + "bin/sh", "/sandbox_infinite.sh"])
    p.wait()

    assert p.returncode != 0
    del s

def test_run_time_context():
    r0 = RunTimeContext({'max_cpu_time': 1})
    r1 = RunTimeContext(inherited=[r0])

    assert r0['max_cpu_time'] == 1
    assert r1['max_cpu_time'] == 1

    r0['max_cpu_time'] = 2
    assert r0['max_cpu_time'] == 2
    assert r1['max_cpu_time'] == 2

    r1['max_heap_size'] = 2
    assert r0['max_heap_size'] == RunTimeContext.default_values['max_heap_size']
    assert r1['max_heap_size'] == 2


if __name__ == "__main__":
    pass

