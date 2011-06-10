
from cement import namespaces
from cement.core.controller import expose as cement_expose
from cement.core.controller import CementController
from cement.core.log import get_logger
from cement.core.namespace import get_config
from cement.core.view import render

from iustools.core import irc_commands
from iustools.core.exc import IUSToolsRuntimeError
from iustools.core.connection import get_mf_connection

log = get_logger(__name__)
config = get_config()

class IUSToolsController(CementController):
    def __init__(self, cli_opts=None, cli_args=None):
        CementController.__init__(self, cli_opts, cli_args)
        self.cli_opts = cli_opts
        self.cli_args = cli_args
        self.mf = get_mf_connection(config['mf_connection'])
        
class expose(cement_expose):
    """
    Decorator function for plugins to expose commands.  This overrides
    the default cement 'expose()' decorator.  Used as:
    
    Arguments:
    
        template
            A template in python module form (i.e 'myapp.templates.mytemplate')
        namespace
            The namespace to expose the command in.  Default: root
        ircallow
            Allow this command to be exposed to the ircbot plugin
    
    Optional Keyword Arguments:
    
        is_hidden
            True/False whether command should display on --help.
    
    
    Usage:
    
    .. code-block:: python
    
        class MyController(CementController):
            @expose('myapp.templates.mycontroller.cmd', namespace='root')
            def cmd(self):
                foo="Foo"
                bar="Bar"
                return dict(foo=foo, bar=bar)
                
    """

    def __init__(self, template=None, namespace='root', **kwargs):
        # These get set in __call__
        self.func = None
        self.name = kwargs.get('name', None)
        self.template = template
        self.namespace = namespace
        self.tmpl_module = None
        self.tmpl_file = None
        self.config = namespaces['root'].config
        self.is_hidden = kwargs.get('is_hidden', False)
        self.desc = kwargs.get('desc', None)
        self.irc_command = kwargs.get('irc_command', None)
        
        if not self.namespace in namespaces:
            raise CementRuntimeError, \
                "The namespace '%s' is not defined!" % self.namespace
        
        # First set output_handler from config
        # DEPRECATION: output_engine
        self.output_handler = None
        if not self.config.has_key('output_handler'):
            if self.config.has_key('output_engine'):
                self.output_handler = self.config['output_engine']
        else:
            self.output_handler = self.config['output_handler']
        
        # The override output_handler from @expose()
        if self.template:
            parts = template.split(':')
            if len(parts) >= 2:
                self.output_handler = parts[0]
                self.template = parts[1]
            elif len(parts) == 1:
                self.template = parts[0]
            else:
                raise CementRuntimeError, "Invalid handler:template identifier."
                        
    def __get__(self, obj, type=None):
        if self.func:
            return self.__class__(self.func.__get__(obj, type))
        else:
            return self.__get__
        
    def __call__(self, func):
        parts = func.__module__.split('.')

        con_namespace = parts[-1]
        controller = parts[-2]
        base = '.'.join(parts[:-2])
        
        self.func = func
        if not self.name:
            self.name = self.func.__name__
        
        if not self.output_handler:
            log.debug("no output handler configured to generate output " + \
                      "for %s" % self.name)
            
        log.debug("exposing namespaces['%s'].commands['%s'] from '%s'" % \
                 (self.namespace, self.name, self.func.__module__))
                
        # First for the template
        if not self.name:
            self.name = self.func.__name__

        cmd = {
            'is_hidden' : self.is_hidden,
            'original_func' : func,
            'func' : self.name,
            'controller_namespace' : con_namespace,
            }

        # map irc commands to ius-tools commands
        if self.irc_command:
            irc_commands[self.irc_command] = dict(
                namespace=self.namespace, 
                controller_namespace=con_namespace,
                func=self.name
                )
                                              
        # Set the command info in the dest namespace
        namespaces[self.namespace].commands[self.name] = cmd
        self.func = render(self.output_handler, self.template)(self.func)
        return self.func