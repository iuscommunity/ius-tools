"""IUSTools exception classes."""

class IUSToolsError(Exception):
    """Generic errors."""
    def __init__(self, value, code=1):
        Exception.__init__(self)
        self.msg = value
        self.code = code
    
    def __str__(self):
        return self.msg
        
    def __unicode__(self):
        return unicode(self.msg)
                
class IUSToolsConfigError(IUSToolsError):
    """Config parsing and setup errors."""
    def __init__(self, value):
        code = 10
        IUSToolsError.__init__(self, value, code)

class IUSToolsRuntimeError(IUSToolsError):
    """Runtime errors."""
    def __init__(self, value):
        code = 20
        IUSToolsError.__init__(self, value, code)

class IUSToolsArgumentError(IUSToolsError):
    """Argument errors."""
    def __init__(self, value):
        code = 40
        IUSToolsError.__init__(self, value, code)
