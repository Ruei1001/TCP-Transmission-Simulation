import socket
import time
import random
HOST = '0.0.0.0'
PORT = 7010
global client_seq
global client_ack
global server_seq
global server_ack
client_seq = random.randint(1,10000)
client_ack = 0

socket.setdefaulttimeout(30)
# this function take the packet as string and send through the socket
def send_packet(sender_socket : socket.socket, packet : str):
    sender_socket.sendall(packet.encode())
    type = packet.split(':')[0]
    seq = int(packet.split(':')[1])
    ack = int(packet.split(':')[2])
    print(f'send packet : {type} : SEQ={seq}  : ACK={ack}')

# this function read the socket return the type seq and ack value
def recieve_packet(reciever_socket : socket.socket):
    packet = reciever_socket.recv(1024).decode()
    type = packet.split(':')[0]
    seq = int(packet.split(':')[1])
    ack = int(packet.split(':')[2])
    if type == "SEQ":
        print(f"recieved packet : SEQ={seq} : ACK={ack}")
    else:
        print(f"recieved packet : {type} : SEQ={seq} : ACK={ack}")

    return type, seq, ack

# --------------------------------------------------------------------------- #
# this function returns a client socket and do three way handshake to connect #
# --------------------------------------------------------------------------- #
def client_handshake(HOST, PORT)->socket.socket:
    global client_seq
    global client_ack
    global server_seq
    global server_ack
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))

    print(f"Server\'s ip address : {HOST}")
    print(f"Server\'s port : {PORT}")
    #client_socket.bind((HOST, PORT))
    # send synchronization
    client_seq = 1225
    client_ack = 0

    print("(connecting)")
    # send the SYN packet
    syn_packet = f"SYN:{client_seq}:{client_ack}"
    send_packet(client_socket, syn_packet)
    #print("packet loss")

    # Receive SYN-ACK with server sequence number and acknowledgment number
    try:
        server_type, server_seq, server_ack = recieve_packet(client_socket)
    except socket.timeout:
        #syn_packet = f"SYN:{client_seq}:{client_ack}"
        print("Time out")
        #send_packet(client_socket, syn_packet)
        server_type, server_seq, server_ack = recieve_packet(client_socket)
    #the possibility of continuous 2 packet loss is 10^-12 is cp value is too low to implement a while loop to check

    if server_ack == client_seq + 1:
        client_seq = client_seq + 1
        ack_packet = f"ACK:{client_seq}:{server_seq+1}"
        send_packet(client_socket, ack_packet)
        print("(connected)") #sucessful connected
    
    return client_socket

def handshake(client_socket : socket.socket, HOST, PORT):
    global server_seq
    global client_seq
    global client_ack
    global server_ack
    syn_packet = f"PSH:{client_seq}:{server_seq+1}"
    send_packet(client_socket, syn_packet)

    # Receive SYN-ACK with server sequence number and acknowledgment number
    server_type, server_seq, server_ack = recieve_packet(client_socket)
    if server_ack == client_seq + 1:
        client_seq = client_seq + 1
        ack_packet = f"ACK:{client_seq}:{server_seq+1}"
        send_packet(client_socket, ack_packet)
        return True
    else:
        return False

def request_file(client_socket:socket.socket, filename, num:int):
    global client_seq
    global server_seq
    global server_ack
    count = 0
    print(f"(task {num}: {filename} )")
    packet = f"FILE:{filename}"
    client_socket.sendall(packet.encode())
    # the packet now is File:filename
    

    response = client_socket.recv(1024)
    print("result")
    if response == b'FILE_FOUND':
        print("File found")
        with open('received_' + filename, 'wb') as file:
            while True:
                data = client_socket.recv(1024)
                count += 1 
                if data == b'EOF':
                    break
                if not data:
                    break
                file.write(data)

                server_type, server_seq, server_ack = recieve_packet(client_socket)
                client_seq = server_ack
                if count % 2 == 0:
                    ack_packet = f"ACK:{client_seq}:{server_seq}"
                    send_packet(client_socket, ack_packet)
            if count % 2 == 1:
                ack_packet = f"ACK:{client_seq}:{server_seq}"
                send_packet(client_socket, ack_packet)
        #print(f"File '{filename}' received")
        print(f"(task {num}: end)")
    else:
        print(f"File '{filename}' not found.")
    #send ACK
    '''
    ack_packet = f"ACK:{client_seq}:{server_seq + 1}"
    client_socket.sendall(ack_packet.encode())
    print(f'send packet : ACK : SEQ={client_seq}  : ACK={server_seq + 1}')
    client_seq = client_seq + 1'''

