import pdb as debug

class MessageHandler(set):
    debug=False

    def __init__(self,dt):
        self.dt = dt

    def add(self,msg):
        if msg.delay < 0.:
            self.process_message(msg)
        else:
            super(MessageHandler,self).add(msg)

    def process_message(self,msg):
        msg.to.get_message(msg)

    def process(self):
        # We need these two extra sets to avoid set changing size during iteration.
        # Sometimes processing a message causes the reciever to send a new message.
        discards=set()
        process=self.copy()
        for msg in process:
            msg.delay -= self.dt
            if msg.delay <= 0.:
                self.process_message(msg)
                discards.add(msg)
        for msg in discards:
            self.discard(msg)        

class Message(object):
    
    def __init__(self,to,sender,subject,body=None,delay=0.):
        """
        Default delay will result in delivery on the next check. Set to negative to send immediately.
        """
        self.to=to
        self.sender=sender
        self.subject=subject
        self.body=body
        self.delay=delay
