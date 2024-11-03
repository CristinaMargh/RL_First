# #!/usr/bin/python3
# import sys
# import struct
# import wrapper
# import threading
# import time
# from wrapper import recv_from_any_link, send_to_link, get_switch_mac, get_interface_name

# MAC_table = {}

# def parse_ethernet_header(data):
#     # Unpack the header fields from the byte array
#     #dest_mac, src_mac, ethertype = struct.unpack('!6s6sH', data[:14])
#     dest_mac = data[0:6]
#     src_mac = data[6:12]
    
#     # Extract ethertype. Under 802.1Q, this may be the bytes from the VLAN TAG
#     ether_type = (data[12] << 8) + data[13]

#     vlan_id = -1
#     # Check for VLAN tag (0x8100 in network byte order is b'\x81\x00')
#     if ether_type == 0x8200:
#         vlan_tci = int.from_bytes(data[14:16], byteorder='big')
#         vlan_id = vlan_tci & 0x0FFF  # extract the 12-bit VLAN ID
#         ether_type = (data[16] << 8) + data[17]

#     return dest_mac, src_mac, ether_type, vlan_id

# def create_vlan_tag(vlan_id):
#     # 0x8100 for the Ethertype for 802.1Q
#     # vlan_id & 0x0FFF ensures that only the last 12 bits are used
#     return struct.pack('!H', 0x8200) + struct.pack('!H', vlan_id & 0x0FFF)

# def send_bdpu_every_sec():
#     while True:
#         # TODO Send BDPU every second if necessary
#         time.sleep(1)

# def find_port(port1, links):
#     # for p1, p2 in links:
#     #     if p1 == port1:
#     #         return p2
#     # return None
#     if port1 in links: 
#         return links[port1]
#     else:
#         return None

# def main():
#     # init returns the max interface number. Our interfaces
#     # are 0, 1, 2, ..., init_ret value + 1
#     switch_id = sys.argv[1]

#     num_interfaces = wrapper.init(sys.argv[2:])
#     interfaces = range(0, num_interfaces)

#     print("# Starting switch with id {}".format(switch_id), flush=True)
#     print("[INFO] Switch MAC", ':'.join(f'{b:02x}' for b in get_switch_mac()))

#     # Create and start a new thread that deals with sending BDPU
#     t = threading.Thread(target=send_bdpu_every_sec)
#     t.start()

#     # Printing interface names
#     for i in interfaces:
#         print(get_interface_name(i))
#     while True:
#         # Note that data is of type bytes([...]).
#         # b1 = bytes([72, 101, 108, 108, 111])  # "Hello"
#         # b2 = bytes([32, 87, 111, 114, 108, 100])  # " World"
#         # b3 = b1[0:2] + b[3:4].
#         interface, data, length = recv_from_any_link()

#         dest_mac, src_mac, ethertype, vlan_id = parse_ethernet_header(data)

#         # Print the MAC src and MAC dst in human readable format
#         dest_mac = ':'.join(f'{b:02x}' for b in dest_mac)
#         src_mac = ':'.join(f'{b:02x}' for b in src_mac)

#         # Note. Adding a VLAN tag can be as easy as
#         # tagged_frame = data[0:12] + create_vlan_tag(10) + data[12:]

#         print(f'Destination MAC: {dest_mac}')
#         print(f'Source MAC: {src_mac}')
#         print(f'EtherType: {ethertype}')

#         print("Received frame of size {} on interface {}".format(length, interface), flush=True)

#         # TODO: Implement forwarding with learning
		
#         MAC_table[src_mac] = interface	
#         # if dest_mac != get_switch_mac():
#         #     if dest_mac in MAC_table:
#         #         send_to_link(MAC_table[dest_mac], length, data)
#         #     else:
#         #         for o in interfaces:
#         #             if o != interface:
#         #                 send_to_link(o, length, data)
#         # else:
#         #     for o in interfaces:
#         #         if o != interface:
#         #             send_to_link(o, length, data)
        

#         # TODO: Implement VLAN support
#         # find out acces and trunk ports by decomposing the .cfg files
#         trunk_links = {}
#         regular_links = {}

