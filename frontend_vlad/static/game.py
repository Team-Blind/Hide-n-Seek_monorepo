from js import document, console
from pyodide.ffi import create_proxy
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import base64

class HideAndSeekGame:
    def __init__(self):
        self.game_board = document.getElementById('gameBoard')
        self.game_status = document.getElementById('gameStatus')
        self.reset_btn = document.getElementById('resetBtn')
        self.hider_position = None
        self.seeker_position = None
        self.game_phase = 'hiding'
        self.encryption_key = get_random_bytes(16)  # AES key size

        self.create_board()
        self.reset_btn.addEventListener('click', create_proxy(self.reset_game))

    def create_board(self):
        self.game_board.innerHTML = ''
        for i in range(16):
            cell = document.createElement('div')
            cell.className = 'cell'
            cell.dataset.index = str(i)
            cell.addEventListener('click', create_proxy(self.handle_cell_click))
            self.game_board.appendChild(cell)

    def handle_cell_click(self, event):
        if self.game_phase == 'finished':
            return

        index = int(event.target.dataset.index)
        position = [index // 4, index % 4]

        if self.game_phase == 'hiding':
            self.hider_position = position
            self.game_phase = 'seeking'
            self.game_status.textContent = 'Seeker, try to find the hider!'
        elif self.game_phase == 'seeking':
            self.seeker_position = position
            self.play_game()

    def play_game(self):
        # Encrypt the positions before sending
        encrypted_data = self.encrypt(json.dumps({
            'hider': self.hider_position,
            'seeker': self.seeker_position
        }))

        # In a real application, you would send this data to the server
        # For this example, we'll just process it locally
        self.handle_result(encrypted_data)

    def handle_result(self, encrypted_data):
        # In a real application, this would be the server's response
        # For this example, we'll just decrypt and process locally
        decrypted_data = json.loads(self.decrypt(encrypted_data))
        self.display_result(decrypted_data)

    def display_result(self, data):
        cells = self.game_board.getElementsByClassName('cell')
        
        hider_cell = cells[data['hider'][0] * 4 + data['hider'][1]]
        hider_cell.classList.add('hider')
        hider_cell.textContent = 'H'

        seeker_cell = cells[data['seeker'][0] * 4 + data['seeker'][1]]
        seeker_cell.classList.add('seeker')
        seeker_cell.textContent = 'S'

        if self.check_win(data['hider'], data['seeker']):
            self.game_status.textContent = 'Seeker wins!'
        else:
            self.game_status.textContent = 'Hider wins!'

        self.game_phase = 'finished'
        self.reset_btn.style.display = 'inline-block'

    def check_win(self, hider_pos, seeker_pos):
        return abs(hider_pos[0] - seeker_pos[0]) <= 1 and abs(hider_pos[1] - seeker_pos[1]) <= 1

    def reset_game(self, event):
        self.hider_position = None
        self.seeker_position = None
        self.game_phase = 'hiding'
        self.game_status.textContent = 'Hider, choose your position!'
        self.reset_btn.style.display = 'none'
        self.create_board()

    def encrypt(self, data):
        cipher = AES.new(self.encryption_key, AES.MODE_ECB)
        ct_bytes = cipher.encrypt(pad(data.encode(), AES.block_size))
        return base64.b64encode(ct_bytes).decode('utf-8')

    def decrypt(self, enc_data):
        enc = base64.b64decode(enc_data)
        cipher = AES.new(self.encryption_key, AES.MODE_ECB)
        pt = unpad(cipher.decrypt(enc), AES.block_size)
        return pt.decode('utf-8')

# Initialize the game when the page loads
game = HideAndSeekGame()