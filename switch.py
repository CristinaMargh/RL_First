
import sys
import struct
import wrapper
import threading
import time
from wrapper import recv_from_any_link, send_to_link, get_switch_mac, get_interface_name

MAC_table = {}
LENGTH = 38 # for llc length
priority = 0
root_bridge_ID = 0
own_bridge_ID = 0
root_path_cost = 0
root_port = 0
trunk_links = {}
regular_links = {}

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
# Creating the BPDU frame
def make_bpdu():
   
    dest_mac = '01:80:c2:00:00:00'
    frame = bytearray(53)
    frame[0:6] = bytes.fromhex(dest_mac.replace(':', ''))
    frame[6:12] = get_switch_mac()
        
    # LLC length and header
    frame[12:14] = LENGTH.to_bytes(2, byteorder='big')
    frame[14:17] = struct.pack("!BBB", 0x42, 0x42, 0x03)  

    # BPDU Header : Protocol identifier, Protocol Version Identifier : Spanning Tree, BPDU Type and flags
    frame[17:19] = struct.pack("!H", 0x0000)
    frame[19] = 0x00
    frame[20] = 0x00
    frame[21] = 0x00
    # BPDU Configs : root identifier, rooth path cost, bridge identifier
    frame[22:30] = root_bridge_ID.to_bytes(8, byteorder='big')
    frame[30:34] = root_path_cost.to_bytes(4, byteorder='big')
    frame[34:42] = own_bridge_ID.to_bytes(8, byteorder='big')

    frame[42:44] = struct.pack("!H", 0x8004)  # port_id
    frame[44:46] = struct.pack("!H", 0x0001)  # message_age
    frame[46:48] = struct.pack("!H", 0x0011)  # max_age
    frame[48:50] = struct.pack("!H", 0x0002)  # hello_time
    frame[50:52] = struct.pack("!H", 0x000F)  # forward_delay

    return frame

def send_bdpu_every_sec():

    while True:
        # Send BDPU every second if necessary
        if root_bridge_ID == own_bridge_ID:
            dest_mac = '01:80:c2:00:00:00'
            frame = bytearray(53)
            frame[0:6] = bytes.fromhex(dest_mac.replace(':', ''))
            frame[6:12] = get_switch_mac()
                
            # LLC length and header
            frame[12:14] = LENGTH.to_bytes(2, byteorder='big')
            frame[14:17] = struct.pack("!BBB", 0x42, 0x42, 0x03)  

            # BPDU Header : Protocol identifier, Protocol Version Identifier : Spanning Tree, BPDU Type and flags
            frame[17:19] = struct.pack("!H", 0x0000)
            frame[19] = 0x00
            frame[20] = 0x00
            frame[21] = 0x00
            # BPDU Configs
            frame[22:30] = root_bridge_ID.to_bytes(8, byteorder='big')
            frame[30:34] = root_path_cost.to_bytes(4, byteorder='big')
            frame[34:42] = own_bridge_ID.to_bytes(8, byteorder='big')

            frame[42:44] = struct.pack("!H", 0x8004)  # port_id
            frame[44:46] = struct.pack("!H", 0x0001)  # message_age
            frame[46:48] = struct.pack("!H", 0x0011)  # max_age
            frame[48:50] = struct.pack("!H", 0x0002)  # hello_time
            frame[50:52] = struct.pack("!H", 0x000F)  # forward_delay

            # Send
            for o in interfaces:
                if get_interface_name(o) in trunk_links:
                    send_to_link(o, len(frame), bytes(frame))

        time.sleep(1)
# Used to extract the informations from the switchis configuration
def parse_config(switch_id):
    global priority
    global trunk_links
    with open(f"configs/switch{switch_id}.cfg", 'r') as file:
        lines = file.readlines()
        priority = int(lines[0].strip())
        for line in lines[1:]:
            parts = line.split()
            port1 = parts[0]
            port2 = parts[1]
            link_type = 'trunk' if parts[1] == 'T' else 'regular'
            port_status_trunk = 'BLOCKED'
            port_status_access = 'LISTENING'

            if link_type == 'trunk':
                trunk_links[port1] = {'port2' : port2, 'status' : port_status_trunk}
            else:
                regular_links[port1] = {'port2': int(port2), 'status' : port_status_access}

