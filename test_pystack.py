from __future__ import absolute_import

import sys
import subprocess
import platform
import time

from pytest import fixture, mark, param
from distutils.spawn import find_executable
from click.testing import CliRunner

from pystack import cli_main, tolerate_missing_locale


skipif_non_gdb = mark.skipif(
    not find_executable('gdb'), reason='gdb not found')
skipif_non_lldb = mark.skipif(
    not find_executable('lldb'), reason='lldb not found')
skipif_darwin = mark.skipif(
    platform.system().lower() == 'darwin', reason='gdb on darwin is unstable')


STATEMENTS = {
    'sleep': '__import__("time").sleep(360)',
}


@fixture
def process(request):
    args = [sys.executable, '-c', request.param]
    process = subprocess.Popen(args)
    try:
        time.sleep(1)
        yield process
    finally:
        process.terminate()
        process.wait()


@fixture
def cli():
    tolerate_missing_locale()
    return CliRunner()


@mark.parametrize(('process', 'debugger'), [
    param(STATEMENTS['sleep'], 'gdb', marks=[skipif_non_gdb, skipif_darwin]),
    param(STATEMENTS['sleep'], 'lldb', marks=skipif_non_lldb),
], indirect=['process'])
def test_smoke(cli, process, debugger):
    result = cli.invoke(cli_main, [str(process.pid), '--debugger', debugger])
    assert not result.exception
    assert result.exit_code == 0
    assert '  File "<string>", line 1, in <module>\n' in result.output
