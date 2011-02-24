"""iustools exception classes."""

class IustoolsError(Exception):
    """Generic errors."""
    def __init__(self, value, code=1):
        Exception.__init__(self)
        self.msg = value
        self.code = code
    
    def __str__(self):
        return self.msg
        
    def __unicode__(self):
        return unicode(self.msg)
                
class IustoolsConfigError(IustoolsError):
    """Config parsing and setup errors."""
    def __init__(self, value):
        code = 10
        IustoolsError.__init__(self, value, code)

class IustoolsRuntimeError(IustoolsError):
    """Runtime errors."""
    def __init__(self, value):
        code = 20
        IustoolsError.__init__(self, value, code)

class IustoolsArgumentError(IustoolsError):
    """Argument errors."""
    def __init__(self, value):
        code = 40
        IustoolsError.__init__(self, value, code)
