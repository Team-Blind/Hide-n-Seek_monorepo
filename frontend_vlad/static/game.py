from pyscript import document
import json
import js
import asyncio

class HideAndSeekGame:
    def __init__(self):
        """Initialize the game and set up WebSockets."""
        self.player_type = document.getElementById("player_type").textContent.strip().lower()
        self.status_element = document.getElementById("gameStatus")
        self.my_position = None
        self.game_state = {"phase": "placement", "current_turn": "hider"}
        
        # ✅ Wait until `window.socket` is available before using it
        asyncio.ensure_future(self.wait_for_socket())

    async def wait_for_socket(self):
        """Wait until JavaScript WebSocket is initialized."""
        while not hasattr(js.window, "socket"):
            print("[DEBUG] Waiting for window.socket to be initialized...")
            await asyncio.sleep(0.1)  # Wait for JavaScript to initialize socket
        
        self.sio = js.window.socket  # ✅ Now safe to use
        print("[DEBUG] Socket.IO is ready, sending join event.")
        
        # Register event listeners
        self.sio.on("connect", self.on_socket_connect)
        self.sio.on("game_state_update", self.on_game_state_update)
        self.sio.on("position_update", self.on_position_update)
        self.sio.on("distance_update", self.on_distance_update)

        # ✅ Send join event after connection is ready
        self.on_socket_connect()

    def on_socket_connect(self):
        """Send join event only after the Socket.IO connection is established."""
        print(f"[DEBUG] Socket.IO connected! Sending join event with player_type: {self.player_type}")
        self.sio.emit("join", json.dumps({"player_type": self.player_type}))

    def create_board(self):
        """Generate the game board dynamically inside PyScript."""
        game_board = document.getElementById("gameBoard")
        for y in range(6):
            for x in range(6):
                cell = document.createElement("div")
                cell.className = "cell"
                cell.id = f"cell_{x}_{y}"
                cell.setAttribute("data-x", str(x))
                cell.setAttribute("data-y", str(y))
                cell.addEventListener("click", self.on_cell_click)
                game_board.appendChild(cell)

    def on_cell_click(self, event):
        """Handle cell clicks for position placement or movement."""
        x = int(event.target.getAttribute("data-x"))
        y = int(event.target.getAttribute("data-y"))

        print(f"[DEBUG] Clicked on: ({x}, {y}), Phase: {self.game_state['phase']}, Turn: {self.game_state['current_turn']}")

        if self.game_state["phase"] == "placement":
            if not self.my_position:
                self.my_position = {"x": x, "y": y}
                self.highlight_position(x, y)
                self.sio.emit("move", {"player_type": self.player_type, "position": self.my_position})
                self.update_status("Position set. Waiting for opponent.")

    def on_game_state_update(self, state):
        """Handle updates to the game state."""
        print(f"[DEBUG] Received game state update: {state}")

        if isinstance(state, str):
            state = json.loads(state)
        
        self.game_state = state

        print(f"[DEBUG] Updated game state: {self.game_state}")

        if not self.game_state.get("hider_connected") or not self.game_state.get("seeker_connected"):
            self.update_status("Waiting for both players...")
            return

        if self.game_state["phase"] == "placement":
            if not self.my_position:
                self.update_status("Choose your starting position!")
            else:
                self.update_status("Position set. Waiting for opponent.")
        elif self.game_state["phase"] == "movement":
            if self.game_state["current_turn"] == self.player_type:
                self.update_status("Your turn to move!")
            else:
                self.update_status("Waiting for opponent to move...")

    def on_position_update(self, data):
        """Handle position updates from the server."""
        if isinstance(data, str):
            data = json.loads(data)

        if 'position' in data and data["position"]:
            self.my_position = data["position"]
            self.highlight_position(self.my_position["x"], self.my_position["y"])

    def on_distance_update(self, data):
        """Handle distance updates from the server."""
        if isinstance(data, str):
            data = json.loads(data)

        if 'distance' in data:
            self.update_status(f"Distance to opponent: {data['distance']} squares")

    def update_status(self, message):
        """Update the game status."""
        self.status_element.textContent = message

    def highlight_position(self, x, y):
        """Highlight the player's position on the board."""
        for cell in document.getElementsByClassName("cell"):
            cell.classList.remove("hider", "seeker")

        cell = document.getElementById(f"cell_{x}_{y}")
        if cell:
            class_name = "hider" if self.player_type == "hider" else "seeker"
            cell.classList.add(class_name)

# Initialize the game
GAME = HideAndSeekGame()
