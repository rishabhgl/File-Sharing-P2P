import socket
import time
import os
import json
import hashlib
import base64

from central_reg import MongoWrapper
from userdetails import get_ip
from file_utils import break_file

'''
Provide addresses in tuple format
'''


class Sender:
    def __init__(self):
        self.hostname = socket.gethostname()
        self.ip_addr = get_ip()
        self.port = 65432
        self.alt_port = 54321
        # self.CHUNK_SIZE = 65530
        self.CHUNK_SIZE = 1024
        self.db_engine = MongoWrapper()

    def setup_listener(self):
        sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sckt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sckt.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024 * 1024)
        print("SEOCKER", sckt)
        return sckt

    def send_message(self, sckt, client_addr, content):
        if sckt:
            print(client_addr)
            sckt.connect(client_addr)
            # print("SENDING->", content)
            total_sent = 0
            while total_sent < len(content):
                sent = sckt.send(content[total_sent:])
                if sent == 0:
                    raise RuntimeError("Socket Connection broken")
                total_sent += sent
                print("SENT ", total_sent)
        else:
            raise RuntimeError("Unable to bind socket")

    def break_file(self, file_path):
        return break_file(file_path, self.CHUNK_SIZE)

    def populate_peers(self, peers, parts):
        ctr = [i for i in range(0, len(parts))]
        if len(peers) == len(parts):
            return zip(ctr, peers, parts)
        elif len(peers) > len(parts):
            return zip(ctr, peers[0:len(parts)], parts)
        else:
            new_peers = peers
            extra_req = len(parts) - len(peers)
            i = 0
            iter = 0
            while i < extra_req:
                if iter >= len(peers):
                    iter = 0
                new_peers.append(peers[iter])
                iter += 1
                i += 1
            return zip(ctr, new_peers, parts)

    def upload_file(self, file_path, peers):
        try:
            parts = self.break_file(file_path)
            filename, extension = os.path.splitext(file_path)

            if filename.__contains__('/'):
                filename = filename[filename.rindex('/')+1:]

            filehash = hashlib.md5(filename.encode('utf-8')).hexdigest()
            timestamp = time.time()

            file_meta = {"name": filename, "hash": filehash, "size": len(parts) * self.CHUNK_SIZE, "type": extension, "total_parts": len(parts), "timestamp": timestamp}

            file_id = self.db_engine.add_data_to_collection("File", file_meta)
            print("File Id: ", file_id)
            
            for ctr, peer, part in self.populate_peers(peers, parts):
                sckt = self.setup_listener()
                print("sending for peer ", peer)
                meta = {"part_file_name": f'{ctr}.part',
                        "original_name": filename,
                        "file_id": file_id,
                        "extension": extension, "content": part,
                        "offset": ctr, "length": len(parts),
                        "user_mac": peer['user_id'],
                        "timestamp": timestamp,
                        "original_size": len(parts)*self.CHUNK_SIZE}
                json_meta = json.dumps(meta)
                self.send_message(sckt, peer['address'], json_meta.encode('utf-8'))
                sckt.close()
                print("Sent for ", peer)
                meta.pop("content")
                self.db_engine.add_data_to_collection('Part', meta)
                print("Updated Registry")
        except Exception as e:
            print("Unable to upload file!")
            print(e)



if __name__ == "__main__":
    sender = Sender()
    peers = ['0.0.0.0:8000']
    sender.upload_file('/home/akshat/clg/se_project/File-Sharing-P2P/p2pbackend/o.jpg', peers)
