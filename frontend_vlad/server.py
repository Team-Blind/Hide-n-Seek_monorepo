import json
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from flask_talisman import Talisman
import math
import logging

# Set up logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", transports=['websocket', 'polling'])

csp = {
    'default-src': [
        "'self'",
        'https://pyscript.net',
        'https://cdn.socket.io',
        'https://cdn.jsdelivr.net'
    ],
    'script-src': [
        "'self'",
        'https://pyscript.net',
        'https://cdn.socket.io',
        'https://cdn.jsdelivr.net',
        "'unsafe-inline'",  # ✅ Allow inline scripts
        "'unsafe-eval'"  # ✅ Allow PyScript execution
    ],
    'style-src': [
        "'self'",
        "'unsafe-inline'",
        'https://pyscript.net'
    ],
    'style-src-elem': [
        "'self'",
        "'unsafe-inline'",
        'https://pyscript.net'
    ],
    'img-src': ["'self'", "data:"],  # ✅ Allow images & base64 images
    'connect-src': [
        "'self'",
        'ws://localhost:5001', 'wss://localhost:5001',
        'ws://127.0.0.1:5001', 'wss://127.0.0.1:5001',
        'https://cdn.jsdelivr.net',
        'https://cdn.jsdelivr.net/pyodide/'
    ]
}


Talisman(app, content_security_policy=csp)


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
    logger.debug('Client connected')

@socketio.on('join')
def handle_join(data):
    """Ensure data is properly parsed as a dictionary"""
    logger.debug(f"Received join event with raw data: {data}")

    if isinstance(data, str):  # ✅ Convert JSON string to dictionary if needed
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            logger.error("[ERROR] Failed to parse JSON from join event.")
            return emit("error", {"message": "Invalid JSON format"})

    if not isinstance(data, dict) or "player_type" not in data:
        logger.error("[ERROR] Missing 'player_type' key in received data.")
        return emit("error", {"message": "Missing player_type"})

    player_type = data["player_type"]

    if player_type not in ["hider", "seeker"]:
        logger.error(f"[ERROR] Invalid player type received: {player_type}")
        return emit("error", {"message": "Invalid player type"})

    game_state[f"{player_type}_connected"] = True
    logger.debug(f"{player_type} connected. Current game state: {game_state}")

    emit("game_state_update", {
        "phase": game_state["phase"],
        "current_turn": game_state["current_turn"],
        "hider_connected": game_state["hider_connected"],
        "seeker_connected": game_state["seeker_connected"]
    }, broadcast=True)


@socketio.on('move')
def handle_move(data):
    logger.debug(f"[DEBUG] Received move data: {data}")

    player_type = data['player_type']
    position = data['position']

    logger.debug(f"[DEBUG] {player_type} moved to {position}")

    if game_state['phase'] == 'placement':
        game_state['positions'][player_type] = position

        logger.debug(f"[DEBUG] {player_type} position set. Current positions: {game_state['positions']}")

        if 'hider' in game_state['positions'] and 'seeker' in game_state['positions']:
            game_state['phase'] = 'movement'
            game_state['current_turn'] = 'hider'

            logger.debug("[DEBUG] Transitioning to movement phase.")

            emit('game_state_update', {
                'phase': game_state['phase'],
                'current_turn': game_state['current_turn'],
                'hider_connected': game_state['hider_connected'],
                'seeker_connected': game_state['seeker_connected']
            }, broadcast=True)
        else:
            emit('game_state_update', {
                'phase': game_state['phase'],
                'current_turn': game_state['current_turn'],
                'message': 'Position set. Waiting for opponent.'
            })

@socketio.on('position_response')
def handle_position_response(data):
    hider_pos = game_state['positions'].get('hider')
    seeker_pos = game_state['positions'].get('seeker')

    if hider_pos and seeker_pos:
        distance = calculate_distance(hider_pos, seeker_pos)
        emit('distance_update', {'distance': distance}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
