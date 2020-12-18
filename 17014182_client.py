#17014182
from State import *
from socket import socket
from sys import argv
from time import sleep
#used for formating messages
import json
#to generate a random starting seq = random + 0 value
import random

#the list of transitions that can occur
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
    '''this is the starting state of the client mode, closed state'''
    def __init__(self, Context):
        State.__init__(self, Context)
    def rst(self):
        print("---------------------------")
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
        return True
    def active_open(self):
        print("At closed state!")
        #initiate connection process
        #and transition to Synsent state when connection made
        print("Contacting peer...")
        if self.CurrentContext.connection_address == 0: #for the client
            self.CurrentContext.make_connection()#connects to the server which was awaiting
        print("Connection made!")
        sleep(self.CurrentContext.sleep_time)#to slow the progress to be able to see the output
        print("Transitioning to Syn_sent!")
        self.CurrentContext.setState("Syn_sent")#once connection made, transitioning to syn_sent
        return True
    def trigger(self):#where the first transition will get triggered in the closed state
        print("---------------------------")
        print("At the Closed State!")
        return self.CurrentContext.rst()
        
class Syn_sent(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)
    def syn_ack(self):
        try:
            cmd = self.CurrentContext.socket.recv(1024)
            packet = json.loads(cmd.decode())
            if  packet["Flags"] == '[SYN, ACK]':#to receive the SYN+ACK
                print(packet," received!")
                #set the values correctly according to what is received
                self.CurrentContext.ack_value = packet["Seq"] + 1 #learns the sequence value
                self.CurrentContext.seq_value = packet ["Ack"]
                print("Transitioning to Established!")
                self.CurrentContext.setState("Established")#once syn+ack received, transition to established state occurs
                return True
            else:
                print("Did not receive SYN+ACK!")
                print("Wrong message received, expected SYN+ACK!")
                self.CurrentContext.rst()#rst will occur only if the wrong flag was received
                return False
        except Exception:
            print("Could not receive message!")
            self.CurrentContext.timeout()#timeout will only occur when no message is received
            return False
    def rst(self):
        print("Rst!")
        print("Transmissioning to Closed!")#transitions to closed state where the reset will get triggered
        self.CurrentContext.setState("Closed")
        return True
    def timeout(self):
        print("Timeout!")
        sleep(self.CurrentContext.sleep_time)#to simulate a timeout countdown
        print("Transmissioning to Closed!")
        self.CurrentContext.setState("Closed")
        return True
    def syn(self):
        try:
            m = {"Flags":"[SYN]","Seq": self.CurrentContext.seq_value}
            print(m, " Sent!")
            packet = json.dumps(m)
            self.CurrentContext.socket.send(packet.encode())
            self.CurrentContext.syn_ack()#once SYN is sent, the syn_ack transition will occur
            return True
        except Exception:
            print("Could not send SYN!")
            return False
    def trigger(self):
        print("---------------------------")
        print("At the Syn_sent State!")
        return self.CurrentContext.syn()#triggering syn transition firstly in the syn_sent state

class Established(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)
    def close(self):
        print("Transitioning to Fin_wait_1!")
        self.CurrentContext.setState("Fin_wait_1")
        return True
    def ack(self):
        try:
            m = {"Flags":"[ACK]","Seq": self.CurrentContext.seq_value, "Ack":self.CurrentContext.ack_value}
            print(m, " Sent!")
            packet = json.dumps(m)
            self.CurrentContext.socket.send(packet.encode())
            #for the communication of the message after the 3 way handshake
            try:
                cmd = self.CurrentContext.socket.recv(1024)
                packet = json.loads(cmd.decode())
                print(packet," received!")
                self.CurrentContext.ack_value = packet["Bytes"] + 1#receive the bytes plus 1 for ack value
                m = {"Flags":"[ACK]", "Ack":self.CurrentContext.ack_value}
                print(m, " Sent!")
                packet = json.dumps(m)
                self.CurrentContext.socket.send(packet.encode())
                return self.CurrentContext.close()
            except Exception:
                print("could not receive Message!")
                return False
        except Exception:
            print("Could not send ACK!")
            return False
    def trigger(self):#where the first transition will get triggered in the established state
        print("---------------------------")
        print("At the Established State!")
        return self.CurrentContext.ack()
       
