class State(object):
    """
    Base class for states
    """
    def __init__(self,owner):
        self.owner=owner

    def enter(self):
        pass
    
    def execute(self):
        pass

    def exit(self):
        pass

    def get_message(self,msg):
        return False
