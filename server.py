import signal
import socket
import sys

import argumentValidator

"""
author Michael Waller
"""

print("Welcome to the TextFileTransfer Server")


def sendConfirmation(client):
    client.settimeout(10)
    confirm = b'confirm\r\n'
    bitLength = client.send(confirm)

    while confirm:
        client.settimeout(10)
        confirm = confirm[bitLength:]
        bitLength = client.send(confirm)


def receiveBytes(client, compareBytes, endLine=b'\r\n'):
    client.settimeout(10)
    recvBits = client.recv(1024)
    while not recvBits.__contains__(endLine):
        client.settimeout(10)
        recvMoreBits = client.recv(1024)
        recvBits += recvMoreBits
    return recvBits == compareBytes


def receiveFile(client):
    client.settimeout(10)
    recvBits = client.recv(10485760)
    recvLength = len(recvBits)
    extraBits = -1

    while extraBits != 0 and recvLength < sys.maxsize:
        client.settimeout(10)
        recvMoreBits = client.recv(10485760)
        if recvLength + len(recvMoreBits) >= sys.maxsize:
            recvLength = sys.maxsize
        else:
            recvLength += len(recvMoreBits)
        extraBits = len(recvMoreBits)

    return recvLength


def handler(signum):
    global not_stopped
    print('Signal handler called with signal', signum)
    not_stopped = False


signal.signal(signal.SIGINT | signal.SIGTERM | signal.SIGQUIT, handler)

err = argumentValidator.isCorrectArguments(sys.argv, 1, sys.argv[1])
if not err[0]:
    sys.stderr.write(err[1] + "\n")
    exit(1)
port = int(sys.argv[1])
try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serverSocket:
        serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1)
        serverSocket.bind(("0.0.0.0", port))
        serverSocket.listen(10)

        not_stopped = True

        while not_stopped:
            count = 0
            try:
                with serverSocket.accept()[0] as curr:
                    print('Accepted connection', curr.getsockname())

                    while count < 2:
                        if count == 0:
                            sendConfirmation(curr)
                        if receiveBytes(curr, b'confirm-bytes\r\n'):
                            sendConfirmation(curr)
                            count += 1
                        if receiveBytes(curr, b'confirm-bytes-again\r\n\r\n', b'\r\n\r\n') and count == 1:
                            count += 1
                        if count == 2:
                            receivedAmount = receiveFile(curr)
                            curr.close()
                    pass
                pass

            except socket.gaierror:
                sys.stderr.write("ERROR: Incorrect Host name\n")
                curr.close()
                continue
            except TimeoutError:
                sys.stderr.write("ERROR: Unable to connect to Server at %s\n" % sys.argv[1])
                curr.close()
                continue
            except socket.error:
                sys.stderr.write("ERROR: Socket Unable to connect\n")
                curr.close()
                continue
            except Exception:
                sys.stderr.write("ERROR")
                curr.close()
                continue
        pass
    pass
except TimeoutError:
    sys.stderr.write("ERROR: Timeout\n")
    serverSocket.close()
except socket.error:
    sys.stderr.write("ERROR\n")
    serverSocket.close()

print("Closing")
