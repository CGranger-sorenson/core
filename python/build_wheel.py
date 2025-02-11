#!/usr/bin/env python3
# Copyright 2023, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#  * Neither the name of NVIDIA CORPORATION nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
# OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import argparse
import os
import pathlib
import re
import shutil
import subprocess
import sys
from distutils.dir_util import copy_tree
from tempfile import mkstemp


def fail_if(p, msg):
    if p:
        print("error: {}".format(msg), file=sys.stderr)
        sys.exit(1)


def mkdir(path):
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)


def touch(path):
    pathlib.Path(path).touch()


def cpdir(src, dest):
    copy_tree(src, dest, preserve_symlinks=1)


def sed(pattern, replace, source, dest=None):
    fin = open(source, "r")
    if dest:
        fout = open(dest, "w")
    else:
        fd, name = mkstemp()
        fout = open(name, "w")

    for line in fin:
        out = re.sub(pattern, replace, line)
        fout.write(out)

    fin.close()
    fout.close()
    if not dest:
        shutil.copyfile(name, source)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dest-dir", type=str, required=True, help="Destination directory."
    )
    parser.add_argument(
        "--binding-path", type=str, required=True, help="Path to Triton Python binding."
    )

    FLAGS = parser.parse_args()

    FLAGS.triton_version = None
    with open("TRITON_VERSION", "r") as vfile:
        FLAGS.triton_version = vfile.readline().strip()

    FLAGS.whl_dir = os.path.join(FLAGS.dest_dir, "wheel")

    print("=== Building in: {}".format(os.getcwd()))
    print("=== Using builddir: {}".format(FLAGS.whl_dir))
    print("Adding package files")
    mkdir(os.path.join(FLAGS.whl_dir, "tritonserver"))
    shutil.copy("tritonserver/__init__.py", os.path.join(FLAGS.whl_dir, "tritonserver"))
    # Type checking marker file indicating support for type checkers.
    # https://peps.python.org/pep-0561/
    shutil.copy("tritonserver/py.typed", os.path.join(FLAGS.whl_dir, "tritonserver"))
    cpdir("tritonserver/_c", os.path.join(FLAGS.whl_dir, "tritonserver", "_c"))
    cpdir("tritonserver/_api", os.path.join(FLAGS.whl_dir, "tritonserver", "_api"))
    PYBIND_LIB = os.path.basename(FLAGS.binding_path)
    shutil.copyfile(
        FLAGS.binding_path,
        os.path.join(FLAGS.whl_dir, "tritonserver", "_c", PYBIND_LIB),
    )

    shutil.copyfile("LICENSE.txt", os.path.join(FLAGS.whl_dir, "LICENSE.txt"))
    shutil.copyfile("setup.py", os.path.join(FLAGS.whl_dir, "setup.py"))
    shutil.copyfile("pyproject.toml", os.path.join(FLAGS.whl_dir, "pyproject.toml"))

    os.chdir(FLAGS.whl_dir)
    print("=== Building wheel")
    args = ["python3", "-m", "build"]

    wenv = os.environ.copy()
    wenv["VERSION"] = FLAGS.triton_version
    wenv["TRITON_PYBIND"] = PYBIND_LIB
    p = subprocess.Popen(args, env=wenv)
    p.wait()
    fail_if(p.returncode != 0, "Building wheel failed failed")

    cpdir("dist", FLAGS.dest_dir)

    print("=== Output wheel file is in: {}".format(FLAGS.dest_dir))
    touch(os.path.join(FLAGS.dest_dir, "stamp.whl"))
