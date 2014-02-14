
import os
import sys
import platform
import resource
import subprocess
import tempfile
import shutil


def lib_dependencies_osx(binary_path, deps):
    """Get executable's dynamic libraries list (Mac OS X specific code)"""

    otool = subprocess.Popen(['otool', '-L', binary_path], stdout=subprocess.PIPE)
    otool.wait()

    i = 0

    for l in otool.stdout:
        i += 1

        if i == 1:
            continue

        l = l.strip()
        dep = l.split(' ')[0]

        if dep in deps:
            continue

        deps.append(dep)
        lib_dependencies_osx(dep, deps)

    return deps

def lib_dependencies_linux(binary_path, deps):
    """Get executable's dynamic libraries list (Linux specific code)"""

    otool = subprocess.Popen(['ldd', binary_path], stdout=subprocess.PIPE)
    otool.wait()

    for l in otool.stdout:
        l = l.strip()
        l = l.split(' ')

        for dep in l:
            if dep == '':
                continue

            if dep[0] != '/':
                continue

            if dep not in deps:
                deps.append(dep)
                lib_dependencies_linux(dep, deps)

            break

    return deps

def lib_dependencies(binary_path):
    """Get executable's dynamic libraries list"""

    deps = list()

    if platform.system() == "Darwin":
        lib_dependencies_osx(binary_path, deps)

    else:
        lib_dependencies_linux(binary_path, deps)

    return deps


class Profile(object):
    """Contains all Sandbox's execution constants"""
    # parameters: dict()

    def __init__(self, parameters=dict(), inherited=list()):
        self.parameters = dict(parameters)
        self.inherited = list(inherited)

    def __setitem__(self, key, value):
        assert key in Profile.params
        assert type(value) == type(Profile.params[key])

        self.parameters[key] = value

    def __getitem__(self, key):
        assert key in Profile.params

        def getitem_rec(self, key):
            if key in self.parameters:
                return self.parameters[key]

            value = None

            for p in self.inherited:
                tmp = getitem_rec(p, key)

                if tmp != None:
                    value = tmp

            return value

        value = getitem_rec(self, key)

        if value == None:
            return Profile.default_values[key]

        return value

    params = {
        'max_cpu_time': resource.RLIMIT_CPU, # in seconds
        'max_heap_size': resource.RLIMIT_DATA, # in bytes
        'max_stack_size': resource.RLIMIT_STACK, # in bytes
        'max_processes': resource.RLIMIT_NPROC,
    }

    default_values = {
        'max_cpu_time': 10,
        'max_heap_size': 16 * 1024 * 1024,
        'max_stack_size': 32 * 1024,
        'max_processes': 0,
    }


class Sandbox(object):
    """Sandbox object to execute code in a chroot jail (must be executed as root)

    Important: A chroot jail is actually a technic to change the root directory before executing sub processes. Therefore
    the use of Sandbox is very tricky, two you have then two root basises:
        - the main basis: the very one of your computer
        - the sandbox basis: the one of the sand box

    Members:
        root_directory (in the main basis)
    """

    def __init__(self, root_directory = None):
        assert os.getuid() == 0  # must be root to instantiate a Sandbox

        if not root_directory:
            self.root_directory = tempfile.mkdtemp(suffix='.sandbox', prefix='elif_') + "/"
        else:
            self.root_directory = root_directory

        self._build()

    def to_main_basis(self, path):
        """Converts absolute path from the sandbox's basis to the main basis"""

        assert path[0] == '/'
        return self.root_directory[:-1] + path

    def to_sandbox_basis(self, path):
        """Converts absolute path from the main basis to the sandbox's basis"""

        return "/" + os.path.relpath(os.path.abspath(path), os.path.abspath(self.root_directory))

    def recover(self):
        """Recover the sandbox from scratch"""

        self._clean()
        self._build()

    def makedirs(self, directory):
        directory = self.to_main_basis(directory)

        if not os.path.isdir(directory):
            os.makedirs(directory)

    def mktemp(self, prefix='tmp', suffix=''):
        """Allocates a temporary file name in the /tmp/ directory of the sand box and return its path

        Important: the returned path is in the main basis
        """

        return tempfile.mktemp(prefix=prefix, suffix=suffix, dir=self.tmp_directory)

    def clone_bin_dependencies(self, executable_path):
        """Clone binary file's dependencies

        Important:
            - <executable_path> must be in the main basis
        """

        dependencies = lib_dependencies(executable_path)

        for dep_src in dependencies:
            dep_dest = self.to_main_basis(dep_src)
            dep_dest_dir = os.path.dirname(dep_dest)

            if os.path.isfile(dep_dest):
                continue

            if not os.path.isdir(dep_dest_dir):
                os.makedirs(dep_dest_dir)

            shutil.copy2(dep_src, dep_dest)

        return True

    def clone_bin(self, bin_path_src):
        """Clones a binary file and its dependencies to the sandbox

        Important:
            - <bin_path_src> must be in the main basis
        """

        bin_path_src = os.path.abspath(bin_path_src)
        bin_path_dest = self.to_main_basis(bin_path_src)

        shutil.copy(bin_path_src, bin_path_dest)

        return self.clone_bin_dependencies(bin_path_src)

    def process(self, cmd, profile=None, stdin=None, stdout=None, stderr=None):
        """Processes a sub process, wait for its end and then returns the subprocess.Popen

        Caution: all paths in the <cmd> parameter must be in the sandbox basis
        """

        if profile == None:
            profile = Profile()

        def subprocess_limits():
            os.chroot(self.root_directory)

            for key, name in Profile.params.items():
                value = profile[key]
                resource.setrlimit(name, (value, value))

        stdin_param = None

        if isinstance(stdin, str):
            stdin_param = subprocess.PIPE

        process = subprocess.Popen(cmd, stdin=stdin_param, stdout=stdout, stderr=stderr, preexec_fn=subprocess_limits)

        if isinstance(stdin, str):
            process.stdin.write(stdin)
            process.stdin.close()

        process.wait()

        return process

    @property
    def tmp_directory(self):
        """Returns the sandbox's /tmp/ directory in the main basis"""

        return "{}tmp/".format(self.root_directory)

    def __del__(self):
        self._clean()

    def _build(self):
        self.makedirs('/')
        self.makedirs('/tmp/')
        self.makedirs('/bin/')
        self.makedirs('/usr/lib/')

        if platform.system() == "Darwin":
            """ Mac OS X specific environment """

            self.clone_bin("/usr/lib/dyld")

    def _clean(self):
        if os.path.isdir(self.root_directory):
            shutil.rmtree(self.root_directory)
