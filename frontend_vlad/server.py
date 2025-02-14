import json
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from flask_talisman import Talisman

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
        "'unsafe-inline'",  # 
        "'unsafe-eval'" 
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
    'img-src': ["'self'", "data:"], 
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
    'positions': {},
    'distance': None
}

def calculate_distance(hider_pos, seeker_pos):
    dx = abs(hider_pos['x'] - seeker_pos['x'])
    dy = abs(hider_pos['y'] - seeker_pos['y'])
    return dx + dy

@app.route('/')
def index():
    # Reset game state to initial values
    global game_state
    game_state = {
        "phase": "placement",
        "positions": {},
        "current_turn": "hider",
        "distance": None,
        "hider_connected": False,
        "seeker_connected": False
    }
    return render_template('index.html')

@app.route('/join/<player_type>')
def join_game(player_type):
    if player_type not in ['hider', 'seeker']:
        return 'Invalid player type', 400
    return render_template('game.html', player_type=player_type)

@app.route('/game-over')
def game_over():
    result = request.args.get('result')
    return render_template('game_over.html', result=result)

@socketio.on('connect')
def handle_connect():
    print("[DEBUG] Client connected")

@socketio.on('join')
def handle_join(data):
    """Ensure data is properly parsed as a dictionary"""
    if isinstance(data, str):  
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            
            return emit("error", {"message": "Invalid JSON format"})

    if not isinstance(data, dict) or "player_type" not in data:
        
        return emit("error", {"message": "Missing player_type"})

    player_type = data["player_type"]

    if player_type not in ["hider", "seeker"]:
        print(f"[DEBUG] Invalid player type: {player_type}")
        return emit("error", {"message": "Invalid player type"})

    game_state[f"{player_type}_connected"] = True
    

    emit("game_state_update", {
        "phase": game_state["phase"],
        "current_turn": game_state["current_turn"],
        "hider_connected": game_state["hider_connected"],
        "seeker_connected": game_state["seeker_connected"]
    }, broadcast=True)

import json

@socketio.on('placed')
def handle_placed(data):
    """Handle player moves and transition game state when needed."""
    print(f"[DEBUG] Received placed data: {data}")

    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            print("[ERROR] Received invalid JSON in 'placed' event")
            return

    if not isinstance(data, dict) or "player_type" not in data or "position" not in data:
        print("[ERROR] Invalid placed data format.")
        return

    if game_state["phase"] != "placement":
        print("[DEBUG] Not in placement phase, ignoring placed event.")
        return

    player_type = data["player_type"]
    position = data["position"]

    print(f"[DEBUG] {player_type} placed at {position}")

    game_state["positions"][player_type] = position
    if ('hider' in game_state['positions'] and 'seeker' in game_state['positions']):
        game_state["phase"] = "movement"
        print("[DEBUG] Transitioning to movement phase.")

    if game_state["phase"] == "movement":
        game_state["distance"] = calculate_distance(game_state["positions"]["hider"], game_state["positions"]["seeker"])

    emit('game_state_update', game_state, broadcast=True)

@socketio.on('move')
def handle_move(data):
    """Handle player moves and transition game state when needed."""
    print(f"[DEBUG] Received move data: {data}")

    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            print("[ERROR] Received invalid JSON in 'move' event")
            return

    if not isinstance(data, dict) or "player_type" not in data or "position" not in data:
        print("[ERROR] Invalid move data format.")
        return
    
    if game_state["phase"] != "movement":
        print("[DEBUG] Not in movement phase, ignoring move event.")
        return

    player_type = data["player_type"]
    position = data["position"]

    print(f"[DEBUG] {player_type} moved to {position}")

    game_state["positions"][player_type] = position
    game_state["current_turn"] = "seeker" if player_type == "hider" else "hider"
    game_state["distance"] = calculate_distance(game_state["positions"]["hider"], game_state["positions"]["seeker"])

    print(f"[DEBUG] Distance: {game_state['distance']}")
    if game_state["distance"] <= 1:
        game_state["phase"] = "end"
        print("[DEBUG] Transitioning to end phase.")
        emit('game_end', game_state, broadcast=True)
        print("[DEBUG] Game over.")
    else:
        emit('game_state_update', game_state, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
