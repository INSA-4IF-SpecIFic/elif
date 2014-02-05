
import os
import shutil
import subprocess
from sandbox import Sandbox

def test_root_dir():
    s = Sandbox()
    root_dir = s.root_directory

    assert os.path.isdir(root_dir)
    del s
    assert not os.path.isdir(root_dir)

def test_basic_ls():
    s = Sandbox()

    shutil.copy("/bin/ls", s.root_directory + "bin/")
    p = s.process([s.root_directory + "bin/ls", "/"], stdout=subprocess.PIPE)
    p.wait()
    stdout = p.stdout.read()

    assert "bin" in stdout
    del s

def test_jail_security():
    s = Sandbox()

    shutil.copy("/bin/cat", s.root_directory + "bin/")
    p = s.process([s.root_directory + "bin/cat", os.path.abspath(__file__)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()

    assert p.returncode != 0
    del s

