#from abc import ABC, abstractmethod

class CinemaProcessor(object):
    def __init__(self, host, port):
        self.destination = host
        self.port = port
        self.socket = None

    #@abstractmethod
    def getState(self):
        pass

    #@abstractmethod
    def connect(self):
        pass

    #@abstractmethod
    def disconnect(self):
        pass

    #@abstractmethod
    def send(self, command):
        pass

    # This will probably need to be overridden, but it works for Dolby Cinema processors
    # A response string is split by spaces and the last element (the response data) is returned.
    # If it's an number, it's cast as an integer first.
    # Return True if both values are numbers, False if there was an issue (like a timeout)
    def stripvalue(self, responseText):
        value = responseText.strip().split(" ")[-1]
        if (value.isdigit()):
            return int(value)
        else:
            return value

    def addfader(self, value=1):
        currentFader = self.getfader()
        if(isinstance(value, int) and isinstance(currentFader, int)):
            newFader = currentFader + value
            if(newFader<0):
                self.setfader(0)
            elif(newFader>100):
                self.setfader(100)
            else:
                self.setfader(newFader)
            return True
        else:
            return False

    #@abstractmethod
    def getfader(self):
        pass

    #@abstractmethod
    def setfader(self, value):
        pass

    #@abstractmethod
    def setmute(self, mute=1):
        pass

    #@abstractmethod
    def getmute(self):
        pass

    #@abstractmethod
    def displayfader(self):
        pass
