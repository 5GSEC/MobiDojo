from scapy.all import *
from mutator import get_random_byte

def select_seed():
    print("Select a seed:")
    print("1. InitialUEMessage")
    choice = input("Enter your choice: ")
    
    if choice.strip() == "1":
        return "pcap/InitialUEMessage.pcap"
    else:
        print("Invalid choice. Using default: InitialUEMessage.pcap")
        return "pcap/InitialUEMessage.pcap"

def select_offsets():
    print("Select offsets to modify:")
    print("1) RAN-UE-NGAP-ID")
    print("2) Element ID")
    print("3) RRCEstablishmentCause")
    print("4) UEContextRequest")
    choices = input("Enter your choices: ").split(',')
    offset_map = {
        '1': (73, 74),
        '2': (99,),
        '3': (132,),
        '4': (137,)
    }
    return [offset_map[choice.strip()] for choice in choices if choice.strip() in offset_map]

def select_modification_type():
    print("Select modification type:")
    print("1) Random")
    print("2) In order")
    choice = input("Enter your choice: ")
    return choice.strip()

def modify_packet(packet, offsets, tsn_increment, mod_type, value_increment):
    packet_raw = bytes(packet)
    modified = bytearray(packet_raw)

    # Set TSN (offset 51-54) to the increment value, starting from 0
    new_tsn = tsn_increment.to_bytes(4, byteorder='big')
    modified[50:54] = new_tsn

    for offset in offsets:
        if mod_type == '1':  # Random
            if len(offset) == 2:  # For RAN-UE-NGAP-ID
                start, end = offset
                modified[start:end+1] = get_random_byte().to_bytes(2, 'big')
            else:  # For single byte offsets
                modified[offset[0]] = get_random_byte()
        else:  # In order
            if len(offset) == 2:  # For RAN-UE-NGAP-ID
                start, end = offset
                value = (value_increment % 256).to_bytes(2, 'big')
                modified[start:end+1] = value
            else:  # For single byte offsets
                modified[offset[0]] = value_increment % 256
            value_increment += 1

    return Ether(modified), value_increment

def generate_traffic(seed_file, offsets, count):
    packets = rdpcap(seed_file)
    modified_packets = []
    mod_type = select_modification_type()
    value_increment = 0
    for i in range(count):
        for packet in packets:
            modified_packet, value_increment = modify_packet(packet, offsets, i, mod_type, value_increment)
            modified_packets.append(modified_packet)
    return modified_packets