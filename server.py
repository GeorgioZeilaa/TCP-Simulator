from State import *
from socket import socket
from sys import argv
from time import sleep
#used for formating messages
import json

#list of available transitions
class Transition:
    def passive_open(self):
        print("Error!")
        return False
    def syn(self):
        print("Error!")
        return False
    def ack(self):
        print("Error!")
        return False
    def rst(self):
        print("Error!")
        return False
    def syn_ack(self):
        print("Error!")
        return False
    def close(self):
        print("Error!")
        return False
    def fin(self):
        print("Error!")
        return False
    def timeout(self):
        print("Error!")
        return False
    def active_open(self):
        print("Error!")
        return False

class Closed(State, Transition):
    '''First state of the server side.'''
    def __init__(self, Context):
        State.__init__(self, Context)
    def rst(self):
        print("Current State: Closed, doing reset!")
        try:
            self.CurrentContext.socket.close() #attempt to terminate socket
            self.connection_address = 0 #reset address attribute
            #reset the ack and seq values
            self.CurrentContext.seq_value = 0
            self.CurrentContext.ack_value = 0
            print("Closing connection!")
            return True
        except: #no current connection
            return False
    def passive_open(self):#default starting transition when the program starts
        try:
            print("At Closed state and listening!")
            self.CurrentContext.listen() #server process to accept a connection
            print("Transitioning to Listen!")
            self.CurrentContext.setState("Listen")
            return True
        except:
            print("Connection failed to accept, transitioning back to closed!")
            self.CurrentContext.setState("Closed")
            return False
    def trigger(self):#gets triggered when entering the Closed state
        print("---------------------------")
        print("At the Closed State!")
        return self.CurrentContext.rst()

class Listen(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)
    def syn(self):
        try:
            cmd = self.CurrentContext.connection.recv(1024)#to receive the first flag of SYN
            packet = json.loads(cmd.decode())
            if  packet["Flags"] == '[SYN]':
                print(packet," received!")
                self.CurrentContext.ack_value = packet["Seq"] + 1 #learns the sequence number received and adds one to get it ready for the sending of the 
                print("Transitioning to Syn_recvd!")
                self.CurrentContext.setState("Syn_recvd")#once SYN successfully received, transitioning to syn_recvd state
                return True
            else:
                print("Syn not received!")
                return False
        except: #no current connection
            print("Could not receive SYN!")
            return False
    def trigger(self):#where the first transition will get triggered in the listen state
        print("---------------------------")
        print("At the Listen State!")
        return self.CurrentContext.syn()

class Syn_recvd(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)
    def ack(self):
        try:
            cmd = self.CurrentContext.connection.recv(1024)#to receive the ACK flag
            packet = json.loads(cmd.decode())
            if  packet["Flags"] == '[ACK]':
                print(packet," received!")
                #seting the values correctly for seq and ack values
                self.CurrentContext.seq_value = packet["Seq"]
                self.CurrentContext.ack_value = packet["Ack"]
                print("Transitioning to Established!")
                sleep(self.CurrentContext.sleep_time)#the end of the 3 way handshake
                self.CurrentContext.setState("Established")
                return True
            else:
                print("ACK not received!")
                return False
        except Exception:
            print("Could not receive ACK")
            self.CurrentContext.setState("Closed")
            return False
    def syn_ack(self):
        try:
            m = {"Flags":"[SYN, ACK]","Seq": self.CurrentContext.seq_value, "Ack": self.CurrentContext.ack_value}#sends SYN ACK to the client after receiving a SYN
            print(m, " Sent!")
            packet = json.dumps(m)#converting the packet to json format
            self.CurrentContext.connection.send(packet.encode())
            self.CurrentContext.ack()
            return True
        except Exception:
            print("Could not send SYN+ACK!")
            return False
    def trigger(self):#where the first transition will get triggered in the syn_recvd state
        print("---------------------------")
        print("At the Syn_recvd State!")
        return self.CurrentContext.syn_ack()

