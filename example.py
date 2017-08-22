from flask import Flask, jsonify, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import uuid
import json, ast
import os, sys
import socket
import base64
from pyPdf import PdfFileReader, PdfFileWriter
from tempfile import NamedTemporaryFile
import glob
from PythonMagick import Image
import shutil
import unicodedata
import io
from google.cloud import vision
import requests
url = 'https://vision.googleapis.com/v1/images:annotate?key=API-KEY'
vision_client = vision.Client()
app = Flask(__name__)
UPLOAD_FOLDER = './upload'
IMAGE_FOLDER = './images'
TEXT_FOLDER = './text'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg'])
basedir = os.path.abspath(os.path.dirname(__file__))


@app.route('/textocr', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        name = os.path.splitext(file.filename)[0]
        extension = os.path.splitext(file.filename)[1]
        f_name = name + extension
        if extension == ".pdf":
            file.save(os.path.join(basedir,UPLOAD_FOLDER , f_name))
            filepath = os.path.join('./upload', f_name)
            os.makedirs(os.path.join("./images", name))
            filepath1 = os.path.join('./images', name)
            reader = PdfFileReader(open(filepath, "rb"))
            for page_num in xrange(reader.getNumPages()):
                writer = PdfFileWriter()
                writer.addPage(reader.getPage(page_num))
                temp = NamedTemporaryFile(prefix=str(page_num), suffix=".pdf", delete=False)
                writer.write(temp)
                temp.close()
                im = Image()
                im.density("300")  # DPI, for better quality
                im.read(temp.name)
                im.write("images/%s/ %d.jpg" % (str(name), page_num))
                os.remove(temp.name)
            os.remove(filepath)
            dirs = os.listdir(filepath1)
            dict = {}
            i = 0
            dict["file_name"] = f_name
            for file in dirs:
                filepath2 = os.path.join(filepath1, file)
                with io.open(filepath2, 'rb') as image_file:
                    content= base64.b64encode(image_file.read())
                    payload = {
                        "requests": [
                            {
                                "image": {
                                    "content": content
                                },
                                "features": [
                                    {
                                        "type": "TEXT_DETECTION"
                                    }
                                ]
                            }
                        ]
                    }
                r = requests.post(url, data=json.dumps(payload))
                r = json.loads(r.text)
                r=r['responses'][0]['textAnnotations'][0]['description']
                key = "page_no-" + str(file)
                dict[key] = r
            shutil.rmtree(filepath1)
            return json.dumps(dict)
        elif extension == '.png' or extension == '.jpg' or extension == '.jpeg':
            dict = {}
            dict["file_name"] = f_name
            file.save(os.path.join(basedir, UPLOAD_FOLDER, f_name))
            filepath = os.path.join('./upload', f_name)
            with io.open(filepath, 'rb') as image_file:
                content = base64.b64encode(image_file.read())
                payload = {
                    "requests": [
                        {
                            "image": {
                                "content": content
                            },
                            "features": [
                                {
                                    "type": "TEXT_DETECTION"
                                }
                            ]
                        }
                    ]
                }
            r = requests.post(url, data=json.dumps(payload))
            r=json.loads(r.text)
            r=r['responses'][0]['textAnnotations'][0]['description']
            dict["text"] = r
            os.remove(filepath)
            return json.dumps(dict)
        else:
            return json.dumps({'file format is wrong': f_name})

    return json.dumps({'file proess completed': f_name})


if __name__ == '__main__':
    app.run(debug=True, port=8080, threaded=True)