def main():
    # init returns the max interface number. Our interfaces
    # are 0, 1, 2, ..., init_ret value + 1
    switch_id = sys.argv[1]
    global interfaces
    num_interfaces = wrapper.init(sys.argv[2:])
    interfaces = range(0, num_interfaces)

    print("# Starting switch with id {}".format(switch_id), flush=True)
    print("[INFO] Switch MAC", ':'.join(f'{b:02x}' for b in get_switch_mac()))
    
    parse_config(switch_id)

    global own_bridge_ID, root_path_cost
    global root_port, root_bridge_ID, trunk_links, priority
    #init
    own_bridge_ID = priority
    root_bridge_ID = own_bridge_ID
    root_path_cost = 0

    if own_bridge_ID == root_bridge_ID:
        for interface in interfaces:
            if get_interface_name(interface) in trunk_links :
                trunk_links[get_interface_name(interface)]['status'] = 'LISTENING'
            else:
                regular_links[get_interface_name(interface)]['status'] = 'LISTENING'

    # finish init

    # Create and start a new thread that deals with sending BDPU
    t = threading.Thread(target=send_bdpu_every_sec)
    t.start()

    while True:
        interface, data, length = recv_from_any_link()

        dest_mac, src_mac, ethertype, vlan_id = parse_ethernet_header(data)

        # Print the MAC src and MAC dst in human readable format
        dest_mac = ':'.join(f'{b:02x}' for b in dest_mac)
        src_mac = ':'.join(f'{b:02x}' for b in src_mac)
		
        MAC_table[src_mac] = interface	
        #BPDU
        if dest_mac == "01:80:c2:00:00:00":
            BPDU_root_bridge = int.from_bytes(data[22:30], byteorder='big')
            BPDU_root_path_cost = int.from_bytes(data[30:34], byteorder='big')
            BPDU_bridge_id = int.from_bytes(data[34:42], byteorder='big')
            
            if BPDU_root_bridge < root_bridge_ID:

                is_bridge = 0
                if own_bridge_ID == root_bridge_ID:
                    is_bridge = 1

                root_bridge_ID = BPDU_root_bridge
                root_path_cost = BPDU_root_path_cost + 10
                root_port = interface
                # if we were the Root Bridge:
                # set all interfaces not to hosts to blocked except the root port
                if is_bridge == 1:
                    for o in interfaces:
                        if (get_interface_name(o)) in trunk_links:
                            if o != root_port:
                                trunk_links[get_interface_name(o)]['status'] = 'BLOCKED'
                            else:
                                trunk_links[get_interface_name(o)]['status'] = 'LISTENING'

                trunk_links[get_interface_name(root_port)]['status'] = 'LISTENING'

                # send bpdu
                for o in interfaces:
                    if (get_interface_name(o)) in trunk_links and trunk_links[get_interface_name(o)]['status'] == 'LISTENING':
                        send_to_link(o, len(make_bpdu()), bytes(make_bpdu()))

            elif BPDU_root_bridge == root_bridge_ID:
                if interface == root_port and BPDU_root_path_cost + 10 < root_path_cost:
                    root_path_cost = BPDU_root_path_cost + 10
                elif interface != root_port:
                    if BPDU_root_bridge > root_path_cost:
                        if trunk_links[get_interface_name(interface)]['status'] != 'LISTENING':
                            trunk_links[get_interface_name(interface)]['status'] = 'LISTENING'
            
            elif BPDU_bridge_id == own_bridge_ID:
                trunk_links[get_interface_name(interface)]['status'] = 'BLOCKED'
            else:
                pass
            
            if own_bridge_ID == root_bridge_ID:
                for o in interfaces:
                    if (get_interface_name(o)) in trunk_links:
                        trunk_links[get_interface_name(o)]['status'] = 'LISTENING'

        else:
            # Implement VLAN support and forwarding with learning
            tagged_frame = data
            tagged_frame_length = length
            if vlan_id == -1:
                if get_interface_name(interface) in regular_links:
                    port = regular_links[get_interface_name(interface)]['port2']
                    if (get_interface_name(interface) in regular_links):
                        port = regular_links[get_interface_name(interface)]['port2']
                        vlan_id = port
                        tagged_frame = data[0:12] + create_vlan_tag(vlan_id) + data[12:]
                        tagged_frame_length = length + 4

            
            if dest_mac in MAC_table:
                name_next_port = get_interface_name(MAC_table[dest_mac])
                untagged_frame = tagged_frame[0:12] + tagged_frame[16:]
                untagged_frame_length = tagged_frame_length - 4
                # If the destionation is in the switch table we send the packet without header
                if name_next_port in regular_links and (regular_links[name_next_port]['port2'] == vlan_id):
                    send_to_link(MAC_table[dest_mac], untagged_frame_length, untagged_frame)
                elif name_next_port in trunk_links and (trunk_links[name_next_port]['port2'] == 'T'):
                    if trunk_links[name_next_port]['status'] == 'LISTENING':
                        send_to_link(MAC_table[dest_mac], tagged_frame_length, tagged_frame)
            else:
                untagged_frame = tagged_frame[0:12] + tagged_frame[16:]
                untagged_frame_length = tagged_frame_length - 4
                for o in interfaces:
                    if o != interface and (get_interface_name(o)) in trunk_links:
                        if trunk_links[get_interface_name(o)]['status'] == 'LISTENING':    
                            send_to_link(o, tagged_frame_length, tagged_frame)
                    elif o!= interface and (get_interface_name(o)) in regular_links:
                        if regular_links[get_interface_name(o)]['port2'] == vlan_id:
                            send_to_link(o, untagged_frame_length, untagged_frame)

        # data is of type bytes.
        # send_to_link(i, length, data)

if __name__ == "__main__":
    main()

