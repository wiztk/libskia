#!/usr/bin/env python3

"""A python script to build libskia

This script follow the instructions on

    - https://skia.org/user/download
    - https://skia.org/user/build

to build a static Skia library by the tools provided in depot_tools and skia repos.

"""

import sys
import os
import platform
import subprocess
import pathlib
import tarfile

from contextlib import contextmanager
from shutil import copy2, rmtree
from distutils.dir_util import copy_tree

CC = "clang"
CXX = "clang++"
IS_OFFICIAL_BUILD = True
IS_DEBUG = False

NAME = 'libskia'
VERSION = 'm63'
ARCH = platform.processor()


@contextmanager
def scoped_cwd(path):
    cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(cwd)


def get_root_path():
    return os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


def set_environment():
    depot_tools_dir = os.path.join(get_root_path(), 'third_party', 'depot_tools')
    os.environ['PATH'] = depot_tools_dir + ":" + os.environ['PATH']


def sync_deps():
    with scoped_cwd(get_root_path()):
        os.chdir(os.path.join('third_party', 'skia'))
        result = subprocess.run(["python", "tools/git-sync-deps"])
    return result


def generate_ninja_project():
    """Generate ninja project with gn command

    This function always generate ninja project in 'third_party/skia/out/Release'

    :return: A CompletedProcess object, check the boolean value
    """
    with scoped_cwd(get_root_path()):
        os.chdir(os.path.join('third_party', 'skia'))
        arg_list = []

        if IS_DEBUG is True:
            arg_list.append("is_debug=true")
        else:
            arg_list.append("is_debug=false")

        arg_list.append("cc=\"%s\"" % CC)
        arg_list.append("cxx=\"%s\"" % CXX)

        if IS_OFFICIAL_BUILD is True:
            arg_list.append("is_official_build=true")
        else:
            arg_list.append("is_official_build=false")

        command = "bin/gn gen out/Release --args='%s'" % (' '.join(arg_list))
        result = subprocess.run(command, shell=True)

    return result


def build_ninja_project():
    """Build the ninja project generated in 'third_party/skia/out/Release'

    :return: A CompletedProcess object
    """
    with scoped_cwd(get_root_path()):
        os.chdir(os.path.join('third_party', 'skia'))
        result = subprocess.run(["ninja", "-C", "out/Release"])
    return result


def make_tarball(srcdir, filename):
    with tarfile.open(filename, 'w:gz') as tar:
        tar.add(srcdir, arcname=os.path.basename(srcdir))


def package():
    """Package and make a tarball
    """
    with scoped_cwd(get_root_path()):
        tmp_dir = 'out'
        if os.path.exists(tmp_dir):
            rmtree(tmp_dir)
        sub_folder = "%s-%s-%s" % (NAME, VERSION, ARCH)
        dst = tmp_dir + '/' + sub_folder
        pathlib.Path(dst + '/lib').mkdir(parents=True, exist_ok=True)
        pathlib.Path(dst + '/include').mkdir(parents=True, exist_ok=True)
        copy2('third_party/skia/out/Release/libskia.a', dst + '/lib')
        copy_tree('third_party/skia/include', dst + '/include')

        os.chdir('out')
        make_tarball(sub_folder, sub_folder + '.tar.gz')


def main():
    set_environment()
    if not sync_deps():
        return 1
    if not generate_ninja_project():
        return 1
    if not build_ninja_project():
        return 1
    package()
    return 0


if __name__ == '__main__':
    sys.exit(main())
