# RL_First

Switch implementation

The flow of the program starts in main, where I introduced the parsing function of the configuration files for each individual switch, depending on its id. Thus, for this I defined 2 dictionaries :
trunk_links and regular_links, in which I will add the ports according to their type (trunk or access), going through each line in the file separately.The priority of the switch is also very 
important to save. For the STP functionality, I also added field status, initializing the trunk type ports with BLOCKED status and the access type ports with LISTENING.

The program continues with the necessary initializations to be able to find out later which is the root bridge. To send one bpu packet every second, if the ID of the root bridge is equal to 
the current one, a bdpu frame is created that will be sent. To create it, I followed the data and values ​​from the statement and united them all in one frame.

To see if we have BDPU frames to use, check if the destination mac address is 01:80:C2:00:00:00. In this case, we extract the necessary information for BPDU. We check if the bridge ID
is lower than ours, then the switch from which the packet was sent becomes root. With the updated information, a BPDU is retransmitted on the other ports. Next, through successive comparisons, following the pseudocode, we change the statuses of the ports. 

If the destination mac address is not the BPDU specific one, we implement support for VLAN and for forwarding with learning. In the implementation, I forwarded the frame by first checking 
the type of the port I'm on to make sure to add or not the 802.1Q header and to increase or decrease the length by 4 bytes as appropriate. Following the received pseudocode for the switching table, 
the program inserts an entry in the table that links the interface with the source address.
