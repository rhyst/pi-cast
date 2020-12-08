import os
import magic
from flask import Flask, render_template, send_file, abort, redirect, request, jsonify
from funcy import some
from cast_controller import CastController


BASE_DIR = os.getenv('BASE_DIR', '/data')
PUBLIC_URL = os.getenv('PUBLIC_URL', 'http://192.168.0.2:8085')
DEFAULT_DEVICE = os.getenv('DEFAULT_DEVICE', 'Living Room')
PORT = int(os.getenv('PORT', '8085'))

mime = magic.Magic(mime=True)
cc = CastController(DEFAULT_DEVICE)
app = Flask(__name__)

# HTML

@app.route('/', defaults={'req_path': ''})
@app.route('/<path:req_path>')
def dir_listing(req_path):
    if not cc.device and len(cc.available_devices) > 0:
        cc.device = cc.available_devices[0]

    abs_path = os.path.join(BASE_DIR, req_path)

    if not os.path.exists(abs_path):
        return abort(404)

    if os.path.isfile(abs_path):
        return send_file(abs_path)

    files = []
    directories = []
    for name in os.listdir(abs_path):
        if name[0] == '.':
            continue
        abs_item_path = os.path.join(abs_path, name)
        is_dir = os.path.isdir(abs_item_path)
        mime_type = 'dir' if is_dir else mime.from_file(abs_item_path)
        item = {
            "path": os.path.relpath(abs_item_path, BASE_DIR),
            "name": name,
            "is_media": mime_type.startswith('video/') or  mime_type.startswith('audio/')
        }
        if is_dir:
            directories.append(item)
        else:
            files.append(item)
    return render_template('index.html', status=cc.get_status(), directories=directories, files=files, casts=cc.available_devices, current_cast=cc.device.name)

# JSON

@app.route('/status', methods=['GET'])
def status():
    return jsonify({ "ok": True, "status": cc.get_status() })

@app.route('/cast', methods=['POST'])
def cast():
    req_path = request.json.get('request_path')
    abs_path = os.path.join(BASE_DIR, req_path)
    cc.play('http://192.168.0.99:8085/' + req_path, mime.from_file(abs_path), os.path.basename(abs_path))
    return jsonify({ "ok": True, "status": cc.get_status() })
 
@app.route('/device', methods=['POST'])
def set_device():
    cc.set_device(request.json.get('device'))
    return jsonify({ "ok": True, "status": cc.get_status() })

@app.route('/volume', methods=['POST'])
def set_volume():
    cc.set_volume(request.json.get('volume'))
    return jsonify({ "ok": True, "status": cc.get_status() })

@app.route('/play', methods=['POST'])
def resume():
    cc.resume()
    return jsonify({ "ok": True, "status": cc.get_status() })

@app.route('/pause', methods=['POST'])
def pause():
    cc.pause()
    return jsonify({ "ok": True, "status": cc.get_status() })

@app.route('/stop', methods=['POST'])
def stop():
    cc.stop()
    return jsonify({ "ok": True, "status": cc.get_status() })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=PORT)
