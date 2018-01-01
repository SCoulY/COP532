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
    def __init__(self):
        self.next_hop_dict = {3:3,9:9,'Defalut':11}
        self.lookup_dict = {3:'131.231.114.82:1',11:'n2',9:'n3'}
        self.reversed_lookup_dict = {'131.231.114.82:1':3,'n2':11,'n3':9}

    def next_hop(self,dest):
        if 2 == dest:
            return False
        else:
            return self.next_hop_dict[dest]

    def lookup(self,neighbour_num):
        #if neighbour == '131.231.115.27:1':
            #neighbour_name = 'n2' #left handside host 
        neighbour_addr = self.lookup_dict[neighbour_num]
        return neighbour_addr


    def encapsulate(self,dest,data):
        global host_num
        next = self.next_hop(dest)
        return struct.pack('B',(host_num<<4)+next) + data

    def decapsulate(self,data):
        decapsulate_header = bin(struct.unpack('B',data[0])[0])[2:].zfill(8)
        return decapsulate_header


class Full_reliability:
    def __init__(self):
        self.ack = '0'
        self.packetidlist = range(256)
        self.unique_id_list = []
        self.msg_id_list = []
        self.total_package_list = []

    def encapsulate(self,data):
        packetid = random.choice(list(set(self.packetidlist)-set(self.msg_id_list)))
        Msgid_header = struct.pack('B',packetid)
        num_packets,len_of_last_msg = self.segmentation(data)
        #len_header = struct.pack('B',len_of_last_msg)
        for i in range(num_packets):
            current_data = data[:96]
            seq_header = struct.pack('B',i)
            if i != num_packets-1:
                flag_header = struct.pack('B',0) #end flag == 0
            else:
                flag_header = struct.pack('B',64) #end flag == 1
            self.total_package_list.append(flag_header+Msgid_header+seq_header+current_data)
            data = data[96:]
        self.msg_id_list.append(bin(packetid)[2:].zfill(8))
        self.unique_id_list.append(bin(packetid)[2:].zfill(8)+bin(i)[2:].zfill(8))
        return self.total_package_list

    def decapsulate(self,data):
        decapsulate_header = bin(struct.unpack('B',data[0])[0])[2:].zfill(8)+bin(struct.unpack('B',data[1])[0])[2:].zfill(8) + bin(struct.unpack('B',data[2])[0])[2:].zfill(8)
        return decapsulate_header

    def send_ack(self,data,nh,n):
        newheader = struct.pack('B',struct.unpack('B',data[1])[0]+128)
        ack_data = data[0] + newheader + data[2:]
        n.send(nh,ack_data)

    def segmentation(self,data):
        if len(data)%96 == 0:  #need modification
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
        Dest = sys.argv[2].split(":")
        my_host = Network(num, droprate=0.2, corruptrate=0)
        forwarding = Forwarding()
        next = forwarding.reversed_lookup_dict[sys.argv[2]]
        next = forwarding.next_hop(next)
        addr,port = Dest[0],Dest[1]
        n = my_host.add_neighbour(addr,int(port))

    going = True
    fd = x.getfd()
    send_data = {}
    tries = 0
    global host_num
    host_num = 2
    reliability = Full_reliability()


    while going:
        signal.signal(signal.SIGINT,handler)
        r= my_host.orfd(fd,timeout=0.2)
        if send_data!={}  and r == TIMEOUT: #if packet state exist
            if tries<5:
                x.addline('Packet send failed... resent')
                for key in send_data.keys():
                    checksum_data = forwarding.encapsulate(next,send_data[key])
                    my_host.send(n,checksum_data)
                tries += 1

        if r == FD_READY:
            x.addline('FD')
            line = os.read(fd,300)

            packet_list = reliability.encapsulate(line)


            for send_pack in packet_list:
                checksum_data = forwarding.encapsulate(next,send_pack)
               
                my_host.send(n,checksum_data)
                tries = 0
                unique_id = bin(struct.unpack('B',send_pack[1])[0])[2:].zfill(8) + bin(struct.unpack('B',send_pack[2])[0])[2:].zfill(8)
                send_data.update({unique_id:send_pack})
                if line == '/q':
	            	going = False

            

        if r == NET_READY:
            x.addline('net')
            line,source = my_host.receive()
            header = forwarding.decapsulate(line[0]) + reliability.decapsulate(line[1:4])

            ack = header[8]
            end = header[9]
            
            dest_host = int(header[4:8],2)
            source_host = int(header[:4],2)
            unique_id = header[16:32]

            if ack!='1' and unique_id not in reliability.unique_id_list:
                x.addline('them:'+line[4:])
                reliability.unique_id_list.append(unique_id)

            x.addline('received ack:'+header[8:16]+'###')
            if ack == '1':

                send_data.pop(unique_id) #drop data
                tries = 0
                if end == '1':
                    reliability.unique_id_list = []
                    reliability.msg_id_list = []
                    reliability.total_package_list = []
            else: #send ack_packet
                reliability.send_ack(line,n,my_host)
                x.addline('sent ack')
            if source_host != host_num and dest_host != host_num:
                next = forwarding.next_hop(dest_host)
                if next != False:
                    neighbour_addr = forwarding.lookup(next)
                    addr,port = neighbour_addr.split(':')
                    n = my_host.add_neighbour(addr,int(port)) 
                my_host.send(n,line)


#x.stop()

control_strategy()