class Established(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)
    def fin(self):
        try:
            cmd = self.CurrentContext.connection.recv(1024)
            packet = json.loads(cmd.decode())
            if  packet["Flags"] == '[FIN]':
                print(packet," received!")
                self.CurrentContext.ack_value = packet["Seq"] + 1 #learns the sequence value
                print("Transitioning to Closed_wait!")
                self.CurrentContext.setState("Closed_wait")#once the FIN flag has been receive the closed wait state will occur
                return True
            else:
                print("FIN not received!")
                return False
        except Exception:
            print("could not receive FIN!")
            return False
    def trigger(self):#where the first transition will get triggered in the established state
        print("---------------------------")
        print("At the Established State!")
        bytes_value = len(self.CurrentContext.message.encode('utf-8'))#number of bytes in the message
        m = {"Message":self.CurrentContext.message,"Seq": self.CurrentContext.seq_value, "Bytes":bytes_value}
        print(m, " Sent!")
        packet = json.dumps(m)
        self.CurrentContext.connection.send(packet.encode())
        try:
            cmd = self.CurrentContext.connection.recv(1024)
            packet = json.loads(cmd.decode())
            if  packet["Flags"] == '[ACK]':
                print(packet," received!")
                sleep(self.CurrentContext.sleep_time)#the end of the message
                return self.CurrentContext.fin()#trigger the fin to receive the fin flag
            else:
                print("ACK not received!")
                return False
        except Exception:
            print("could not receive ACK!")
            return False

class Closed_wait(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)
    def close(self):
        print("Transitioning to Lack_ack!")
        self.CurrentContext.setState("Last_ack")
        return True
    def ack(self):
        try:
            m = {"Flags":"[ACK]","Seq": self.CurrentContext.seq_value, "Ack":self.CurrentContext.ack_value}
            print(m, " Sent!")
            packet = json.dumps(m)
            self.CurrentContext.connection.send(packet.encode())
            self.CurrentContext.close()#to trigger the close transition aftering sending the ack
            return True
        except Exception:
            print("could not send ACK!")
            return False
    def trigger(self):#where the first transition will get triggered in the closed wait state
        print("---------------------------")
        print("At the Closed_wait State!")
        return self.CurrentContext.ack()

class Last_ack(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)
    def ack(self):
        try:
            cmd = self.CurrentContext.connection.recv(1024)
            packet = json.loads(cmd.decode())#to convert the json format
            if  packet["Flags"] == '[ACK]':
                print(packet," received!")#final confirmation of the closing connection
                print("Transitioning to Closed!")
                self.CurrentContext.setState("Closed")
                return True
            else:
                print("ACK not received!")
                return False
        except Exception:
            print("could not receive ACK!")
            return False
    def fin(self):
        try:
            m = {"Flags":"[FIN]","Seq": self.CurrentContext.seq_value, "Ack":self.CurrentContext.ack_value}
            print(m, " Sent!")
            packet = json.dumps(m)
            self.CurrentContext.connection.send(packet.encode())
            self.CurrentContext.ack()#to trigger the transition of ack
            return True
        except Exception:
            print("could not send FIN!")
            return False
    def trigger(self):
        print("---------------------------")
        print("At the Last_ack State!")
        return self.CurrentContext.fin()

class TCP_Server(StateContext, Transition):
    def __init__(self):
        self.sleep_time = 5 #used for timeout
        self.host = "127.0.0.1"
        self.port = 5000
        self.connection_address = 0
        #used for TCP
        self.seq_value = 0
        self.ack_value = 0
        self.message = "Hello World!"
        self.socket = None
        #all of the avialable states to be used later to transition to
        self.availableStates["Closed"] = Closed(self)
        self.availableStates["Listen"] = Listen(self)
        self.availableStates["Syn_recvd"] = Syn_recvd(self)
        self.availableStates["Established"] = Established(self)
        self.availableStates["Closed_wait"] = Closed_wait(self)
        self.availableStates["Last_ack"] = Last_ack(self)
        print("Transitioning to closed!")
        self.setState("Closed")#the starting state is set

    #the transitions that will be used
    def passive_open(self):
        return self.CurrentState.passive_open()
    def syn(self):
        return self.CurrentState.syn()
    def ack(self):
        return self.CurrentState.ack()
    def syn_ack(self):
        return self.CurrentState.syn_ack()
    def rst(self):
        return self.CurrentState.rst()
    def fin(self):
        return self.CurrentState.fin()
    def close(self):
        return self.CurrentState.close()
    def listen(self):
        '''this method initiates a listen socket'''
        self.socket = socket()
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)
            self.connection, self.connection_address = self.socket.accept() #connection acceptance
            return True
        except Exception as err:
            print(err)
            exit()

if __name__ == '__main__':
    TCP = TCP_Server()
    print("Running in server mode!")
    TCP.passive_open()#the starting transition from closed which is passive open
