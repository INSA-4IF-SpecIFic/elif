from flask import Flask, render_template, request
import requests
from compilation import Compilation
import json

app = Flask(__name__)

@app.route('/')
def hello():
    return render_template('index.html')


@app.route('/compile', methods=['POST'])
def compile():
    code = request.json['code']

    comp = Compilation(code)
    result = {'stderr': comp.stderr, 'stdout': 'lol'}
    return json.dumps(result)

@app.route('/get_compile')
def get_compile():
    code = request.args.get('code')
    comp = Compilation(code)
    result = {'stderr': comp.stderr, 'stdout': 'lol'}
    return json.dumps(result)

def post_test():
    r = requests.post('http://localhost:5000/post_compile', data={'code':'lol'})
    return r

if __name__ == "__main__":
    app.run(debug=True)

