"""Core methods for determine the connection (server, user, token, etc)."""

import os
from urllib2 import HTTPError, URLError
from configobj import ConfigObj

from cement.core.log import get_logger
from cement.core.namespace import get_config

from mf.core.exc import MFConfigError

from monkeyfarm.interface import MFInterface, MFAPIKeyRequestHandler

log = get_logger(__name__)
                 
def get_mf_connection(con_name='default'):
    """
    Get a connection from the config.  Use 'default' if no connection name is
    supplied.
    
    Optional Arguments:
    
        con_name
            The name of the connection.  The primary configuration should have
            a config block such as '[connection:default]' that has the 
            settings of the default connection.  Other connections can be set
            such as '[connection:my-mf-environment]' in which case this 
            function would be called with 'my-mf-environment' as the 
            con_name parameter.
            
    Usage:
    
    .. code-block:: python
    
        from mf.core.connection import get_connection
        hub = get_connection()
        
    """
    if not con_name:
        con_name = 'default'
        
    hub = None

    # use monkeyfarm configs
    config_files = [
        '/etc/monkeyfarm/mf.conf', 
        os.path.join(os.path.abspath(os.environ['HOME']), '.mf.conf')
        ]
        
    for _file in config_files:
        if not os.path.exists(_file):
            continue

        c = ConfigObj(_file)    
        for sect in c.sections:
            if sect.startswith('connection:'):
                try:
                    assert c[sect].has_key('user'), \
                        "Missing 'user' setting in %s (%s)." % (_file, sect)
                    assert c[sect].has_key('api_key'), \
                        "Missing 'api_key' setting in %s (%s)." % (_file, sect)
                    assert c[sect].has_key('url'), \
                        "Missing 'url' setting in %s (%s)." % (_file, sect)    
                except AssertionError, e:
                    raise MFConfigError, e.args[0]
                    
                name = sect.split(':')[1]
                if name == con_name:
                    api_key = "%s:%s" % (c[sect]['user'],
                                         c[sect]['api_key'])
                    url = c[sect]['url']
                    try:
                        rh = MFAPIKeyRequestHandler(url)
                        rh.auth(c[sect]['user'], c[sect]['api_key'])
                        hub = MFInterface(request_handler=rh)
                        return hub
                    except HTTPError, e:
                        raise MFConfigError, \
                            "Unable to connect to '%s'.  %s %s." % \
                            (url, e.code, e.msg)
                    except URLError, e:
                        raise MFConfigError, \
                            "Unable to connect to '%s'.  %s." % \
                            (url, e.args[0])
    if not hub:
        raise MFConfigError, "Unknown connection '%s'." % con_name