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

class Checksum:
    def __init__(self):
        self.sum = 0
        self.check_header = 0
        self.len_header = 0

    def cal_checksum_header(self,data,len_of_last_msg): #now data should have a mixed header of 4 bytes and 94 bytes original data
        self.sum = 0
        for byte in data:
            self.sum = self.sum + struct.unpack('B',byte)[0]
        self.check_header = self.sum%256
        self.len_header = len_of_last_msg
        return struct.pack('B',self.check_header) + struct.pack('B',self.len_header)

    def encapsulate(self,data,len_of_last_msg):
        return self.cal_checksum_header(data,len_of_last_msg)+data

    def decapsulate(self,data):
        checksumheader = bin(struct.unpack('B',data[0])[0])[2:].zfill(8) + bin(struct.unpack('B',data[1])[0])[2:].zfill(8)
        return checksumheader

class Forwarding:
    def __init__(self):
        self.next_hop_dict = {3:3,9:9,'Defalut':11}
        self.lookup_dict = {3:'131.231.114.82:1',9:'131.231.115.148:1'}
        self.reversed_lookup_dict = {'n2':3,'n1':9}

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
        return struct.pack('B',(host_num<<4)+dest) + data

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
        self.total_package_list = []
        packetid = random.choice(list(set(self.packetidlist)-set(self.msg_id_list)))
        Msgid_header = struct.pack('B',packetid)
        num_packets,len_of_last_msg = self.segmentation(data)
        #len_header = struct.pack('B',len_of_last_msg)
        for i in range(num_packets):
            current_data = data[:94]
            seq_header = struct.pack('B',i)
            if i != num_packets-1:
                flag_header = struct.pack('B',0) #end flag == 0
            else:
                flag_header = struct.pack('B',64) #end flag == 1
            self.total_package_list.append(flag_header+Msgid_header+seq_header+current_data)
            data = data[94:]
        self.msg_id_list.append(bin(packetid)[2:].zfill(8))
        self.unique_id_list.append(bin(packetid)[2:].zfill(8)+bin(i)[2:].zfill(8))
        return self.total_package_list,len_of_last_msg

    def decapsulate(self,data):
        decapsulate_header = bin(struct.unpack('B',data[0])[0])[2:].zfill(8)+bin(struct.unpack('B',data[1])[0])[2:].zfill(8) + bin(struct.unpack('B',data[2])[0])[2:].zfill(8)
        return decapsulate_header

    def send_ack(self,data,nh,n,dest):
        global host_num
        newheader = struct.pack('B',struct.unpack('B',data[3])[0]+128)
        #newsender = struct.pack('B',(host_num<<4)+dest)
        ack_data = data[:3]  + newheader + data[4:]
        n.send(nh,ack_data)

    def segmentation(self,data):
        if len(data)%94 == 0:  #need modification
            num_packets = len(data)/94
            len_of_last_msg = 0
        else:
            num_packets = len(data)/94+1
            len_of_last_msg = len(data)%94
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
        Dest = int(sys.argv[2])
        my_host = Network(num, droprate=0.2, corruptrate=0)
        forwarding = Forwarding()
        #next = forwarding.reversed_lookup_dict[sys.argv[2]]
        next = forwarding.next_hop(Dest)
        #add all the neighbours
        n1 = my_host.add_neighbour('131.231.115.148',1)
        n2 = my_host.add_neighbour('131.231.114.82',1)
        if next: #if dest is not this host
            neighbour_addr = forwarding.lookup(next)
            if neighbour_addr == '131.231.114.82:1':
                n = n2
            elif neighbour_addr == '131.231.115.148:1':
                n = n1

    going = True
    fd = x.getfd()
    send_data = {}
    tries = 0
    global host_num,len_of_last_msg
    host_num = 2
    reliability = Full_reliability()
    checksum = Checksum()

    while going:
        signal.signal(signal.SIGINT,handler)
        r= my_host.orfd(fd,timeout=0.2)
        if send_data!={}  and r == TIMEOUT: #if packet state exist and timeout then resend all the packets left in dict
            if tries<5:
                x.addline('Packet send failed... resent')
                for key in send_data.keys(): #lookup all the remaining packet in the dist and resend
                    checksum_data = forwarding.encapsulate(Dest,send_data[key])
                    total_data = checksum.encapsulate(checksum_data,len_of_last_msg)
                    my_host.send(n,total_data)
                tries += 1

        if r == FD_READY:
            x.addline('FD')
            line1 = os.read(fd,300)

            packet_list,len_of_last_msg = reliability.encapsulate(line1)


            for send_pack in packet_list:
                checksum_data = forwarding.encapsulate(Dest,send_pack)
                total_data = checksum.encapsulate(checksum_data,len_of_last_msg)
                my_host.send(n,total_data)
                tries = 0
                unique_id = bin(struct.unpack('B',send_pack[1])[0])[2:].zfill(8) + bin(struct.unpack('B',send_pack[2])[0])[2:].zfill(8) #msg_id + seq_num
                send_data.update({unique_id:send_pack})
                if line1 == '/q':
	            	going = False

        if r == NET_READY:
            x.addline('net')
            line,source = my_host.receive()
            header = checksum.decapsulate(line[:2]) + forwarding.decapsulate(line[2]) + reliability.decapsulate(line[3:6])

            ack = header[24]
            end = header[25]

            len_last_pack = int(header[8:16],2)

            dest_host = int(header[20:24],2)
            source_host = int(header[16:20],2)
            unique_id = header[32:48]

            if source_host != host_num and dest_host != host_num: #in this case only do forwarding without considering ack and packet loss
                next = forwarding.next_hop(dest_host)
                if next != False:
                    neighbour_addr = forwarding.lookup(next)
                    if neighbour_addr == '131.231.114.82:1':
                        n = n2
                    elif neighbour_addr == '131.231.115.148:1':
                        n = n1
                    my_host.send(n,line)
                    x.addline('forwarding')

            else: #this case is as a receiver
                if ack!='1' and unique_id not in reliability.unique_id_list:
                    x.addline('them:'+line[6:])
                    reliability.unique_id_list.append(unique_id)

                #x.addline('received ack:'+header[24:32]+'###')
                if ack == '1':
                    send_data.pop(unique_id) #drop data
                    tries = 0
                    if end == '1': #refresh the lists
                        reliability.unique_id_list = []
                        reliability.msg_id_list = []
                        reliability.total_package_list = []
                else: #send ack_packet
                    #compute new sum and compared with checksum
                    if end != '1':
                        new_sum = checksum.cal_checksum_header(line[2:],len_last_pack)
                    else:
                        new_sum = checksum.cal_checksum_header(line[2:6+len_last_pack],len_last_pack)
                    if new_sum[0] == line[0]: #no corruption
                        if source_host == 3:
                            n = n2
                        elif source_host == 9:
                            n = n1
                        reliability.send_ack(line,n,my_host,source_host)
                        x.addline('sent ack')


control_strategy()
