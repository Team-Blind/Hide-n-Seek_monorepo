from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

game_state = {
    'hider_connected': False,
    'seeker_connected': False,
    'phase': 'placement',
    'hider_position': None,
    'seeker_position': None,
    'current_turn': 'hider'
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/join/<player_type>')
def join_game(player_type):
    if player_type not in ['hider', 'seeker']:
        return 'Invalid player type', 400
    return render_template('game.html', player_type=player_type)

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('join')
def handle_join(data):
    player_type = data['player_type']
    if player_type == 'hider':
        game_state['hider_connected'] = True
    else:
        game_state['seeker_connected'] = True
    emit('game_state_update', game_state, broadcast=True)

@socketio.on('move')
def handle_move(data):
    position = data['position']
    player_type = data['player_type']
    
    if player_type == 'hider':
        game_state['hider_position'] = position
        game_state['current_turn'] = 'seeker'
    else:
        game_state['seeker_position'] = position
        game_state['current_turn'] = 'hider'
    
    if game_state['phase'] == 'placement' and game_state['hider_position'] and game_state['seeker_position']:
        game_state['phase'] = 'movement'
    
    emit('game_state_update', game_state, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
