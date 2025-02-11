from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import math

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

game_state = {
    'hider_connected': False,
    'seeker_connected': False,
    'phase': 'placement',
    'current_turn': 'hider',
    'positions': {}
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
    game_state[f'{player_type}_connected'] = True

    # Debug: Log connections
    print(f"[DEBUG] {player_type} connected. Current game state: {game_state}")

    # Send updated game state to all players
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

    # Debug: Log move event
    print(f"[DEBUG] {player_type} moved to {position}")

    # Handle placement phase
    if game_state['phase'] == 'placement':
        # Store player's position
        game_state['positions'][player_type] = position

        # Debug: Log placement update
        print(f"[DEBUG] {player_type} position set. Current positions: {game_state['positions']}")

        # Send the position back to the player
        emit('position_update', {'position': position}, to=request.sid)

        # Check if both players have placed their positions
        if 'hider' in game_state['positions'] and 'seeker' in game_state['positions']:
            game_state['phase'] = 'movement'
            game_state['current_turn'] = 'hider'  # Hider starts the movement phase

            # Debug: Log phase transition
            print("[DEBUG] Both players placed positions. Transitioning to movement phase.")

            # Notify all players of the updated game state
            emit('game_state_update', {
                'phase': game_state['phase'],
                'current_turn': game_state['current_turn']
            }, broadcast=True)
        else:
            # Notify the player that their position is set
            emit('game_state_update', {
                'phase': game_state['phase'],
                'current_turn': game_state['current_turn'],
                'message': 'Position set. Waiting for opponent.'
            })
        return

    # Handle movement phase
    if game_state['phase'] == 'movement':
        if game_state['current_turn'] != player_type:
            emit('invalid_move', {'message': 'Not your turn!'}, to=request.sid)
            return

        # Update the position and change the turn
        game_state['positions'][player_type] = position
        game_state['current_turn'] = 'seeker' if player_type == 'hider' else 'hider'

        # Request opponent's position to calculate the distance
        emit('request_position', {'from_player': player_type, 'position': position}, broadcast=True)

        # Notify players of the updated game state
        emit('game_state_update', {
            'phase': game_state['phase'],
            'current_turn': game_state['current_turn']
        }, broadcast=True)

@socketio.on('position_response')
def handle_position_response(data):
    # Calculate and broadcast distance when both positions are available
    hider_pos = game_state['positions'].get('hider')
    seeker_pos = game_state['positions'].get('seeker')

    if hider_pos and seeker_pos:
        distance = calculate_distance(hider_pos, seeker_pos)
        emit('distance_update', {'distance': distance}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
