from icns import Network, UI, FD_READY, NET_READY, TIMEOUT
import sys, os,signal, random, binascii, struct, time

class simple_reliability:
    def __init__(self):
        self.ack = '0'
        self.packetidlist = range(128)
        self.msg_id_list = []

    def encapsulate(self,data):
        packetid = random.choice(list(set(self.packetidlist)-set(self.msg_id_list)))
        header = self.ack + bin(packetid)[2:].zfill(7)
        self.msg_id_list.append(header[1:])
        encapsulate_data = header + data
        return header,encapsulate_data

    def decapsulate(self,data):
        decapsulate_data = data[8:]
        return decapsulate_data

    def send_ack(self,data,nh,n):
        self.ack = '1'
        ack_data = self.ack + data[1:]
        n.send(nh,ack_data)

class Forwarding:
    def __init__(self,data):
        self.next_hop_dict = {3:3,9:9,'Defalut':11}
        self.lookup_dict = {3:'n1',11:'n2',9:'n3'}
        self.reversed_lookup_dict = {'n1':3,'n2':11,'n3':9}

    def next_hop(self,host_num):
        if int(self.data[8:12],2) == host_num:
            return False
        else:
            return self.next_hop_dict[int(data[12:16],2)]


    def lookup(self):
        global neighbour
        if neighbour == '131.231.115.27:2':
            neighbour_name = 'n1'
        return self.reversed_lookup_dict[neighbour_name]

    def encapsulate(self,data):
        global host_num
        next = next_hop(data,host_num)
        return bin(host_num)[2:].zfill(4) + bin(host_num)[2:].zfill(4) + data


class Full_reliability:
    def __init__(self):
        self.ack = '0'
        self.packetidlist = range(256)
        self.msg_id_list = []
        self.total_package_list = []

    def encapsulate(self,data):
        packetid = random.choice(list(set(self.packetidlist)-set(self.msg_id_list)))
        Msgid_header = struct.pack('B',packetid)
        num_packets,len_of_last_msg = self.segmentation(data)
        len_header = struct.pack('B',len_of_last_msg)
        for i in range(num_packets):
            current_data = data[:96]
            seq_header = struct.pack('B',i)
            if i != num_packets-1:
                flag_header = struct.pack('B',0) #end flag == 0
            else:
                flag_header = struct.pack('B',64) #end flag == 1
            self.total_package_list.append(flag_header+Msgid_header+seq_header+len_header+current_data)
            data = data[96:]
        self.msg_id_list.append(bin(packetid)[2:].zfill(8))
        return self.total_package_list

    def decapsulate(self,data):
        decapsulate_header = bin(struct.unpack('B',data[0])[0])[2:].zfill(8) + bin(struct.unpack('B',data[1])[0])[2:].zfill(8) + bin(struct.unpack('B',data[2])[0])[2:].zfill(8) + bin(struct.unpack('B',data[3])[0])[2:].zfill(8)
        return decapsulate_header

    def send_ack(self,data,nh,n):
        newheader = struct.pack('B',struct.unpack('B',data[0])[0]+128)
        ack_data = newheader + data[1:]
        n.send(nh,ack_data)

    def segmentation(self,data):
        if len(data)%96 == 0:
            num_packets = len(data)/96
            len_of_last_msg = 0
        else:
            num_packets = len(data)/96+1
            len_of_last_msg = len(data)//96
        return num_packets,len_of_last_msg



def handler(signum,frame):
    global x
    x.stop()

def is_chinese_str(mystr):
    for x in mystr:
        if u'\u4e00' <= x <= u'\u9fff':
            return True
        return False


def control_strategy():
    if len(sys.argv) < 3:
        print "not gonna work"
        sys.exit()
    else:
        global x
        x = UI("test")
        num = int(sys.argv[1])
        neighbour = sys.argv[2].split(":")
        n1 = Network(num, droprate=0.5, corruptrate=0)
        n = n1.add_neighbour(neighbour[0],int(neighbour[1]))

    going = True
    fd = x.getfd()
    send_data = False
    tries = 0
    global host_num
    host_num = 2
    reliability = Full_reliability()


    while going:
        signal.signal(signal.SIGINT,handler)
        r= n1.orfd(fd,timeout=0.2)
        if send_data!=False  and r == TIMEOUT: #if packet state exist
            if tries<5:
                x.addline('Packet send failed... resent')
                n1.send(n,send_data)
                tries += 1

        if r == FD_READY:
            x.addline('FD')
            line = os.read(fd,1000)

            packet_list = reliability.encapsulate(line)


            for send_pack in packet_list:
                n1.send(n,send_pack)
                tries = 0

                if line == '/q':
	            	going = False

            send_data = send_pack

        if r == NET_READY:
            x.addline('net')
            line,source = n1.receive()
            header = reliability.decapsulate(line)

            newid = header[8:16]
            # x.addline('New ID: ' + newid)

            if newid not in reliability.msg_id_list:
                #x.addline(newid)
                x.addline('them:'+line[4:])
                reliability.msg_id_list.append(newid)

            ack = header[0]
            end = header[1]
            x.addline('received ack:'+header[:8]+'###')
            if ack == '1':
                send_data = False #drop data
                tries = 0
                if end == '1':
                    reliability.msg_id_list = []
                    reliability.total_package_list = []
            else: #send ack_packet
                reliability.send_ack(line,n,n1)
                x.addline('sent ack')


#x.stop()

control_strategy()
