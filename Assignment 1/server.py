import socket
import threading
import os
import time
import mimetypes
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime

accesscounts = {}


def response(code, filename, clientsocket):

    if code == 200:
        length = os.path.getsize(filename)
        lastmodified = datetime.fromtimestamp(os.path.getmtime(filename))
        lasttime = mktime(lastmodified.timetuple())
        filetype = mimetypes.MimeTypes().guess_type(filename)[0]
        if filetype is None:
            filetype = "application/octet-stream"
        header = ("HTTP/1.1 200 OK" + '\n'+"Date: " + format_date_time(time.time()) + '\n' + "Server: Apache \n" + "Last-Modified: " + format_date_time(
            lasttime) + '\n' + "Accept-Ranges: bytes\n" + "Content-Length: " + str(length) + '\n' + "Content-Type: " + str(filetype) + "\n" + '\n')
        header = header.encode()
        fileread = open(filename, "rb")
        header += fileread.read(length)
        clientsocket.send(header)
        fileread.close()

    else:
        header = """HTTP/1.0 404 Not Found\r\n\r\n<!DOCTYPE HTML><html><head><title>404 Not Found</title></head><body><h1>404 Resource Not Found</h1></body></html>\r\n"""
        # Convert to byte data
        header = header.encode()
        clientsocket.send(header)

    return header


def clientresponse(clientsocket, address):
    request = clientsocket.recv(1024)
    resource = request.decode().split()[1]
    requestedfile = resource.strip('/')
    lock = threading.Lock()
    clientip, clientport = address

    if (os.path.isfile(requestedfile)):
        response(200, requestedfile, clientsocket)
        if requestedfile in accesscounts:
            lock.acquire()
            accesscounts[requestedfile] += 1
            lock.release()

        else:
            lock.acquire()
            accesscounts[requestedfile] = 1
            lock.release()

        print("/" + requestedfile + "|" + clientip + "|" +
              str(clientport) + "|" + str(accesscounts[requestedfile]))
        clientsocket.close()

    else:
        response(404, requestedfile, clientsocket)
        clientsocket.close()



def socketinit():
    # create an INET, STREAMing socket
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # bind the socket to a public host, and a well-known port.
    serversocket.bind(('', 0))
    # Return a fully qualified domain name.
    host = socket.getfqdn()
    try:  
        os.chdir("www")
    except OSError as err:
        print("Directory Not found: {0}".format(err))
        exit(1)
    # Return the socket’s own address and covert to string. Used to find out the port number of an IPv4/v6 socket.
    port = str(serversocket.getsockname()[1])
    print("Starting Server")
    print("Host:"+host+" Port:"+port)
    serversocket.listen(20)  # Liseten to 20 connections in queue
    while 1:
        (clientsocket, address) = serversocket.accept()
        # creating new thread
        newthread = threading.Thread(
            target=clientresponse, args=(clientsocket, address))
        newthread.start()


def mainfunc():
    socketinit()


if __name__ == "__main__":
    mainfunc()
