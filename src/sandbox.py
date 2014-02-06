
import os
import sys
import platform
import resource
import subprocess
import tempfile
import shutil


def lib_dependencies(binary_path, deps=None):
    if deps == None:
        deps = list()

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
        lib_dependencies(dep, deps)

    return deps


class RunTimeContext(object):
    # parameters: dict()

    def __init__(self, parameters=dict(), inherited=list()):
        self.parameters = dict(parameters)
        self.inherited = list(inherited)

    def __setitem__(self, key, value):
        assert key in RunTimeContext.params
        assert type(value) == type(RunTimeContext.params[key])

        self.parameters[key] = value

    def __getitem__(self, key):
        assert key in RunTimeContext.params

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
            return RunTimeContext.default_values[key]

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
    # root_directory

    def __init__(self, root_directory = None):
        if not root_directory:
            self.root_directory = tempfile.mkdtemp(suffix='.sandbox', prefix='elif_') + "/"
        else:
            self.root_directory = root_directory

        self._build()

    def __del__(self):
        self._clean()

    def _build(self):
        self._ensure_directory('./')
        self._ensure_directory('./tmp/')
        self._ensure_directory('./bin/')
        self._ensure_directory('./usr/lib/')

        os_name = platform.system()

        """ Mac OS X specific environment """
        if os_name == "Darwin":
            shutil.copy2("/usr/lib/dyld", "{}usr/lib/dyld".format(self.root_directory))
            self.fetches_dependencies("{}usr/lib/dyld".format(self.root_directory))

    def _ensure_directory(self, directory):
        directory = self.root_directory + directory

        if not os.path.isdir(directory):
            os.makedirs(directory)

    def _clean(self):
        if os.path.isdir(self.root_directory):
            shutil.rmtree(self.root_directory)

    def recover(self):
        self._clean()
        self._build()


    @property
    def tmp_directory(self):
        return "{}tmp/".format(self.root_directory)

    def mktemp(prefix, suffix):
        return tempfile.mktemp(prefix=prefix, suffix=suffix, dir=self.tmp_directory)


    def fetches_dependencies(self, executable_path):
        dependencies = lib_dependencies(executable_path)

        for dep_src in dependencies:
            dep_dest = "{}{}".format(self.root_directory[:-1], dep_src)
            dep_dest_dir = os.path.dirname(dep_dest)

            if os.path.isfile(dep_dest):
                continue

            if not os.path.isdir(dep_dest_dir):
                os.makedirs(dep_dest_dir)

            shutil.copy2(dep_src, dep_dest)

        return True

    def fetch_bin(self, bin_path_src):
        bin_path_src = os.path.abspath(bin_path_src)
        bin_path_dest = self.root_directory[:-1] + bin_path_src

        shutil.copy(bin_path_src, bin_path_dest)

        return self.fetches_dependencies(bin_path_src)

    def root_path(self, path):
        return "/" + os.path.relpath(os.path.abspath(path), os.path.abspath(self.root_directory))

    def process(self, cmd, profile=None, stdout=None, stderr=None):
        if profile == None:
            profile = RunTimeContext()

        def subprocess_limits():
            os.chroot(self.root_directory)

            for key, name in RunTimeContext.params.items():
                value = profile[key]
                resource.setrlimit(name, (value, value))

        chroot_cmd = list()
        chroot_cmd.append(self.root_path(cmd[0]))
        chroot_cmd.extend(cmd[1:])

        self.fetches_dependencies(cmd[0])

        return subprocess.Popen(chroot_cmd, stdout=stdout, stderr=stderr, preexec_fn=subprocess_limits)


if __name__ == "__main__":
    s = Sandbox("./.sandbox/", cpu_time_limit=1)

    s.fetch_bin('/bin/ls')
    p = s.process(['.sandbox/bin/ls', '-l', '/'])
    p.wait()

    del s

