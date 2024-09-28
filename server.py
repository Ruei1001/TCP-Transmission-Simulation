import socket
from time import sleep
import threading
import random

HOST = '0.0.0.0'
PORT = 7010
global server_seq
server_seq = 8121
global current
current = 0
global client_seq
global client_ack
global server_ack
global cwnd, rwnd, threshold
cwnd = int(1024)
rwnd = int(524288)
threshold = int(65536)

#initialize
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(5)

print('server\'s ip address: %s\n server\'s port :%s' % (HOST, PORT))
print('wait for connection...')
client_list = []

import os
import math
socket.setdefaulttimeout(30)
def send_packet(sender_socket : socket.socket, packet : str, current : int):
    sender_socket.sendall(packet.encode())
    type = packet.split(':')[0]
    seq = int(packet.split(':')[1])
    ack = int(packet.split(':')[2])
    if type == 'SEQ':
        print(f'send packet ({current}): SEQ={seq}  : ACK={ack}')
    else:
        print(f'send packet ({current}): {type} : SEQ={seq}  : ACK={ack}')

# this function read the socket return the type seq and ack value
def recieve_packet(reciever_socket : socket.socket, current : int):
    packet = reciever_socket.recv(1024).decode()
    type = packet.split(':')[0]
    seq = int(packet.split(':')[1])
    ack = int(packet.split(':')[2])
    print(f"recieved packet ({current}): {type} : SEQ={seq} : ACK={ack}")

    return type, seq, ack
# this function handles the file transmission request
def handle_file_transmission(client_socket, filename, current):
    global cwnd, rwnd, threshold, server_seq, client_seq
    count = 0
    if os.path.exists(filename):
        sleep(0.1)
        client_socket.sendall(b"FILE_FOUND")
        with open(filename, 'rb') as file:
            while True:
                data = file.read(1024)
                cwnd += 1024
                rwnd -= 1024
                count += 1
                if not data:
                    break
                client_seq += 1024
                client_socket.sendall(data)
                #send 
                ack_packet = f"SEQ:{server_seq}:{client_seq}"
                send_packet(client_socket, ack_packet, current)
                #recieve ack
                if count % 2 == 0:
                    client_type, client_seq, client_ack = recieve_packet(client_socket, current)
                #if client_ack == server_seq :
                    #continue
                
                sleep(0.1)
            if count %2 == 1:
                client_type, client_seq, client_ack = recieve_packet(client_socket, current)
        print("Finish reading")
        server_seq += 1
        client_socket.sendall(b"EOF")
        return "File Found"
    else:
        client_socket.sendall(b"FILE_NOT_FOUND")
        return "File Not Found"

# this function handles the math calculation
def handle_math_calculation(client_socket, operation : str):
    global cwnd, rwnd, threshold
    try:
        result = eval(operation)
        client_socket.sendall(str(result).encode())
        cwnd += 1024
        rwnd -= 1024
        return str(result)
    except ValueError:
        client_socket.sendall(b"Error: Invalid operands")
        return "Error: Invalid operands"

# this function handles the DNS query
def handle_dns_query(client_socket, hostname):
    global cwnd, rwnd, threshold
    try:
        ip_address = socket.gethostbyname(hostname)
        client_socket.sendall(ip_address.encode())
        cwnd += 1024
        rwnd -= 1024
        return ip_address
    except socket.gaierror:
        client_socket.sendall(b"Error: Host not found")
        return "Error: Host not found"
    


def handshake(client_socket:socket.socket, client_address):
    global client_seq
    global server_seq
    global current
    global cwnd, rwnd, threshold
    #print(f"current client address is : {client_address}")
    # recieve a packet
    packet = client_socket.recv(1024).decode()
    client_type = packet.split(':')[0]
    client_seq = int(packet.split(':')[1])
    client_ack = int(packet.split(':')[2])
    
    # see if the packet is in the client list 
    if client_address[1] in client_list:
        current = client_list.index(client_address[1])
        print(f"recieved packet ({current}) : {client_type} : SEQ={client_seq} : ACK={client_ack}")
    else:
        client_list.append(client_address[1])
        current = client_list.index(client_address[1])
        print(f"recieved packet {client_address[0]} : {client_address[1]} : {client_type} : SEQ={client_seq} : ACK={client_ack}")
        print(f"(Add client {client_address[0]} : {client_address[1]} : ({current}) )")

    # if recieve a SYN packet
    if client_type == 'SYN':
        print(f"({current})(connecting)")
        print(f"({current}) cwnd {cwnd}, rwnd {rwnd}, threshold {threshold}")
        


        #---------------------------------------------------------------------#
        #                       send SYN-ACK                                  #
        #---------------------------------------------------------------------#
        client_packet = f"SYN-ACK:{server_seq}:{client_seq + 1}"
        send_packet(client_socket, client_packet, current)  #<--------------- comment this line then generate packet loss
        #print("packet loss")

        
        # if packet loss will time out and go to except resend the SYN-ACK and wait for recieve
        try:
            client_type, client_seq, client_ack = recieve_packet(client_socket, current)
        except socket.timeout:
            #! SYN-ACK packet loss
            print(f"(time out)")
            sleep(2)
            send_packet(client_socket, client_packet, current)
            client_type, client_seq, client_ack = recieve_packet(client_socket, current)
        
        if client_ack == server_seq + 1:
            server_seq = server_seq + 1
            print(f"({current})(connected)") 
            return "SYN_suceed"
        else:
            return "FAIL"     
    
    

