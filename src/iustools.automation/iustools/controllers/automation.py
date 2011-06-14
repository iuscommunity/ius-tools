"""automation controller class to expose commands for iustools."""

from cement.core.controller import CementController, expose

from iustools.model.automation import AutomationModel

class AutomationController(CementController):
    @expose()              
    def automation_command(self):
        """Register root command that doesn't use a template."""
        foo = 'bar'
        
        # Even if you're not using a template, return relevant data so that
        # you can still use the --json engine, or similar.
        return dict(foo=foo)
          
    @expose()            
    def automation_command_help(self):
        """help methods are accessed as 'command-help'."""
        print "automation root command help method."

    @expose('iustools.templates.automation.automation_command')              
    def automation_command2(self, *args, **kw):
        """Register root command, with Genshi templating."""
        foo = "Hello"
        bar = "World"
        return dict(foo=foo, bar=bar)

    @expose(namespace='automation')              
    def automation_sub_command(self):
        """Register sub command for the automation namespace."""
        foo = 'bar'
        print foo
        return dict(foo=foo)

