import socket
import json
import os
import base64
import requests

from central_reg import MongoWrapper

def make_download_requests(file_uid):

    try:
        mongo = MongoWrapper()
        file_info = mongo.get_file_data(file_uid)
        seeders_info = []
        
        parts_of_file = mongo.get_parts_for_file(file_info["_id"])

        parts = [0] * file_info['total_parts']

        for part in parts_of_file:
            offset = part['offset']
            if parts[offset] == 0:
                parts[offset] = part
                parts[offset]['users'] = [part['user_mac']]
                parts[offset].pop('user_mac')
            else:
                parts[offset]['users'].append(part['user_mac'])
        
        for part in parts:
            active_users = 0
            for user in part['users']:
                result = mongo.get_user_if_active(user)
                if result:
                    user_info = {"offset": part['offset'], "user_ip": result['ip_address']}
                    active_users += 1
                    seeders_info += [user_info]
                    break
            if active_users == 0:
                return "Could not find enough active users!"
            
    except Exception as e:
        print(e)
        return "Internal Error"


    for seeder_info in seeders_info:
            
        #Here will start send http request to Flask server to start concurrent downloads with each each seeder

        request_data = json.dumps({'file_info': file_info, 'seeder_info': seeder_info})
        # request_data = { 'file_uid': file_info['file_uid'], 'seeder_info': seeder_info}

        response = requests.post("http://127.0.0.1:5000/download/request", json = request_data)
        print(response.text)
        if response.text != "Success":
            return {"status": "Something went wrong!"}
        else:
            pass
            # mongo.update_seeders_post_download(file_info['file_uid'], seeder_info['offset'])
    
    summary = {'file_info': file_info, "status": "Success!"}
    return json.dumps(summary)
        

def request_download(file_info, seeder):
    SHARE_PATH = f'/home/{os.getlogin()}/.localran/'
    savepath = os.path.join(SHARE_PATH, f"{file_info['name']}-{file_info['timestamp']}-2")

    os.makedirs(savepath, exist_ok=True)

    timeout_dur = 15
    python_message = {
            "operation": "download",
            "file_info": file_info,
            "offset": seeder['offset']
        }
    
    message = json.dumps(python_message)
    seeder_ip = str(seeder['user_ip'])
    seeder_port = 8010

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((seeder_ip, seeder_port))
        sock.settimeout(timeout_dur) 
        print("Connected to sender!")
        
        sock.sendall(bytes(message, encoding='utf-8'))
        print("Sent request")
        
        try:
            part = bytearray()
            
            while True:
                print("Receiving part...")
                data = sock.recv(1024 * 5)
                
                if not data:
                    with open(f"{savepath}/{seeder['offset']}.part{file_info['type']}", "wb+") as file_part:
                        part = base64.b64decode(part)
                        file_part.write(part)
                        print("Part", seeder['offset'], "written!")
                        return True
                
                part.extend(data)
                
        except Exception as e:
            print(e)
            return False
    

if __name__ == "__main__":
    
    file_info = {
        "file_uid": "1023"
    }  
    
    make_download_requests(file_info['file_uid'])
        


