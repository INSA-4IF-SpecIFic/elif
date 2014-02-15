
import os
import sys
import platform
import resource
import subprocess
import tempfile
import shutil
import pwd


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


class ProcessFeedback(object):
    """Sandbox's process feedback

    Members:
        return_code: the process return code (not return_code for compatibility with subprocess.Popen)
        killing_signal: the signal ID that has killed the process
        stdout: the stdout's pipe
        stderr: the stderr's pipe
        ressources: used ressources information (CF offcial documentation resource.getrusage())
    """

    def __init__(self, return_code, killing_signal, stdout, stderr, resources):
        self.return_code = return_code
        self.killing_signal = killing_signal
        self.stdout = stdout
        self.stderr = stderr
        self.resources = resources

    @property
    def ended_correctly(self):
        return self.killing_signal == 0


class Sandbox(object):
    """Sandbox object to execute code in a chroot jail (must be executed as root)

    Important: A chroot jail is actually a technic to change the root directory before executing sub processes. Therefore
    the use of Sandbox is very tricky, two you have then two root basises:
        - the main basis: the very one of your computer
        - the sandbox basis: the one of the sand box

    Members:
        root_directory (in the main basis)
        user_name: the running user's name
    """

    def __init__(self, root_directory = None):
        assert os.getuid() == 0  # must be root to instantiate a Sandbox

        if not root_directory:
            self.root_directory = tempfile.mkdtemp(suffix='.sandbox', prefix='elif_') + "/"
        else:
            self.root_directory = root_directory

        self.user_name = 'nobody'
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
            os.makedirs(directory, 0755)

        else:
            os.chmod(directory, 0755)

    def open(self, path, mode):
        return open(self.to_main_basis(path), mode)

    def chmod(self, path, mode):
        return os.chmod(self.to_main_basis(path), mode)

    def mktemp(self, prefix='tmp', suffix=''):
        """Allocates a temporary file name in the /tmp/ directory of the sand box and return its path

        Important: the returned path is in the main basis
        """

        return tempfile.mktemp(prefix=prefix, suffix=suffix, dir=self.tmp_directory)

    def clone(self, path_src):
        """Clones a common file to the sandbox

        Important:
            - <path_src> must be in the main basis
        """
        assert path_src[0] == '/'

        path_dest = self.to_main_basis(path_src)

        shutil.copy(path_src, path_dest)
        os.chmod(path_dest, 0755)

        return True

    def clone_bin(self, bin_path_src):
        """Clones a binary file and its dependencies to the sandbox

        Important:
            - <bin_path_src> must be in the main basis
        """
        self.clone(bin_path_src)

        return self.clone_bin_dependencies(bin_path_src)

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
                os.makedirs(dep_dest_dir, 0755)

            shutil.copy2(dep_src, dep_dest)
            os.chmod(dep_dest, 0755)

        return True

    def process(self, cmd, profile=None, stdin=None, stdout=None, stderr=None):
        assert len(cmd) >= 1

        if profile == None:
            profile = Profile()

        env = dict()
        env['PATH'] = '/usr/bin:/bin'
        env['USER'] = self.user_name
        env['HOME'] = '/'
        env['SHELL'] = '/bin/sh'

        stdin_r = None
        stdin_w = None

        if isinstance(stdin, str):
            stdin_r, stdin_w = os.pipe()

        stdout_r = None
        stdout_w = None

        if stdout == subprocess.PIPE:
            stdout_r, stdout_w = os.pipe()

        stderr_r = None
        stderr_w = None

        if stderr == subprocess.PIPE:
            stderr_r, stderr_w = os.pipe()

        elif stderr == subprocess.STDOUT:
            if stdout == subprocess.PIPE:
                stderr_w = stdout_w

            else:
                stdout_r, stderr_w = os.pipe()

        pid = os.fork()

        if pid == 0:
            # children process
            uid = pwd.getpwnam(self.user_name).pw_uid

            # stdin setup
            if stdin_r:
                sys.stdin = os.fdopen(stdin_r, 'r')
                os.dup2(sys.stdin.fileno(), 0)

            if stdin_w:
                os.close(stdin_w)


            # stdout setup
            if stdout_r:
                os.close(stdout_r)

            if stdout_w:
                sys.stdout = os.fdopen(stdout_w, 'w')
                os.dup2(sys.stdout.fileno(), 1)


            # stderr setup
            if stderr_r:
                os.close(stderr_r)

            if stderr_w:
                sys.stderr = os.fdopen(stderr_w, 'w')
                os.dup2(sys.stderr.fileno(), 2)

            # changes root
            os.chroot(self.root_directory)
            os.chdir('/')

            resource.setrlimit(resource.RLIMIT_CPU, (profile['max_cpu_time'], profile['max_cpu_time']))
            resource.setrlimit(resource.RLIMIT_DATA, (profile['max_heap_size'], profile['max_heap_size']))
            resource.setrlimit(resource.RLIMIT_STACK, (profile['max_stack_size'], profile['max_stack_size']))

            # os.setuid() mights create pseverals threads on linux, then we limit processes after
            os.setuid(uid)
            resource.setrlimit(resource.RLIMIT_NPROC, (profile['max_processes'], profile['max_processes']))

            # launch executable
            os.execve(cmd[0], cmd, env)

        # stdin setup
        if stdin_r:
            os.close(stdin_r)

        if stdin_w:
            stdin_w = os.fdopen(stdin_w, 'w')

        if isinstance(stdin, str):
            stdin_w.write(stdin)

        if stdin_w:
            stdin_w.close()


        # stdout/stderr setup
        if stdout_r:
            stdout_r = os.fdopen(stdout_r, 'r')

        if stdout_w:
            os.close(stdout_w)

        if stderr_r:
            stderr_r = os.fdopen(stderr_r, 'r')

        if stderr_w and stderr_w != stdout_w:
            os.close(stderr_w)

        pid, exit_status, resources = os.wait4(pid, 0)

        return_code = int((exit_status >> 8) & 0xFF)
        killing_signal = int(exit_status & 0xFF)

        return ProcessFeedback(
            return_code=return_code,
            killing_signal=killing_signal,
            stdout=stdout_r,
            stderr=stderr_r,
            resources=resources
        )

    @property
    def tmp_directory(self):
        """Returns the sandbox's /tmp/ directory in the main basis"""

        return "{}tmp/".format(self.root_directory)

    def __del__(self):
        self._clean()

    def _build(self):
        self.makedirs('/')
        self.makedirs('/bin/')
        self.makedirs('/tmp/')
        self.makedirs('/usr/bin/')
        self.makedirs('/usr/lib/')

        if platform.system() == "Darwin":
            """ Mac OS X specific environment """

            self.clone_bin("/usr/lib/dyld")

    def _clean(self):
        if os.path.isdir(self.root_directory):
            shutil.rmtree(self.root_directory)
