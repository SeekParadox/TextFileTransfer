import socket
import sys

import argumentValidator

"""
@author Michael Waller
"""


def receive_bytes(sock, bit_count=1024):
    """
    Method for receiving a sequence of bytes from a socket server
    :param sock: existing socket used to receive bytes
    :param bit_count: amount of bits expected to receive from server socket: default value 1024
    :return: None
    """
    sock.settimeout(10)
    rData = sock.recv(bit_count)
    compare_bytes = b"confirm\r\n"

    if rData:
        while rData != compare_bytes:
            sock.settimeout(10)  # newest one
            recieve_more = sock.recv(bit_count)
            if recieve_more:
                rData += recieve_more
            else:
                raise TimeoutError
    else:
        raise TimeoutError
    print(rData)


def send_confirmation(sock, msg):
    """
    Method for sending confirmation to the server that bytes were received
    :param sock: existing socket used to send bytes
    :param msg: confirmation message
    :return: None
    """
    sock.settimeout(10)
    length = sock.send(msg)

    while msg:
        sock.settimeout(10)
        msg = msg[length:]
        length = sock.send(msg)


def send_file(sock, openFile):
    """
    Method for sending file over to the socket server:
    :param sock: existing socket used to send file
    :param openFile:  file-header to be sent to the socket server
    :return: None
    """
    try:
        file = open(openFile, "rb")
    except FileNotFoundError:
        sys.stderr.write("ERROR: File not found\n")
        exit(1)

    file.readable()
    o = file.read()

    while o:
        sender = o[:10000]
        sock.settimeout(10)
        length = sock.send(sender)
        while sender:
            sock.settimeout(10)
            sender = sender[length:]
            length = sock.send(sender)
        o = o[10000:]


err = argumentValidator.isCorrectArguments(sys.argv, 4, sys.argv[2])
if not err[0]:
    sys.stderr.write(err[1] + "\n")
    exit(1)
port = int(sys.argv[2])

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    try:
        sock.settimeout(10)
        sock.connect((sys.argv[1], int(sys.argv[2])))
        compareBytes = b"confirm\r\n"
        count = 0

        while count < 2:
            receive_bytes(sock)

            if count == 0:
                confirmation = b'confirm-bytes\r\n'
                send_confirmation(sock, confirmation)

            elif count == 1:
                confirmation = b'confirm-bytes-again\r\n\r\n'
                send_confirmation(sock, confirmation)
            count += 1

        send_file(sock, sys.argv[3])

    except socket.gaierror:
        sys.stderr.write("ERROR: Incorrect Host name\n")
        exit(1)
    except TimeoutError:
        sys.stderr.write("ERROR: Unable to connect to Server at %s\n" % sys.argv[1])
        exit(1)
    except socket.error:
        sys.stderr.write("ERROR: Socket Unable to connect\n")
        exit(1)

    pass
pass
