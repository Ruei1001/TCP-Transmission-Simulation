This server-client code simulates a reliable connection with congestion control mechanisms for handling file transmission, DNS queries, and mathematical operations. It also implements a three-way handshake protocol for connection establishment and a proper teardown with the FIN-ACK process.

Main Concepts Covered:
Three-way Handshake (TCP-like SYN/ACK/FIN):

The server and client perform a handshake similar to TCP, using SYN, SYN-ACK, and ACK packets to establish and terminate connections.
Congestion Control Simulation:

The variables cwnd, rwnd, and threshold are used to simulate a congestion window, receive window, and threshold for data transmission. These variables help control how much data can be sent at once.
Packet Loss Handling:

Timeout mechanisms and retransmission strategies are implemented to handle packet loss. For example, if a SYN-ACK packet is lost, the server resends the packet.
File Transmission:

The server sends files to the client in chunks of 1024 bytes. Both sides acknowledge the successful reception of data using SEQ and ACK numbers.
Mathematical Operations:

The server evaluates basic mathematical expressions sent by the client using the eval() function and returns the result.
DNS Queries:

The server resolves hostnames to IP addresses using socket.gethostbyname() and sends the result back to the client.

How the TCP Simulation Works
Server (server.py)
The server simulates a TCP server that:

Listens for incoming client connections on a specified IP address and port.
Accepts client connections.
Receives data from the client.
Sends responses back to the client.
Closes the connection once communication is finished.
Client (client.py)
The client simulates a TCP client that:

Establishes a connection to the server using a specific IP address and port.
Sends data to the server.
Receives responses from the server.
Closes the connection when communication is completed.
How to Run the Simulation
1. Start the Server
To start the server, navigate to the directory containing the files and run:

python server.py

The server will start listening for client connections on a specific IP and port (which you can configure in the code).

2. Run the Client
After starting the server, in a new terminal window or on a separate machine, run the client using the following command:

python client.py

The client will connect to the server and initiate the TCP communication. Once the client finishes transmitting data, it will close the connection.

Customizing IP and Port
By default, both the client and server scripts may use hardcoded IP addresses and port numbers. If you want to change these values:

Open server.py and modify the HOST and PORT variables for the server.
Open client.py and modify the HOST and PORT variables to match the server.
