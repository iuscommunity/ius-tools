"""
The purpose of this module is to test plugin functionality.  It is here
as an example of how one might perform nose testing on an application built
on top of the Cement Framework.  It is not a fully comprehensive test, of the
application... and needs to be expanded as the application and plugin grow.

The initial file loaded by nose runs the application.  Additional calls are
then made via the 'simulate' function rather than needing to reload the 
application for every test.
"""

import os
from nose.tools import raises, with_setup, eq_, ok_

from cement import namespaces
from cement.core.namespace import get_config
from cement.core.testing import simulate
from cement.core.exc import CementRuntimeError

from iustools.core.exc import IUSToolsArgumentError

config = get_config()
    
def setup_func():
    """Setup operations before every test."""
    pass

def teardown_func():
    """Teardown operations after every test."""
    pass
    
@with_setup(setup_func, teardown_func)
def test_default_cmd():
    args = [
        __file__, 'version_tracker', 'default', 
        '--release=5']
    (out_dict, out_txt) = simulate(args)

@with_setup(setup_func, teardown_func)
def test_default_cmd_with_filter():
    args = [
        __file__, 'version_tracker', 'default', 
        '--filter=php',
        '--release=5']
    (out_dict, out_txt) = simulate(args)
    res = len(out_dict['packages']) > 1
    ok_(res)
    
    args = [
        __file__, 'version_tracker', 'default', 
        '--filter=bogus_filter',
        '--release=5']
    (out_dict, out_txt) = simulate(args)
    res = len(out_dict['packages']) == 0
    ok_(res)
    
@with_setup(setup_func, teardown_func)
def test_default_cmd_with_package():
    args = [
        __file__, 'version_tracker', 'default', 
        '--package=php52',
        '--release=5']
    (out_dict, out_txt) = simulate(args)
    res = len(out_dict['packages']) == 1
    ok_(res)
    
    args = [
        __file__, 'version_tracker', 'default', 
        '--package=php52',
        '--release=4']
    (out_dict, out_txt) = simulate(args)
    res = len(out_dict['packages']) == 1
    ok_(res)
    
    args = [
        __file__, 'version_tracker', 'default', 
        '--package=bogus_package',
        '--release=5']
    (out_dict, out_txt) = simulate(args)
    res = len(out_dict['packages']) == 0
    ok_(res)

