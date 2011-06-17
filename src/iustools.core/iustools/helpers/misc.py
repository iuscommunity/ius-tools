
from cement.core.log import get_logger

from subprocess import Popen, PIPE
from iustools.core import exc

log = get_logger(__name__)

def exec_command(cmd_args):
    """
    Quick wrapper around subprocess to exec shell command and bail out if the
    command return other than zero.
   
    Required Arguments:
   
        cmd_args
            The args to pass to subprocess.

   
    Usage:
   
    .. code-block:: python
   
        from mf.helpers.misc import exec_command
        (stdout, stderr) = exec_command(['ls', '-lah'])

    """
    log.debug("exec_command: %s" % ' '.join(cmd_args))
    proc = Popen(cmd_args, stdout=PIPE, stderr=PIPE, shell=True)
    (stdout, stderr) = proc.communicate()
    if proc.wait():
        # call return > 0
        raise exc.IUSToolsRuntimeError, \
            "shell command exited with code '%s'. STDERR: %s" % \
            (proc.returncode, stderr)
    return (stdout, stderr)