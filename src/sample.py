from flask import Flask, render_template, request

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_compile')
def get_compile():
    code = request.args.get('code')
    return code

@app.route('/post_compile')
def post_compile():
    code = request.form.get('code')
    return code


if __name__ == "__main__":
    app.run(debug=True)
