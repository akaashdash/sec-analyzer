import os
import numpy as np
from flask import Flask, request, send_from_directory, jsonify
from flask_cors import CORS

app = Flask(__name__, static_folder='./frontend/build', static_url_path='/')
CORS(app)

@app.route('/')
def index():
    return send_from_directory(app.static_folder,'index.html')
    

# @app.errorhandler(404)
# def not_found(e):
#     return app.send_static_file('index.html')

@app.route('/company')
def getCompanyData():
    ticker, year = request.args.get('ticker'), request.args.get('year')
    return jsonify({"ticker": "PLTR", "year": 2021})

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=False, port=os.environ.get('PORT', 80))