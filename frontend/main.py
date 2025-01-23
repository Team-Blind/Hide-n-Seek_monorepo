from openfhe import *
import requests
import json

serType = JSON 
datafolder = "demodata"

player_id = 0 

def main():
    cc = get_crypto_context_from_server()
    public_key = get_public_key_from_server()

    direction = input("이동할 방향을 입력하세요 (up, down, left, right): ")
    vector = direction_to_vector(direction)

    ciphertext = encrypt_message(vector, public_key, cc)

    send_to_server(ciphertext)

    while True:
        game_state = get_game_state_from_server()
        if game_state['is_decryption_stage']:
            perform_decryption_stage(cc)
            break

        direction = input("이동할 방향을 입력하세요 (up, down, left, right): ")
        vector = direction_to_vector(direction)

        ciphertext = encrypt_message(vector, public_key, cc)

        send_to_server(ciphertext)

        time.sleep(5)  # 5초마다 서버 상태 확인

def get_crypto_context_from_server():
    response = requests.get('http://127.0.0.1:5000/get_crypto_context')
    if response.status_code != 200:
        raise Exception("Failed to get crypto context from server")
    
    crypto_context_json = response.json()
    cc = DeserializeCryptoContext(datafolder + "/cryptocontext.txt", serType)
    return cc

def get_public_key_from_server():
    response = requests.get('http://127.0.0.1:5000/get_pubkey')
    if response.status_code != 200:
        raise Exception("Failed to get public key from server")
    
    public_key_json = response.json()['public_key']
    public_key = DeserializePublicKey(datafolder + "/key-public.txt", serType)
    return public_key

def direction_to_vector(direction):
    if direction == "up":
        return [0, 0]
    elif direction == "down":
        return [0, 1]
    elif direction == "left":
        return [1, 0]
    elif direction == "right":
        return [1, 1]
    else:
        raise ValueError("Invalid direction")

def encrypt_message(vector, public_key, cc):
    plaintext = cc.MakePackedPlaintext(vector)
    ciphertext = cc.Encrypt(public_key, plaintext)
    return ciphertext

def send_to_server(ciphertext):
    filepath = "/path/to/ciphertext.json"
    if not SerializeToFile(filepath, ciphertext, "JSON"):
        raise Exception("Error writing serialization of ciphertext to file")

    with open(filepath, 'r') as file:
        ciphertext_json = file.read()

    response = requests.post('http://127.0.0.1:5000/move', json={'player_id': 1, 'ciphertext': ciphertext_json})
    if response.status_code != 200:
        raise Exception("Failed to send ciphertext to server")

    print("Ciphertext sent to server successfully")

def get_game_state_from_server():
    response = requests.get('http://127.0.0.1:5000/get_game_state')
    if response.status_code != 200:
        raise Exception("Failed to get game state from server")
    
    return response.json()

def perform_decryption_stage(cc, kp, ciphertext):
    print("Decryption stage started")
    # Decryption logic here
    partial_decryption = cc.MultipartyDecryptLead([ciphertext], kp.secretKey)
    response = requests.post('http://127.0.0.1:5000/decryption', json={'player_id': 1, 'partial_decryption': partial_decryption})


if __name__ == "__main__":
    main()