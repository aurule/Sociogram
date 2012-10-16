class AttrError(Exception):
    '''Exception for attribute conflicts.'''
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class MissingNode(Exception):
    '''Exception for missing nodes.'''
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
