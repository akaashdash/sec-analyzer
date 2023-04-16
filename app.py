import os
import numpy as np
from flask import Flask, request, send_from_directory, jsonify, send_file
from flask_cors import CORS
from edgar import CompanyFactory
import datetime

app = Flask(__name__, static_folder='./frontend/build', static_url_path='/')
CORS(app)
cf = CompanyFactory()
CURR_YEAR = datetime.date.today().year

@app.route('/')
def index():
    return app.send_static_file('index.html')
    return send_from_directory(app.static_folder, 'index.html')
    
@app.errorhandler(404)
def not_found(e):
    return app.send_static_file('index.html')
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/company/wordcloud')
def getCompanyWordCloud():
    ticker, year = request.args.get('ticker'), int(request.args.get('year'))
    if year < 2000 or year > CURR_YEAR:
        return "Invalid Year", 400
    company = cf.from_ticker(ticker, year=int(year))
    if company is None:
        return "Invalid Ticker", 400
    filing = company.get_filing(int(year))
    if filing is None:
        return "No Filing For Year", 400
    return send_file(filing.get_wordcloud(), mimetype='image/gif')

@app.route('/company/knowledgegraph')
def getCompanyKnowledgeGraph():
    ticker, year = request.args.get('ticker'), int(request.args.get('year'))
    if year < 2000 or year > CURR_YEAR:
        return "Invalid Year", 400
    company = cf.from_ticker(ticker, year=int(year))
    if company is None:
        return "Invalid Ticker", 400
    filing = company.get_filing(int(year))
    if filing is None:
        return "No Filing For Year", 400
    return send_file(filing.get_knowledgegraph(), mimetype='image/gif')

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=False, port=os.environ.get('PORT', 80))