#!/usr/bin/env python3
"""
cc-speak launcher: uses sys.executable to run stop-speak.py with the same
Python interpreter that was used to invoke this script, regardless of whether
the system calls it 'python3' or 'python'.
"""
import os
import subprocess
import sys

script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stop-speak.py")
stdin_data = sys.stdin.buffer.read()

subprocess.run(
    [sys.executable, script],
    input=stdin_data,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
