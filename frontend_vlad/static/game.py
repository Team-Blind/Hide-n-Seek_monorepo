from pyscript import document
import json
import js
import asyncio
from pyodide.ffi import create_proxy  # ✅ Fixes event handler destruction

class HideAndSeekGame:
    def __init__(self):
        """Initialize the game and set up WebSockets."""
        self.player_type = document.getElementById("player_type").textContent.strip().lower()
        self.status_element = document.getElementById("gameStatus")
        self.my_position = None
        self.game_state = {"phase": "placement", "current_turn": "hider"}
        
        # ✅ Store event handler proxies to prevent them from being destroyed
        self.on_game_state_update_proxy = create_proxy(self.on_game_state_update)
        self.on_position_update_proxy = create_proxy(self.on_position_update)
        self.on_distance_update_proxy = create_proxy(self.on_distance_update)

        self.create_board()

        # ✅ Wait for the WebSocket connection
        asyncio.ensure_future(self.wait_for_socket())

    async def wait_for_socket(self):
        """Wait until JavaScript WebSocket is initialized."""
        while not hasattr(js.window, "socket"):
            print("[DEBUG] Waiting for window.socket to be initialized...")
            await asyncio.sleep(0.1)
        
        self.sio = js.window.socket  # ✅ Access JavaScript Socket.IO instance
        print("[DEBUG] Socket.IO is ready, sending join event.")

        # ✅ Use proxies for event listeners
        self.sio.on("game_state_update", self.on_game_state_update_proxy)
        self.sio.on("position_update", self.on_position_update_proxy)
        self.sio.on("distance_update", self.on_distance_update_proxy)

        self.on_socket_connect()

    def on_socket_connect(self):
        """Send join event after WebSocket connection is established."""
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

                # ✅ Fix event listener issues by using `create_proxy`
                cell.addEventListener("click", create_proxy(self.on_cell_click))
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
                self.sio.emit("move", json.dumps({"player_type": self.player_type, "position": self.my_position}))
                self.update_status("Position set. Waiting for opponent.")

    def on_game_state_update(self, state):
        """Handle updates to the game state safely."""
        print(f"[DEBUG] Received game state update: {state}")

        # ✅ Ensure state is always a Python dictionary
        if isinstance(state, str):
            try:
                state = json.loads(state)
            except json.JSONDecodeError:
                print("[ERROR] Failed to parse JSON from game state update.")
                return

        elif hasattr(state, "to_py"):  # ✅ Convert JavaScript proxy to Python dict
            state = state.to_py()

        if not isinstance(state, dict):  # ✅ Ensure it's always a dictionary
            print("[ERROR] Invalid game state format received.")
            return

        self.game_state = state

        print(f"[DEBUG] Updated game state: {self.game_state}")

        # ✅ Use `.get()` safely with default values
        if not self.game_state.get("hider_connected", False) or not self.game_state.get("seeker_connected", False):
            self.update_status("Waiting for both players...")
            return

        if self.game_state.get("phase") == "placement":
            if not self.my_position:
                self.update_status("Choose your starting position!")
            else:
                self.update_status("Position set. Waiting for opponent.")
        elif self.game_state.get("phase") == "movement":
            if self.game_state.get("current_turn") == self.player_type:
                self.update_status("Your turn to move!")
            else:
                self.update_status("Waiting for opponent to move!")


    def on_position_update(self, data):
        """Handle position updates from the server."""
        if isinstance(data, str):
            data = json.loads(data)  # Convert JSON string to dictionary

        if 'position' in data and data["position"]:
            self.my_position = data["position"]
            self.highlight_position(self.my_position["x"], self.my_position["y"])

    def on_distance_update(self, data):
        """Handle distance updates from the server."""
        if isinstance(data, str):
            data = json.loads(data)  # Convert JSON string to dictionary

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

# ✅ Initialize the game
GAME = HideAndSeekGame()
