from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
import math

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")


game_state = {
    'hider_connected': False,
    'seeker_connected': False,
    'phase': 'placement',
    'current_turn': None
}

ROOM_NAME = 'hide_and_seek'

@app.route('/')
def index():
    """Serve the game interface."""
    player_type = request.args.get('player_type', 'hider')
    return render_template('index.html', player_type=player_type)

@socketio.on('join')
def handle_join(data):
    """Handle player joining the game."""
    player_type = data['player_type']
    join_room(ROOM_NAME)

    if player_type == 'hider':
        game_state['hider_connected'] = True
    elif player_type == 'seeker':
        game_state['seeker_connected'] = True

    if game_state['hider_connected'] and game_state['seeker_connected']:
        game_state['phase'] = 'placement'
        game_state['current_turn'] = 'hider'

    emit('game_state_update', game_state, room=ROOM_NAME)

@socketio.on('move')
def handle_move(data):
    """Request the other player's position to calculate distance."""
    player_type = data['player_type']
    position = data['position']

    # Emit a position request to the other player
    emit('request_position', {'from_player': player_type, 'position': position}, room=ROOM_NAME)

@socketio.on('position_response')
def handle_position_response(data):
    """Calculate distance when both positions are available."""
    hider_pos = data['hider_pos']
    seeker_pos = data['seeker_pos']
    distance = calculate_distance(hider_pos, seeker_pos)

    # Emit the distance to all players
    emit('distance_update', {'distance': distance}, room=ROOM_NAME)

def calculate_distance(pos1, pos2):
    """Calculate the Euclidean distance between two positions and round up."""
    dx = pos1['x'] - pos2['x']
    dy = pos1['y'] - pos2['y']
    return math.ceil(math.sqrt(dx ** 2 + dy ** 2))

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001)