#         with open(f"configs/switch{switch_id}.cfg", 'r') as file:
#             lines = file.readlines()
#             for line in lines[1:]:
#                 parts = line.split().strip()
#                 port1 = parts[0]
#                 port2 = parts[1]
#                 link_type = 'trunk' if parts[1] == 'T' else 'regular'

#                 if link_type == 'trunk':
#                     trunk_links[port1] = int(port2)
#                 else:
#                     regular_links[port1] = int(port2)
#         # am creat vlan_id is am adaugat headerul in caz ca nu era
#         if (vlan_id == -1):
#             if (get_interface_name(interface) in regular_links):
#                 port = regular_links[get_interface_name(interface)]
#                 vlan_id = int(port)
#                 tagged_frame = data[0:12] + create_vlan_tag(vlan_id) + data[12:]
#                 tagged_frame_length = length + 4
#         else:
#             port = trunk_links[get_interface_name(interface)]
#             tagged_frame = data
#             tagged_frame_length = length(data)
#             data = data[0:12] + data[16:]
#             length = tagged_frame_length - 4

        
#             # Daca destinatia se afla in tabela switch-ului (avem vlan normal)
#             # trimitem pachetul FARA header (nu e nevoie de el)
#             if dest_mac in MAC_table:
#                 if find_port(get_interface_name(MAC_table[dest_mac], regular_links)) == vlan_id:
#                     send_to_link(MAC_table[dest_mac], length, data)
#                 elif find_port(get_interface_name(MAC_table[dest_mac]), trunk_links) == 'T':
#                     send_to_link(MAC_table[dest_mac], tagged_frame_length, tagged_frame)
#             else:
#                 for i in interfaces:
#                     if i != interface and get_interface_name(MAC_table[dest_mac]) in trunk_links:
#                         send_to_link(i, tagged_frame_length, tagged_frame)
#                     elif i!= interface and get_interface_name(MAC_table[dest_mac]) in regular_links:
#                         if int(regular_links[get_interface_name(MAC_table[dest_mac])]) == vlan_id:
#                             send_to_link(i, length, data[0:12] + data[16:])

#         # TODO: Implement STP support
		
#         # data is of type bytes.
#         # send_to_link(i, length, data)

# if __name__ == "__main__":
#     main()


#!/usr/bin/python3
import sys
import struct
import wrapper
import threading
import time
from wrapper import recv_from_any_link, send_to_link, get_switch_mac, get_interface_name

MAC_table = {}

def parse_ethernet_header(data):
    # Unpack the header fields from the byte array
    #dest_mac, src_mac, ethertype = struct.unpack('!6s6sH', data[:14])
    dest_mac = data[0:6]
    src_mac = data[6:12]
    
    # Extract ethertype. Under 802.1Q, this may be the bytes from the VLAN TAG
    ether_type = (data[12] << 8) + data[13]

    vlan_id = -1
    # Check for VLAN tag (0x8100 in network byte order is b'\x81\x00')
    if ether_type == 0x8200:
        vlan_tci = int.from_bytes(data[14:16], byteorder='big')
        vlan_id = vlan_tci & 0x0FFF  # extract the 12-bit VLAN ID
        ether_type = (data[16] << 8) + data[17]

    return dest_mac, src_mac, ether_type, vlan_id

def create_vlan_tag(vlan_id):
    # 0x8100 for the Ethertype for 802.1Q
    # vlan_id & 0x0FFF ensures that only the last 12 bits are used
    return struct.pack('!H', 0x8200) + struct.pack('!H', vlan_id & 0x0FFF)

def send_bdpu_every_sec():
    while True:
        # TODO Send BDPU every second if necessary
        time.sleep(1)

