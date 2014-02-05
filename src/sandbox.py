
import os
import subprocess
import tempfile
import shutil
import sys


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
        if not os.path.isdir(self.root_directory):
            os.makedirs(self.root_directory)

        os.makedirs(self.tmp_directory)
        os.makedirs(self.root_directory + "bin/")

        # ---- dyld is very important
        os.makedirs(self.root_directory + "usr/lib/")
        shutil.copy2("/usr/lib/dyld", "{}usr/lib/".format(self.root_directory))

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

    def root_path(self, path):
        return "/" + os.path.relpath(os.path.abspath(path), os.path.abspath(self.root_directory))

    def process(self, cmd):
        chroot_cmd = list()
        chroot_cmd.extend(['sudo', 'chroot', self.root_directory])
        chroot_cmd.append(self.root_path(cmd[0]))
        chroot_cmd.extend(cmd[1:])

        self.fetches_dependencies(cmd[0])

        print chroot_cmd

        return subprocess.Popen(chroot_cmd)


if __name__ == "__main__":
    s = Sandbox("./.sandbox/")

    shutil.copy("/bin/ls", s.root_directory + "bin/")

    p = s.process(['.sandbox/bin/ls', '-l', '/'])
    p.wait()

    del s

