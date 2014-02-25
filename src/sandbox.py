
import os
import sys
import platform
import resource
import subprocess
import tempfile
import shutil
import pwd
import time
import signal


def which(file):
    """Locates a program <file> in the user's path"""

    for path in os.environ["PATH"].split(os.pathsep):
        if os.path.exists(path + "/" + file):
            return path + "/" + file

    return None


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
        assert key in Profile.default_values
        assert type(value) == type(Profile.default_values[key])

        self.parameters[key] = value

    def __getitem__(self, key):
        assert key in Profile.default_values

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

    default_values = {
        'max_cpu_time': 10,
        'max_duration': 20,
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
        report: running report flags
    """

    def __init__(self, return_code, killing_signal, stdout, stderr, resources, report):
        self.return_code = return_code
        self.killing_signal = killing_signal
        self.stdout = stdout
        self.stderr = stderr
        self.resources = resources
        self.report = report

    @property
    def ended_correctly(self):
        """Checks if the process has ended correctly"""

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
        env_paths: the environment's paths
    """

    def __init__(self, root_directory = None):
        assert os.getuid() == 0  # must be root to instantiate a Sandbox

        if not root_directory:
            self.root_directory = tempfile.mkdtemp(suffix='.sandbox', prefix='elif_') + "/"
        else:
            self.root_directory = root_directory

        self.running_envs = list()
        self.user_name = 'nobody'
        self.env_paths = [
            '/usr/bin',
            '/bin'
        ]

        self._build()

    @property
    def shell_environment(self):
        """Gets running shell environment constants"""

        environ = dict()
        environ['PATH'] = os.pathsep.join(self.env_paths)
        environ['USER'] = self.user_name
        environ['HOME'] = '/'
        environ['SHELL'] = '/bin/sh'

        return environ

    def to_main_basis(self, path):
        """Converts absolute path from the sandbox's basis to the main basis"""

        assert path[0] == '/'
        return self.root_directory[:-1] + path

    def to_sandbox_basis(self, path):
        """Converts absolute path from the main basis to the sandbox's basis"""

        return "/" + os.path.relpath(os.path.abspath(path), os.path.abspath(self.root_directory))

    def which(self, file):
        """Locates a program <file> in the sandbox and returns his path in the sandbox's basis

        Parameters:
            - <file>: file name to look at
        """

        for path in self.shell_environment["PATH"].split(os.pathsep):
            path += "/" + file

            if os.path.exists(self.to_main_basis(path)):
                return path

        return None

    def isfile(self, path):
        """Tests if a file exists in sandbox

        Parameters:
            - <path>: path of the file to test in the sandbox's basis
        """
        assert path.startswith('/')

        return os.path.isfile(self.to_main_basis(path))

    def makedirs(self, directory):
        """Tests if a file exists in sandbox

        Parameters:
            - <directory>: path of the directory to make in the sandbox's basis
        """

        directory = self.to_main_basis(directory)

        if not os.path.isdir(directory):
            os.makedirs(directory, 0755)

        else:
            os.chmod(directory, 0755)

    def open(self, path, mode):
        """Opens a file in the sandbox

        Parameters:
            - <path>: path of the file to open
            - <mode>: desired open file mode
        """

        return open(self.to_main_basis(path), mode)

    def chmod(self, path, mode):
        """Sets file's CHMOD in the sandbox

        Parameters:
            - <path>: path of the file to open
            - <mode>: desired file mode
        """

        return os.chmod(self.to_main_basis(path), mode)

    def mktemp(self, prefix='tmp', suffix=''):
        """Allocates a temporary file name in the /tmp/ directory of the sand box and return its path

        Important: the returned path is in the main basis

        Parameters:
            - <prefix>: temporary directory's prefix
            - <suffix>: temporary directory's suffix
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

    def clone_dir(self, path_src):
        """Clones a directory to the sandbox

        Important:
            - <path_src> must be in the main basis
        """
        assert path_src[0] == '/'

        path_dest = self.to_main_basis(path_src)

        if os.path.exists(path_dest):
            return

        shutil.copytree(path_src, path_dest)

    def clone_bin(self, bin_path_src):
        """Clones a binary file and its dependencies to the sandbox

        Important:
            - <bin_path_src> must be in the main basis or a known program in user's environment
        """
        if not bin_path_src.startswith('/'):
            bin_path_src = which(bin_path_src)

            assert bin_path_src.startswith('/')  # couldn't find command <bin_path_src>

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
        """Processes a program securly in the sandbox, and returns its feedback

        Parameters:
            - cmd: the program invocation command
            - profile: the environment limits
            - stdin: a string to give by the stdin
            - stdout: redirect stdout in a pipe by passing subprocess.PIPE
            - stdout: redirect stderr in a pipe by passing subprocess.PIPE or in the stdout pipe with subprocess.STDOUT
        """
        assert len(cmd) >= 1

        cmd_exec = cmd[0]

        if not cmd_exec.startswith('/'):
            cmd_exec = self.which(cmd_exec)

            assert cmd_exec  # unable to find cmd[0]

        if profile == None:
            profile = Profile()

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

            resource.setrlimit(resource.RLIMIT_CPU, (profile['max_cpu_time'], profile['max_cpu_time'] + 2))
            resource.setrlimit(resource.RLIMIT_DATA, (profile['max_heap_size'], profile['max_heap_size']))
            resource.setrlimit(resource.RLIMIT_STACK, (profile['max_stack_size'], profile['max_stack_size']))

            # os.setuid() mights create pseverals threads on linux, then we limit processes after
            os.setuid(uid)
            resource.setrlimit(resource.RLIMIT_NPROC, (profile['max_processes'], profile['max_processes']))

            # launch executable
            os.execve(cmd_exec, cmd, self.shell_environment)

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

        report = set()
        exit_status = None
        resources = None
        duration_quantum = 0.1
        duration = 0.0
        exit_cause = None

        while True:
            pid_s, exit_status, resources = os.wait4(pid, os.WNOHANG)

            if pid_s != 0:
                break

            if duration <= profile['max_duration']:
                duration += duration_quantum
                time.sleep(duration_quantum)

                continue

            os.kill(pid, signal.SIGKILL)
            exit_cause = 'max_duration'

            pid_s, exit_status, resources = os.wait4(pid, 0)

            break

        return_code = int((exit_status >> 8) & 0xFF)
        killing_signal = int(exit_status & 0xFF)

        if killing_signal == signal.SIGXCPU:
            report.add('max_cpu_time')

        if exit_cause != None:
            report.add(exit_cause)

        if (resources.ru_utime + resources.ru_stime) > profile['max_cpu_time']:
            report.add('max_cpu_time')

        return ProcessFeedback(
            return_code=return_code,
            killing_signal=killing_signal,
            stdout=stdout_r,
            stderr=stderr_r,
            resources=resources,
            report=list(report)
        )

    def add_running_env(self, env_callback):
        assert env_callback not in self.running_envs

        env_callback(self)

        self.running_envs.append(env_callback)

    def recover(self):
        """Recover the sandbox from scratch"""

        self._clean()
        self._build()

    @property
    def tmp_directory(self):
        """Returns the sandbox's /tmp/ directory in the main basis"""

        return self.to_main_basis('/tmp/')

    def __del__(self):
        self._clean()

    def _build(self):
        self.makedirs('/')
        self.makedirs('/bin/')
        self.makedirs('/tmp/')
        self.makedirs('/usr/bin/')
        self.makedirs('/usr/lib/')

        for env_callback in self.running_envs:
            env_callback(self)

        if platform.system() == "Darwin":
            """ Mac OS X specific environment """

            self.clone_bin("/usr/lib/dyld")

    def _clean(self):
        if os.path.isdir(self.root_directory):
            shutil.rmtree(self.root_directory)
