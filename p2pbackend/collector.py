import socket
import asyncio
import base64
import os
import json

from userdetails import get_ip

def save_data(st):
    try:
        os.mkdir(f'/home/{os.getlogin()}/.localran/')
    except FileExistsError:
        print("Exists...")

    file_content = st['content'].encode('utf-8')
    file_content = base64.b64decode(file_content)

    try:
        os.mkdir(f'/home/{os.getlogin()}/.localran/{st["original_name"]}-{st["timestamp"]}')
    except FileExistsError:
        print("Exists")
    with open(f'/home/{os.getlogin()}/.localran/{st["original_name"]}-{st["timestamp"]}/{st["part_file_name"] + st["extension"]}', "wb") as file:
        print("WRITING")
        ac = file_content
        file.write(ac)
    print("RECEIVED")

async def send_data(st, client):
    part = st['offset']
    file_info = st['file_info']
    loop = asyncio.get_event_loop()

    filepath = os.path.join(f"/home/{os.getlogin()}/.localran/", f"{file_info['name']}-{file_info['timestamp']}", f"{part}.part{file_info['type']}")

    if os.path.exists(filepath):
        with open(filepath, "rb") as partdata:
            print("Reading part...")
            data = partdata.read()
            to_send = base64.b64encode(data)
            await loop.sock_sendall(client, to_send)
    else:
        print("Required part does not exist!")
    

async def respond_peer(client):
    loop = asyncio.get_event_loop()

    request = await loop.sock_recv(client, 1024*1024)

    req = request.decode('utf-8')
    st = json.loads(req)

    if (st['operation'] == "upload"):
        save_data(st)
    else:
        await send_data(st, client)
    
    client.close()


async def setup_recieve_data():
    sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    sck.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sck.setblocking(False)

    PORT = 8010
    device_ip = get_ip()
    print(device_ip)
    sck.bind((device_ip, PORT))
    
    sck.listen(8)
    
    loop = asyncio.get_event_loop()

    while True:
        client, _ = await loop.sock_accept(sck)
        loop.create_task(respond_peer(client))