def request_math_operation(client_socket, operation : str, num):

    print(f"(task {num}:{operation})")
    packet = f"MATH:{operation}"
    client_socket.sendall(packet.encode())

    
    result = client_socket.recv(1024).decode()

    print("result")
    print(f"{result}")
    print(f"(task {num}: end)")

def request_dns_query(client_socket, hostname, num):

    print(f"(task {num}: {hostname})")
    packet = f"DNS:{hostname}"
    client_socket.sendall(packet.encode())
    
    ip_address = client_socket.recv(1024).decode()
    print("result")
    print(f"{ip_address}")
    print(f"(task {num}: end)")

def disconnect(client_socket:socket.socket):
    global client_seq
    global server_seq
    # send FIN
    fin_pkg = f"FIN:{client_seq}:{server_seq+1}"
    send_packet(client_socket, fin_pkg)
    
    #--------------------------------------------------------------------#
    #                       Check if FIN-ACK loss                        #
    #--------------------------------------------------------------------#
    try:
        server_type, server_seq, server_ack = recieve_packet(client_socket)
    except socket.timeout:
        print("(time out )")
        server_type, server_seq, server_ack = recieve_packet(client_socket)
    
    if server_ack == client_seq + 1:
        client_seq = client_seq + 1
        ack_packet = f"ACK:{client_seq}:{server_seq+1}"
        send_packet(client_socket, ack_packet)
        return True
    else:
        return False

def debug(client_socket:socket.socket,action_type, action_arg ,num):
    global client_seq
    global server_seq
    #send push
    syn_packet = f"PSH:{client_seq}:{server_seq+1}"
    send_packet(client_socket, syn_packet)
    num += 1
    if action_type == 'FILE':
        filename = action_arg
        request_file(client_socket, filename, num)
    elif action_type == 'MATH':
        request_math_operation(client_socket, action_arg, num)
    elif action_type == 'DNS':
        request_dns_query(client_socket, action_arg, num)
    elif action_type == "FIN":
        print("Disconnecting")
        if disconnect(client_socket) == True:
            print("Disconnected")
        else:
            print("Disconnect failed")

    server_type, server_seq, server_ack = recieve_packet(client_socket)
    if server_ack == client_seq + 1:
        client_seq = client_seq + 1
        ack_packet = f"ACK:{client_seq}:{server_seq+1}"
        send_packet(client_socket, ack_packet)

#client_socket = client_handshake(HOST, PORT)
#client_socket2 = client_handshake(HOST, PORT)
# Initial handshake simulation
client_socket = client_handshake(HOST, PORT)

num = 0
while True:
    action = input("Input the action: ")
    if action == 'FIN':
        print("Disconnecting")
        if disconnect(client_socket) == True:
            print("Disconnected")
            break
        else:
            print("Disconnect failed")
    action_type = action.split(':')[0]
    action_arg = action.split(':')[1]

    #send push
    syn_packet = f"PSH:{client_seq}:{server_seq+1}"
    send_packet(client_socket, syn_packet)
    time.sleep(0.1)
    num += 1
    if action_type == 'FILE':
        filename = action_arg
        request_file(client_socket, filename, num)
    elif action_type == 'MATH':
        request_math_operation(client_socket, action_arg, num)
    elif action_type == 'DNS':
        request_dns_query(client_socket, action_arg, num)
    elif action_type == "FIN":
        print("Disconnecting")
        if disconnect(client_socket) == True:
            print("Disconnected")
            break
        else:
            print("Disconnect failed")
    else:
        print(f"invalid command \"{action}\"")
        continue
    #------------------------------------------------------------------#
    #                   recieve PSH_ACK                                #
    #------------------------------------------------------------------#
    try:
        server_type, server_seq, server_ack = recieve_packet(client_socket)
    except socket.timeout:
        print("(time out)")
        server_type, server_seq, server_ack = recieve_packet(client_socket)
    if server_ack == client_seq + 1:
        client_seq = client_seq + 1

        ack_packet = f"ACK:{client_seq}:{server_seq+1}"
        #! send ACK of PSH-ACK
        send_packet(client_socket, ack_packet)
        
        #break

client_socket.close()