class Fin_wait_1(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)
    def ack(self):
        try:
            cmd = self.CurrentContext.socket.recv(1024)
            packet = json.loads(cmd.decode())
            if  packet["Flags"] == '[ACK]':
                print(packet," received!")
                self.CurrentContext.seq_value = packet["Ack"] + 1
                self.CurrentContext.ack_value = packet["Seq"] + 1
                print("Transitioning to Fin_wait_2!")
                self.CurrentContext.setState("Fin_wait_2")
                return True
            else:
                print("ACK not received!")
                return False
        except Exception:
            print("could not receive ACK!")
            return False
    def fin(self):
        try:
            m = {"Flags":"[FIN]","Seq": self.CurrentContext.seq_value}
            print(m, " Sent!")
            packet = json.dumps(m)
            self.CurrentContext.socket.send(packet.encode())
            self.CurrentContext.ack()
            return True
        except Exception:
            print("could not send FIN!")
            return False
    def trigger(self):#where the first transition will get triggered in the fin wait 1 state
        print("---------------------------")
        print("At the Fin_wait_1 State!")
        return self.CurrentContext.fin()

class Fin_wait_2(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)
    def fin(self):
        try:
            cmd = self.CurrentContext.socket.recv(1024)
            packet = json.loads(cmd.decode())
            if  packet["Flags"] == '[FIN]':
                print(packet," received!")
                print("Transitioning to Timed_wait!")
                self.CurrentContext.setState("Timed_wait")
                return True
            else:
                print("FIN not received!")
                return False
        except Exception:
            print("could not receive FIN!")
            return False
    def trigger(self):#where the first transition will get triggered in the fin wait 2 state
        print("---------------------------")
        print("At the Fin_wait_2 State!")
        return self.CurrentContext.fin()

class Timed_wait(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)
    def timeout(self):
        print("At Timed_wait")
        print("Transitioning to Closed!")
        self.CurrentContext.setState("Closed")
        return True
    def ack(self):
        try:
            m = {"Flags":"[ACK]","Seq": self.CurrentContext.seq_value, "Ack":self.CurrentContext.ack_value}
            print(m, " Sent!")
            packet = json.dumps(m)
            self.CurrentContext.socket.send(packet.encode())
            self.CurrentContext.timeout()
            return True
        except Exception:
            print("could not send ACK!")
            return False
    def trigger(self):#where the first transition will get triggered in the timed wait state
        print("---------------------------")
        print("At the Timed_wait State!")
        return self.CurrentContext.ack()

class TCP_Client(StateContext, Transition):
    def __init__(self):
        self.sleep_time = 5 #used for timeout
        self.host = "127.0.0.1"
        self.port = 5000
        self.connection_address = 0
        #used for TCP
        self.random_value = random.randint(0,9)#random value to simulate the seq = random + 0
        self.seq_value = 123 + 0
        self.ack_value = 0
        self.socket = None
        #all the available states
        self.availableStates["Closed"] = Closed(self)
        self.availableStates["Syn_sent"] = Syn_sent(self)
        self.availableStates["Fin_wait_1"] = Fin_wait_1(self)
        self.availableStates["Fin_wait_2"] = Fin_wait_2(self)
        self.availableStates["Timed_wait"] = Timed_wait(self)
        self.availableStates["Established"] = Established(self)
        print("Transitioning to closed!")
        self.setState("Closed")#default starting state

    #all the used transitions
    def active_open(self):
        return self.CurrentState.active_open()
    def syn(self):
        return self.CurrentState.syn()
    def syn_ack(self):
        return self.CurrentState.syn_ack()
    def close(self):
        return self.CurrentState.close()
    def ack(self):
        return self.CurrentState.ack()
    def fin(self):
        return self.CurrentState.fin()
    def timeout(self):
        return self.CurrentState.timeout()
    def rst(self):
        return self.CurrentState.rst()
    def make_connection(self):
        '''this method initiates an outbound connection'''
        self.socket = socket()
        try:
            self.socket.connect((self.host, self.port))
            self.connection_address = self.host
        except Exception as err:
            print(err)
            exit()

if __name__ == '__main__':
    TCP = TCP_Client()
    print("Running in client mode!")
    TCP.active_open()#starting in the closed state, the active open transition