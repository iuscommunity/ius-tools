"""
This is the application's core code.  Unless you know the "ins-and-outs" of
The Cement CLI Application Framework, you probably should not modify the 
main() function of this file.

"""

import sys
from pkg_resources import get_distribution

from cement.core.exc import CementArgumentError, CementConfigError
from cement.core.exc import CementRuntimeError
from cement.core.log import get_logger
from cement.core.app_setup import lay_cement
from cement.core.command import run_command

from iustools.core.config import default_config
from iustools.core.exc import IustoolsArgumentError, IustoolsConfigError
from iustools.core.exc import IustoolsRuntimeError

VERSION = get_distribution('iustools').version
BANNER = """
iustools version %s
""" % VERSION

def main(args=None):
    try:
        if not args:
            args = sys.argv
            
        lay_cement(config=default_config, banner=BANNER, args=args, 
                   version=VERSION)
    
        log = get_logger(__name__)
        log.debug("Cement Framework Initialized!")

        if not len(args) > 1:
            args.append('default')
        
        run_command(args[1])
            
    except CementArgumentError, e:
        # Display the apps exception names instead for the Cement exceptions.
        print("IustoolsArgumentError > %s" % e)
        sys.exit(e.code)
    except CementConfigError, e:
        print("IustoolsConfigError > %s" % e)
        sys.exit(e.code)
    except CementRuntimeError, e:
        print("IustoolsRuntimeError > %s" % e)
        sys.exit(e.code)
    except IustoolsArgumentError, e:
        print("IustoolsArgumentError > %s" % e)
        sys.exit(e.code)
    except IustoolsConfigError, e:
        print("IustoolsConfigError > %s" % e)
        sys.exit(e.code)
    except IustoolsRuntimeError, e:
        print("IustoolsRuntimeError > %s" % e)
        sys.exit(e.code)
    sys.exit(0)
   
def nose_main(args, test_config):
    """
    This function provides an alternative to main() that is more friendly for 
    nose tests as it doesn't catch any exceptions.
    
    Required Arguments:
        
        args
            The args to pass to lay_cement
        
        test_config
            A test config to pass to lay_cement
    
    Usage:
    
    .. code-block:: python
    
        from iustools.core.appmain import nose_main
        from iustools.core.config import get_nose_config
        
        args = [__file__, 'nosetests', '--quiet']
        (res_dict, output_text) = nose_main(args, get_nose_config())
        
    """
    
    lay_cement(config=test_config, banner=BANNER, args=args)
    log = get_logger(__name__)
    log.debug("Cement Framework Initialized!")

    if not len(args) > 1:
        args.append('default')

    (res, output_txt) = run_command(args[1])
    return (res, output_txt)
         
if __name__ == '__main__':
    main()
    
