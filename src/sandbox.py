
import os
import sys
import platform
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


class Sandbox(object):
    # root_directory

    def __init__(self, root_directory = None):
        if not root_directory:
            self.root_directory = tempfile.mkdtemp(suffix='.sandbox', prefix='elif_') + "/"
        else:
            self.root_directory = root_directory

        print "initializing sandbox ({})".format(self.root_directory)

        self._build()

    def __del__(self):
        print "cleaning sandbox ({})".format(self.root_directory)
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

            print "{} -> {}".format(dep_src, dep_dest)

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

    def process(self, cmd, stdout=None, stderr=None):
        chroot_cmd = list()
        chroot_cmd.extend(['sudo', 'chroot', self.root_directory])
        chroot_cmd.append(self.root_path(cmd[0]))
        chroot_cmd.extend(cmd[1:])

        self.fetches_dependencies(cmd[0])

        return subprocess.Popen(chroot_cmd, stdout=stdout, stderr=stderr)


if __name__ == "__main__":
    s = Sandbox("./.sandbox/")

    shutil.copy("/bin/ls", s.root_directory + "bin/")

    p = s.process(['.sandbox/bin/ls', '-l', '/'])
    p.wait()

    del s

