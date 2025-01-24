from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/play', methods=['POST'])
def play():
    # The game logic is now handled entirely on the frontend
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True)
