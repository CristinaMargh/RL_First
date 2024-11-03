
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
		
        MAC_table[src_mac] = interface	
        # TODO: Implement VLAN support and forwarding with learning
        # Decomposing the .cfg file
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
                    trunk_links[port1] = port2
                else:
                    regular_links[port1] = int(port2)
        # am creat vlan_id is am adaugat headerul in caz ca nu era
        tagged_frame = data
        tagged_frame_length = length
        if vlan_id == -1:
            port = regular_links[get_interface_name(interface)]
            if (get_interface_name(interface) in regular_links):
                port = regular_links[get_interface_name(interface)]
                vlan_id = port
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
            for o in interfaces:
                if o != interface and (get_interface_name(o)) in trunk_links:
                    send_to_link(o, tagged_frame_length, tagged_frame)
                elif o!= interface and (get_interface_name(o)) in regular_links:
                    if regular_links[get_interface_name(o)] == vlan_id:
                        send_to_link(o, untagged_frame_length, untagged_frame)

        # TODO: Implement STP support
		
        # data is of type bytes.
        # send_to_link(i, length, data)

if __name__ == "__main__":
    main()
