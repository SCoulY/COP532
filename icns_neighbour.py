
import icns
import os
import threading
import signal
from multiprocessing import Pool,Process
#threads = 2
#n = icns.Network(112)
#nh=n.add_neighbour("131.231.114.78",111)
#ui = icns.UI('Chat room')
#uid = ui.getfd()

def receive():
    while 1:
        rec_msg = n.receive()
        ui.addline(rec_msg)
    
def send():
	msg = os.read(uid,100)
	if msg:
		n.send(nh,msg)
        
def handler(signum,frame):
	os.close(uid)    
	p.terminate()
	n.remove()
    
if __name__ == '__main__':
    threads = 2
    n = icns.Network(112)
    nh=n.add_neighbour("131.231.114.78",111)
    ui = icns.UI('Chat room')
    uid = ui.getfd()
    rec_msg = ''
    p = Process(target=receive,args=())
    p.start()
    while 1:
#        p.join()
        send()
        signal.signal(signal.SIGINT,handler)
        