def handle_client(client_socket:socket.socket, client_address):
    global server_seq
    global client_seq
    global client_ack
    global cwnd, rwnd, threshold
    global current
    print(f'recieve packet {client_address}')
    if (handshake(client_socket, client_address) == "SYN_suceed"):
        #-------------------------------------------------------------------------------#
        #              start reading request and send result                            #
        #-------------------------------------------------------------------------------#
        print(f"({current}) slow start mode")
        #count = 0
        while True:
            
            #try:
            client_type, client_seq, client_ack = recieve_packet(client_socket, current)
            #except socket.timeout:
                #print("(time out)")
                #client_type, client_seq, client_ack = recieve_packet(client_socket, current)
            
            current = client_list.index(client_address[1])
            if (client_type == 'PSH'):
                sleep(0.1)
                #print("Waiting for ")
                request_packet = client_socket.recv(1024).decode()
                request_type = request_packet.split(':')[0]
                print(f"({current}) {request_packet.split(':')[1]}")
                
                #print(f"({current})request type : {request_type}")
                print(f"({current}) try file transmission")
                if request_type == 'FILE':
                    filename = request_packet.split(':')[1]
                    msg = handle_file_transmission(client_socket, filename, current)
                    print(f"({current}) Sucess")
                    print(f"({current}) {msg}")
                    #continue
                else:
                    print(f"({current}) File not found")
                    print(f"({current})Try calculation")
                    if request_type == 'MATH':
                        #print("here")
                        
                        operation = request_packet.split(':')[1]
                        msg = handle_math_calculation(client_socket, operation)
                        print(f"({current}) Sucess")
                        print(f"({current}) {msg}")
                        #continue
                    else:
                        print(f"({current}) NAN")
                    
                        print(f"({current}) Try DNS look up")
                        if request_type == 'DNS':
                            
                            hostname = request_packet.split(':')[1]
                            msg = handle_dns_query(client_socket, hostname)
                            print(f"({current}) Sucess")
                            print(f"({current}) {msg}")
                            #continue
                        else:
                            print(f"({current}) DNS look up fail")
                    
                    #else:
                        #client_socket.sendall(b"Error: Unknown request type")
                sleep(0.1)
                #---------------------------------------------------------------------#
                #                       send PSH-ACK                                  #
                #---------------------------------------------------------------------#
                client_packet = f"PSH-ACK:{server_seq}:{client_seq + 1}"
                send_packet(client_socket, client_packet, current)

                # check if the PSH-ACK packet loss
                try:
                    client_type, client_seq, client_ack = recieve_packet(client_socket, current)
                except socket.timeout:
                    print(f"(time out)")
                    sleep(2)
                    send_packet(client_socket, client_packet, current)
                    client_type, client_seq, client_ack = recieve_packet(client_socket, current)
                if client_ack == server_seq + 1:
                    server_seq = server_seq + 1
                print(f"({current}) cwnd {cwnd}, rwnd {rwnd}, threshold {threshold}")   


            elif (client_type == 'FIN'):
                print(f"({current}) disconnecting")
                #---------------------------------------------------------------------#
                #                       send FIN-ACK                                  #
                #---------------------------------------------------------------------#
                client_packet = f"FIN-ACK:{server_seq}:{client_seq + 1}"
                send_packet(client_socket, client_packet, current)

                try:
                    client_type, client_seq, client_ack = recieve_packet(client_socket, current)
                except socket.timeout:
                    print("(time out)")
                    sleep(2)
                    send_packet(client_socket, client_packet, current)
                    client_type, client_seq, client_ack = recieve_packet(client_socket, current)
                
                if client_ack == server_seq + 1:
                    server_seq = server_seq + 1
                    print(f"({current})(disconnected)")                     
                print(f"Delete client ({current})")
                client_list.pop(current)
            else:
                    print(client_type)

# --------------------------------------------------------------------------- #
#      this function returns a server socket and do three way handshake       #
# --------------------------------------------------------------------------- #
client_list = []
while True:
        
    client_socket, client_address = server_socket.accept()
    client_thread = threading.Thread(target=handle_client, args=(client_socket,client_address,))
    client_thread.start()