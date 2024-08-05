import docker
import os
import time
import threading
import socket
import struct 

def get_sock(ctn) -> socket.SocketIO:
    return ctn.attach_socket(params={'stdin': 1, 'stdout': 1, 'stderr': 1, 'stream':1})


def thread_function(sock):
    header = os.read(sock.fileno(), 8)
    print(''.join('{:02x} '.format(x) for x in header[3:8]))
    lenght = int.from_bytes(header[4:8], byteorder='big')
    #print(lenght)
    read_bytes = os.read(sock.fileno(), lenght)
    while read_bytes:
        #read_bytes 
        #print("len", len(read_bytes))
        payload = read_bytes.decode("utf-8")
        payload = payload.replace("\n", "")
        print( header[0], ":", payload )
        header = os.read(sock.fileno(), 8)
        lenght = int.from_bytes(header[4:8], byteorder='big')
        print(lenght)
        read_bytes = os.read(sock.fileno(), lenght)

    #os.close(sock)

# Create container and start it
client = docker.from_env()
client.images.pull('alpine:latest')
client.images.pull('python:latest')

print(os.path.dirname(os.path.realpath(__file__)))

#cmd = '/bin/sh -c "while :; do echo hello from stdin; echo hello from stderr > /dev/stderr; sleep 1; done;"'
cmd = 'python3 -u pytest.py'
#container = client.containers.create('debian:latest', name='test', auto_remove=True, stdin_open = True, tty = True, command = 'sh')
#container = client.containers.run("alpine", name="test", auto_remove=True, command=cmd, stdin_open = True, detach=True)
container = client.containers.run("python", name="test", auto_remove=True, command=cmd, stdin_open = True, detach=True, 
                                  volumes = [f'{os.path.dirname(os.path.realpath(__file__))}:/usr/src/app'],
                                  working_dir = '/usr/src/app')

# Create communication socket
s = get_sock(container)
print(type(s))
x = threading.Thread(target=thread_function, args=(s,))
x.start()

# Set the socket as non-blocking
#s._sock.setblocking(False)

# Wait for a while ...
time.sleep(10)

# Send something toi stdin
os.write(s.fileno(),b'this is a test\n')

container.stop()
