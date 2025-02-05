from flask import Flask, render_template, request, make_response
from flask_socketio import SocketIO, emit, join_room
import json

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Game state initialization
game_state = {
    'hider_connected': False,
    'seeker_connected': False,
    'phase': 'placement',
    'current_turn': 'hider',
    'positions': {}
}

ROOM_NAME = 'hide_and_seek'

@app.route('/')
def index():
    """Serve the main game page with CSP header."""
    player_type = request.args.get('player_type', 'hider')

    # Render and add CSP to the response
    response = make_response(render_template('index.html', player_type=player_type))
    response.headers['Content-Security-Policy'] = "script-src 'self' 'unsafe-eval' https://pyscript.net https://cdn.socket.io https://cdn.jsdelivr.net;"


    return response

@socketio.on('join')
def handle_join(data):
    """Handle player joining the game."""
    data = json.loads(data)
    player_type = data['player_type']
    join_room(ROOM_NAME)

    # Log for debugging
    print(f"Player {player_type} joined.")

    # Update game state
    if player_type == 'hider':
        game_state['hider_connected'] = True
    elif player_type == 'seeker':
        game_state['seeker_connected'] = True

    # Notify both players once they're connected
    if game_state['hider_connected'] and game_state['seeker_connected']:
        print("Both players connected. Emitting game state.")
        emit('game_state_update', json.dumps(game_state), room=ROOM_NAME)

@socketio.on('move')
def handle_move(data):
    """Handle player move."""
    data = json.loads(data)
    player_type = data['player_type']
    position = data['position']

    # Placement phase
    if game_state['phase'] == 'placement':
        game_state['positions'][player_type] = position
        print(f"{player_type} placed position: {position}")

        # Transition to movement phase if both players have placed positions
        if 'hider' in game_state['positions'] and 'seeker' in game_state['positions']:
            game_state['phase'] = 'movement'
            game_state['current_turn'] = 'hider'
            print("Both players placed positions. Transitioning to movement phase.")
            emit('game_state_update', json.dumps(game_state), room=ROOM_NAME)

    # Movement phase
    elif game_state['phase'] == 'movement':
        if game_state['current_turn'] != player_type:
            emit('invalid_move', json.dumps({'message': 'Not your turn!'}), room=ROOM_NAME)
            return

        game_state['positions'][player_type] = position
        print(f"{player_type} moved to: {position}")

        # Switch turns
        game_state['current_turn'] = 'seeker' if player_type == 'hider' else 'hider'
        emit('game_state_update', json.dumps(game_state), room=ROOM_NAME)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001)
