from flask import Flask, jsonify, request
import subprocess
import asyncio
from flask_cors import CORS, cross_origin
import json
from threading import Thread
import os
import signal

from userdetails import set_user_availability, get_active_peers
from collector import setup_recieve_data
from download import make_download_requests, request_download
from distributor import Sender
from central_reg import MongoWrapper
from file_utils import stitch_partfiles

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
global conf
conf = False

def run_asyncio_loop():
    asyncio.run(setup_recieve_data())

@app.route("/startup", methods=["POST"])
def setup():
    global conf
    print("Sent")
    if not conf:
        asyncio_thread = Thread(target=run_asyncio_loop)
        asyncio_thread.start()
        conf = True
        dic = {"status": 201, "message": "Setup done"}
        return jsonify(dic)
    return jsonify({"status":400, "message": "already done"})


@app.route("/deactivate",methods=["PUT"])
def close():
    success = set_user_availability(False)
    if not success:
        dic = {"status": 500, "message": "Internal Error"}
        res = jsonify(dic)
        return res
    else:
        res = jsonify({"status": 200, "message": "UPDATED"})
        return res

@app.route("/update", methods=["PUT"])
@cross_origin()
def update_peer():
    success = set_user_availability(True)
    if not success:
        dic = {"status": 500, "message": "Internal Error"}
        res = jsonify(dic)
        return res
    else:
        res = jsonify({"status": 200, "message": "UPDATED"})
        return res


@app.route('/get_files', methods=["GET"])
@cross_origin()
def get_files():
    db = MongoWrapper()
    data = list(db.get_collection_data('File'))
    for i in range(len(data)):
        data[i]['_id'] = str(data[i]['_id'])
    return jsonify({"data": data})

@app.route('/', methods=["POST"])
def test():
    print(request.data)
    return jsonify({"status": 200, "message": "Hello from torrent server"})


@app.route("/upload", methods=["POST"])
@cross_origin()
def upload_file():
    data = request.data.decode('utf-8').replace("'",'"')
    data = json.loads(data)

    peers = get_active_peers(True)

    if len(peers) == 0:
        res = jsonify({"message": "No active peers found"})
        res.status_code = 404
        return res

    s = Sender()
    s.upload_file(data['file'], peers)
    dic = {"status": 201, "message": "Uploading file"}
    response = jsonify(dic)
    return response


@app.route("/download/<file_uid>", methods=["GET"])
@cross_origin()
def download_file(file_uid):
    summary = make_download_requests(file_uid)
    summary = json.loads(summary)
    if summary['status'] != "Success!":
        return jsonify({"status": 404, "message": "No active user found!"})
    stitch_partfiles(summary['file_info'])
    return jsonify({"status": 200, "message": "Downloaded!"})

@app.route("/download/request", methods=["POST"])
@cross_origin()
def request_part():
    data = request.json
    data = json.loads(data)
    if request_download(data['file_info'], data['seeder_info']):
        return "Success"
    else:
        return "Something went wrong"


if __name__ == "__main__":
    app.run(host="0.0.0.0")
