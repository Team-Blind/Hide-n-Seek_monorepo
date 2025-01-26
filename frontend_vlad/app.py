from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import math

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

game_state = {
    'hider_connected': False,
    'seeker_connected': False,
    'phase': 'placement',
    'current_turn': 'hider'
}

def calculate_distance(hider_pos, seeker_pos):
    dx = hider_pos['x'] - seeker_pos['x']
    dy = hider_pos['y'] - seeker_pos['y']
    return math.ceil(math.sqrt(dx * dx + dy * dy))

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
    # Send complete state information
    emit('game_state_update', {
        'phase': game_state['phase'],
        'current_turn': game_state['current_turn'],
        'hider_connected': game_state['hider_connected'],
        'seeker_connected': game_state['seeker_connected']
    }, broadcast=True)

@socketio.on('move')
def handle_move(data):
    player_type = data['player_type']
    position = data['position']
    
    # Update phase if both players have placed
    if game_state['phase'] == 'placement':
        # Send only own position back to the player
        emit('position_update', {'position': position}, to=request.sid)
        
        if 'placement_count' not in game_state:
            game_state['placement_count'] = 1
            game_state['current_turn'] = 'seeker'
        else:
            game_state['phase'] = 'movement'
            game_state['current_turn'] = 'hider'
            del game_state['placement_count']
    else:
        # Send only own position back to the player
        emit('position_update', {'position': position}, to=request.sid)
        game_state['current_turn'] = 'seeker' if player_type == 'hider' else 'hider'
    
    # Request other player's position to calculate distance
    emit('request_position', {'from_player': player_type, 'position': position}, broadcast=True)
    
    # Broadcast game state without positions
    emit('game_state_update', {
        'phase': game_state['phase'],
        'current_turn': game_state['current_turn']
    }, broadcast=True)

@socketio.on('position_response')
def handle_position_response(data):
    # Calculate and broadcast distance when we have both positions
    distance = calculate_distance(data['hider_pos'], data['seeker_pos'])
    emit('distance_update', {'distance': distance}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
