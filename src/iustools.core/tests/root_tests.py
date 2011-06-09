
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
def test_testing_age():  
    (res_dict, output_txt) = simulate([__file__, 'testing-age'])

    res = len(res_dict['packages']) > 0
    ok_(res)

@raises(IUSToolsArgumentError)
@with_setup(setup_func, teardown_func)
def test_default_cmd():
    # The default action is to raise an application error if an unknown 
    # command is called.  This is how we test that the exception is raised.
    simulate([__file__, 'default'])
