import socket
import central_reg
import uuid


field_names = {"id": "user_id", "ip": "ip_address", "active": "active"}
REC_PORT = 8010
DOWN_PORT = 30000

def get_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect(("8.8.8.8", 80))
    ip = sock.getsockname()[0]
    sock.close()
    return ip

def get_mac():
    mac = uuid.getnode()
    hostname = ':'.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2))
    return hostname

def set_user_availability(is_available):
    try:
        
        reg = central_reg.MongoWrapper()        

        hostname = get_mac()
        ip = get_ip()
        cur_user = reg.get_user(hostname)

        new_details_json = {field_names['id']: f"{hostname}", field_names["ip"]: f"{ip}", field_names["active"]: f"{is_available}"}
        
        if cur_user:
            reg.update_data("Peer", cur_user, new_details_json)
            return True
        
        reg.add_data_to_collection("Peer", new_details_json)
        return True

    except socket.error as e:
        print(f"Error: {e}")
        return None
    
def get_active_peers(recv=False):
    reg = central_reg.MongoWrapper()
    peers = reg.get_collection_data("Peer")
    print(peers)
    li = []
    for p in peers:
        print(p)
        if p["active"] == "True" or p["active"] == True:
            if recv:
                li.append(p)
                li[-1]['address'] = (p['ip_address'], REC_PORT)
            else:
                li.append((p['ip_address'], DOWN_PORT))
    print("active peers: ", li)
    return li


if __name__ == "__main__":
    print(get_active_peers(True))
