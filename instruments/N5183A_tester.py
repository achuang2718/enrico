import socket
from telnetlib import Telnet

HOST = '192.168.1.14'  # The server's hostname or IP address
PORT = 5025        # The port used by the server

with Telnet(HOST, 5025) as tn:
    print(tn)