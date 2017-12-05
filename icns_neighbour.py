
import icns
import os,sys
import threading
import signal
import random
from multiprocessing import Pool,Process
#threads = 2
#n = icns.Network(112)
#nh=n.add_neighbour("131.231.114.104",111)
#ui = icns.UI('Chat room')
#uid = ui.getfd()

class reliability:
    def __init__(self):
        self.ack = '0'
        self.msgidlist = range(128)
        self.existlist = []
        self.seq_num = 0
        
    def encapsulate(self,data):
        msgid = random.choice(list(set(self.msgidlist)-set(self.existlist)))
        self.existlist.append(msgid)
        header = self.ack + bin(self.msgidlist)[2:].zfill(7)
        self.seq_num += 1
        encapsulate_data = header + data
        return encapsulate_data
    
    def decapsulate(self,data):
        decapsulate_data = data[24:]
        return decapsulate_data
    
    def send_ack(self,data,nh,n):
        self.ack = '1'
        ack_data = self.ack + data[1:]  
        n.send(nh,ack_data)
    
    
    
    def set_to_default():
        
def receive():
    while 1:
        rec_msg = n.receive()
#        if rec_msg 
        ui.addline(rec_msg)
    
def send():
	msg = os.read(uid,100)
	if msg:
		n.send(nh,msg)
        
def handler(signum,frame):
#    n.remove()
    ui.stop()
    p.terminate()
        
    
if __name__ == '__main__':
    threads = 2
    netnumber = int(sys.argv[1])
    neighbour = sys.argv[2].split(":")
    n = icns.Network(netnumber)
    nh=n.add_neighbour(neighbour[0],int(neighbour[1]))
    ui = icns.UI('Chat room')
    uid = ui.getfd()
    rec_msg = ''
    p = Process(target=receive,args=())
    p.start()
    while 1:
#        p.join()
        signal.signal(signal.SIGINT,handler)
        send()
        
        


