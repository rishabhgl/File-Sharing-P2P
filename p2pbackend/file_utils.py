import base64
import os

from central_reg import MongoWrapper
    

def break_file(filepath, chunk_size):

    with open(filepath, 'rb') as file:
        content = file.read()
        i = 0
        parts = []
        while True:
            part = b''
            if i + chunk_size >= len(content):
                part = content[i:]
                part = base64.b64encode(part).decode('utf-8')
                parts.append(part)
                break
            else:
                part = content[i:i+chunk_size]
                part = base64.b64encode(part).decode('utf-8')
            parts.append(part)
            i += chunk_size
        return parts


def stitch_file(file_parts):
    x = b''
    for part in file_parts:
        x += part
    return x

def stitch_partfiles(file_info):
    SHARE_PATH = f'/home/{os.getlogin()}/.localran/'

    partspath = os.path.join(SHARE_PATH, f"{file_info['name']}-{file_info['timestamp']}-2")
    file_data = b''
    parts = []
    try:
        for part in range(int(file_info['total_parts'])):
            partpath = os.path.join(partspath, f"{part}.part{file_info['type']}")
            if os.path.exists(partpath) == False:
                raise FileExistsError("Required part does not exist")
            with open(partpath, "rb") as part_desc:
                    part_data = part_desc.read()
                    parts += [part_data]
                    
        file_data = stitch_file(parts)

        filepath = os.path.join(SHARE_PATH, "downloads", f"{file_info['name']}_{file_info['_id']}")
        stitched_file_path = os.path.join(filepath, f"file{file_info['type']}")

        os.makedirs(filepath, exist_ok=True)

        with open(stitched_file_path, "wb+") as file:
            file.write(file_data)
            
    except Exception as e:
        print("Could not stitch file")
        print(e)
        return e
    


