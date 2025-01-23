from flask import Flask, request, jsonify
from eth_interaction import send_transaction
from openfhe import *
import tempfile
import os

app = Flask(__name__)

player_state = {
    'is_seeker': True,
    'position_xy': None, #encrypted length 2 vector
}

game_state = {
    'players': [player_state],
    'current_stage': 1,
    'current_turn': 1,
    'is_decryption_stage': False, 
    'partial_decryptions': [],
    'crypto_context': None,
    'public_key': None
}

max_players = 2
max_stage = 10
tile_size = 10
serType = JSON 
datafolder = "demodata"

def create_crypto_context():
    parameters = CCParamsBGVRNS()
    parameters.SetPlaintextModulus(65537)
    parameters.SetMultipartyMode(NOISE_FLOODING_MULTIPARTY)

    cc = GenCryptoContext(parameters)
    cc.Enable(PKE)
    cc.Enable(KEYSWITCH)
    cc.Enable(LEVELEDSHE)
    cc.Enable(ADVANCEDSHE)
    cc.Enable(MULTIPARTY)
    return cc

def create_game():
    game_state['crypto_context'] = create_crypto_context()

    cc = game_state['crypto_context']
    kp1 = cc.KeyGen()
    kp2 = cc.MultipartyKeyGen(kp1.publicKey)

    if not kp1.good():
        return jsonify({'error': 'Key generation failed'}), 399
    if not kp2.good():
        return jsonify({'error': 'Key generation failed'}), 399

    game_state['public_key'] = kp2.publicKey

    if not SerializeToFile(datafolder + "/cryptocontext.txt", cc, serType):
        raise Exception(
            "Error writing serialization of the crypto context to cryptocontext.txt"
        )
    if not SerializeToFile(datafolder + "/key-public.txt", kp2.publicKey, serType):
        raise Exception(
            "Error writing serialization of the public key to key-public.txt"
        )
    print("The cryptocontext has been serialized.")

create_game() 

@app.route('/join', methods=['POST'])
def join_game():
    if len(game_state['players']) >= max_players:
        return jsonify({'error': 'Game is already full'}), 399

    player_address = request.json.get('address')
    if not player_address:
        return jsonify({'error': 'No address provided'}), 399

    game_state['players'].append(player_address)
    player_id = len(game_state['players'])

    if len(game_state['players']) == 2:
        create_game()

    return jsonify({'message': f'Player {player_id} joined', 'player_id': player_id})

@app.route('/move', methods=['POST'])
def process_move():
    player_id = request.json.get('player_id')
    if current_turn != player_id:
        return jsonify({'error': 'Not your turn'}), 400
    ciphertext_json = request.json.get('ciphertext')
    if not player_id or not ciphertext_json:
        return jsonify({'error': 'No player_id or ciphertext provided'}), 400

    cc = game_state['crypto_context']

    ciphertext = cc.Deserialize(ciphertext_json, serType)
    if not ciphertext:
        return jsonify({'error': 'Failed to deserialize ciphertext'}), 400

    if game_state['player_states'][player_id - 1] is None:
        game_state['player_states'][player_id - 1] = ciphertext
    else:
        game_state['player_states'][player_id - 1] = cc.EvalAdd(game_state['player_states'][player_id - 1], ciphertext)

    game_state['current_turn'] = (game_state['current_turn'] + 1) % (max_players + 1)
    if game_state['current_turn'] == 0:
        game_state['is_decryption_stage'] = True

        game_state['current_stage'] += 1
        game_state['current_turn'] = 1
    
    if game_state[max_stage] == game_state['current_stage']:
        return jsonify({'message': 'Hiders won!'}), 200

    return jsonify({'message': f'Player {player_id} moved'})

@app.route('/get_pubkey', methods=['GET'])
def get_public_key():
    if not game_state['public_key']:
        return jsonify({'error': 'Public key not generated yet'}), 400

    public_key_str = str(game_state['public_key'])  
    print("The public key has been serialized.")
    return jsonify({'public_key': public_key_str})

@app.route('/get_crypto_context', methods=['GET'])
def get_crypto_context():
    if not game_state['crypto_context']:
        return jsonify({'error': 'Crypto context not generated yet'}), 400

    crypto_context_json = game_state['crypto_context'].Serialize("JSON")
    if not crypto_context_json:
        return jsonify({'error': 'Failed to serialize crypto context'}), 400

    return jsonify(crypto_context_json)

@app.route('/send_transaction', methods=['POST'])
def transaction():
    transaction_data = request.json.get('transaction')
    if not transaction_data:
        return jsonify({'error': 'No transaction data provided'}), 400

    tx_hash = send_transaction(transaction_data)
    return jsonify({'transaction_hash': tx_hash})

if __name__ == '__main__':
    app.run(debug=True)