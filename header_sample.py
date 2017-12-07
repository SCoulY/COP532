from icns import Network, UI, FD_READY, NET_READY
import sys, os,signal, random, binascii, struct

class simple_reliability:
    def __init__(self):
        self.ack = '0'
        self.packetidlist = range(128)
        self.existlist = []

    def encapsulate(self,data):
        packetid = random.choice(list(set(self.packetidlist)-set(self.existlist)))
        self.existlist.append(packetid)
        header = self.ack + bin(packetid)[2:].zfill(7)
        encapsulate_data = header + data
        return header,encapsulate_data

    def decapsulate(self,data):
        decapsulate_data = data[8:]
        return decapsulate_data

    def send_ack(self,data,nh,n):
        self.ack = '1'
        ack_data = self.ack + data[1:]
        n.send(nh,ack_data)

def handler(signum,frame):
	x.stop()

def is_chinese_str(mystr):
	for x in mystr:
		if u'\u4e00' <= x <= u'\u9fff':
			return True
		return False

def txt2bit(input_text):
	if is_chinese_str(input_text):
		a = ''.join((format(ord(x),'016b') for x in input_text))
		chinese = True
	else:
		a =''.join((format(ord(x),'08b')for x in input_text))
		chinese = False
	if len(a)%792 == 0:
		num_packets = len(a)/792
	else:
		num_packets = len(a)/792+1
	return a,num_blocks,chinese

def control_strategy():
	if len(sys.argv) < 3:
		print "not gonna work"
		sys.exit()
	else:
		x = UI("test")
		num = int(sys.argv[1])
		neighbour = sys.argv[2].split(":")
		n1 = Network(num)
		n = n1.add_neighbour(neighbour[0],
		int(neighbour[1]))

	going = True
	fd = x.getfd()

	while going:
		signal.signal(signal.SIGINT,handler)
		r= n1.orfd(fd)
		if r == FD_READY:
			line = os.read(fd,100)
			x.addline('your msg:'+line)
			reliability = simple_reliability()
			data,num_packets,chinese = txt2bit(line)
			binary_header,encapsulate_data = reliability.encapsulate(data)
			x.addline('header:'+binary_header)
			packed_header = struct.pack('B',int(binary_header,2))
			send_data = packed_header+line
			n1.send(n,send_data)
			x.addline('encapsulate_data:'+send_data)
			if line == '/q':
				going = False
		elif r == NET_READY:
			line,source = n1.receive()
			x.addline('them:'+line)
			up = struct.unpack('B',line[:1])
			X.addline('recived header:'+bin(up[0])[2:].zfill(8))
	x.stop()

if __name__ == '__main__':
	control_strategy()

