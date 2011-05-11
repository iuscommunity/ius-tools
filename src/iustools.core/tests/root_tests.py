
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
def test_package_repo():  
    (res_dict, output_txt) = simulate([__file__, 'package-repo', 'php52'])
    eq_(res_dict['irc_data'], 
        'https://code.launchpad.net/~ius-coredev/ius/php52')
    
@with_setup(setup_func, teardown_func)
def test_bug():  
    (res_dict, output_txt) = simulate([__file__, 'bug', '731697'])
    eq_(res_dict['irc_data'], 
        'LP#731697 - php53 for ius-6 - https://bugs.launchpad.net/bugs/731697')

@with_setup(setup_func, teardown_func)
def test_changelog():  
    (res_dict, output_txt) = simulate([__file__, 'changelog', 'php52'])

    res = '%changelog' in res_dict['changelog']
    ok_(res)

@with_setup(setup_func, teardown_func)
def test_spec():  
    (res_dict, output_txt) = simulate([__file__, 'spec', 'ius-release'])

    res = 'ius-release' in res_dict['spec']
    ok_(res)
            
@raises(IUSToolsArgumentError)
@with_setup(setup_func, teardown_func)
def test_default_cmd():
    # The default action is to raise an application error if an unknown 
    # command is called.  This is how we test that the exception is raised.
    simulate([__file__, 'default'])