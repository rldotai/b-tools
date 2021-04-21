"""
Common functions for various modules
"""
import shutil
import subprocess
import sys


def is_executable(name):
    """Check whether `name` is on PATH and marked as executable."""
    name = str(name)
    return shutil.which(name) is not None

def doit_live(cmd):
    """Execute a command and read from its stdout/stderr as it becomes available.

    From: https://stackoverflow.com/a/4417735
    """
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # Poll process for new output until finished
    while True:
        nextline = process.stdout.readline()
        if nextline == '' and process.poll() is not None:
            break
        sys.stdout.write(nextline.decode())
        sys.stdout.flush()

    output = process.communicate()[0]
    exitCode = process.returncode

    if (exitCode == 0):
        return output
    else:
        raise ProcessException(command, exitCode, output)