def main():
    # init returns the max interface number. Our interfaces
    # are 0, 1, 2, ..., init_ret value + 1
    switch_id = sys.argv[1]

    num_interfaces = wrapper.init(sys.argv[2:])
    interfaces = range(0, num_interfaces)

    print("# Starting switch with id {}".format(switch_id), flush=True)
    print("[INFO] Switch MAC", ':'.join(f'{b:02x}' for b in get_switch_mac()))

    # Create and start a new thread that deals with sending BDPU
    t = threading.Thread(target=send_bdpu_every_sec)
    t.start()

    # Printing interface names
    for i in interfaces:
        print(get_interface_name(i))
    vlan_table = {}
    while True:
        # Note that data is of type bytes([...]).
        # b1 = bytes([72, 101, 108, 108, 111])  # "Hello"
        # b2 = bytes([32, 87, 111, 114, 108, 100])  # " World"
        # b3 = b1[0:2] + b[3:4].
        interface, data, length = recv_from_any_link()

        dest_mac, src_mac, ethertype, vlan_id = parse_ethernet_header(data)

        # Print the MAC src and MAC dst in human readable format
        dest_mac = ':'.join(f'{b:02x}' for b in dest_mac)
        src_mac = ':'.join(f'{b:02x}' for b in src_mac)

        # Note. Adding a VLAN tag can be as easy as
        # tagged_frame = data[0:12] + create_vlan_tag(10) + data[12:]

        print(f'Destination MAC: {dest_mac}')
        print(f'Source MAC: {src_mac}')
        print(f'EtherType: {ethertype}')

        print("Received frame of size {} on interface {}".format(length, interface), flush=True)

        # TODO: Implement forwarding with learning
		
        MAC_table[src_mac] = interface	
        # if dest_mac != get_switch_mac():
        #     if dest_mac in MAC_table:
        #         send_to_link(MAC_table[dest_mac], length, data)
        #     else:
        #         for o in interfaces:
        #             if o != interface:
        #                 send_to_link(o, length, data)
        # else:
        #     for o in interfaces:
        #         if o != interface:
        #             send_to_link(o, length, data)
        

        # TODO: Implement VLAN support
        # find out acces and trunk ports by decomposing the .cfg files
        trunk_links = {}
        regular_links = {}


        with open(f"configs/switch{switch_id}.cfg", 'r') as file:
            lines = file.readlines()
            priority = int(lines[0].strip())
            for line in lines[1:]:
                parts = line.split()
                port1 = parts[0]
                port2 = parts[1]
                link_type = 'trunk' if parts[1] == 'T' else 'regular'

                if link_type == 'trunk':
                    print(f'port1 trunk: {port1}')
                    trunk_links[port1] = port2
                else:
                    print(f'port1 access: {port1}')
                    print(f'port2 access: {port2}')
                    regular_links[port1] = int(port2)
        # am creat vlan_id is am adaugat headerul in caz ca nu era
        tagged_frame = data
        tagged_frame_length = length
        if (vlan_id == -1):
            port = regular_links[get_interface_name(interface)]
            if (get_interface_name(interface) in regular_links):
                port = regular_links[get_interface_name(interface)]
                vlan_id = int(port)
                tagged_frame = data[0:12] + create_vlan_tag(vlan_id) + data[12:]
                tagged_frame_length = length + 4

        
        if dest_mac in MAC_table:
            name_next_port = get_interface_name(MAC_table[dest_mac])
            untagged_frame = tagged_frame[0:12] + tagged_frame[16:]
            untagged_frame_length = tagged_frame_length - 4
            # Daca destinatia se afla in tabela switch-ului (avem vlan normal)
            # trimitem pachetul FARA header (nu e nevoie de el)
            if name_next_port in regular_links and (regular_links[name_next_port] == vlan_id):
                send_to_link(MAC_table[dest_mac], untagged_frame_length, untagged_frame)
            elif name_next_port in trunk_links and (trunk_links[name_next_port] == 'T'):
                send_to_link(MAC_table[dest_mac], tagged_frame_length, tagged_frame)
        else:
            untagged_frame = tagged_frame[0:12] + tagged_frame[16:]
            untagged_frame_length = tagged_frame_length - 4
            for i in interfaces:
                if i != interface and (get_interface_name(i)) in trunk_links:
                    send_to_link(i, tagged_frame_length, tagged_frame)
                elif i!= interface and (get_interface_name(i)) in regular_links:
                    if int(regular_links[get_interface_name(i)]) == vlan_id:
                        send_to_link(i, untagged_frame_length, untagged_frame)

        # TODO: Implement STP support
		
        # data is of type bytes.
        # send_to_link(i, length, data)

if __name__ == "__main__":
    main()
