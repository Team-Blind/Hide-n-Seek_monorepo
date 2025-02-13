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
        
        self.on_game_state_update_proxy = create_proxy(self.on_game_state_update)
        self.on_position_update_proxy = create_proxy(self.on_position_update)
        self.on_distance_update_proxy = create_proxy(self.on_distance_update)

        self.create_board()

        asyncio.ensure_future(self.wait_for_socket())

    async def wait_for_socket(self):
        """Wait until JavaScript WebSocket is initialized."""
        while not hasattr(js.window, "socket"):
            print("[DEBUG] Waiting for window.socket to be initialized...")
            await asyncio.sleep(0.1)
        
        self.sio = js.window.socket 
        print("[DEBUG] Socket.IO is ready, sending join event.")

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
                self.sio.emit("placed", json.dumps({"player_type": self.player_type, "position": self.my_position}))
                self.update_status("Position set. Waiting for opponent.")

        elif self.game_state["phase"] == "movement":
            if self.game_state["current_turn"] != self.player_type:
                print("[DEBUG] Not your turn, ignoring move.")
                self.update_status("Not your turn!")
                return

            if not self.is_valid_move(self.my_position["x"], self.my_position["y"], x, y):
                print("[DEBUG] Invalid move attempt!")
                self.update_status("Invalid move!")
                return

            print(f"[DEBUG] {self.player_type} moving to ({x}, {y})")

            self.dehighlight_position(self.my_position["x"], self.my_position["y"])

            self.my_position = {"x": x, "y": y}
            self.sio.emit("move", json.dumps({"player_type": self.player_type, "position": self.my_position}))

            self.highlight_position(x, y)

            self.game_state["current_turn"] = "seeker" if self.player_type == "hider" else "hider"
            self.update_status("Waiting for opponent to move...")


    def on_game_state_update(self, state):
        """Handle updates to the game state safely."""
        print(f"[DEBUG] Received game state update: {state}")

        if hasattr(state, "to_py"):
            state = state.to_py()

        if isinstance(state, str):
            try:
                state = json.loads(state)
            except json.JSONDecodeError:
                print("[ERROR] Failed to parse JSON from game state update.")
                return

        if not isinstance(state, dict):
            print("[ERROR] Invalid game state format received.")
            return

        self.game_state = state 
        print(f"[DEBUG] Updated game state: {self.game_state}")

        hider_ready = self.game_state.get("hider_connected", False)
        seeker_ready = self.game_state.get("seeker_connected", False)

        if not hider_ready or not seeker_ready:
            print("[DEBUG] Not all players are connected yet.")
            self.update_status("Waiting for both players...")
            return  

        phase = self.game_state.get("phase", "placement")
        current_turn = self.game_state.get("current_turn", "hider")

        if phase == "placement":
            if not self.my_position:
                self.update_status("Choose your starting position!")
            else:
                self.update_status("Position set. Waiting for opponent.")

        elif phase == "movement":
            if current_turn == self.player_type:
                self.update_status("Your turn to move!")
            else:
                self.update_status("Waiting for opponent to move...")

        # positions = self.game_state.get("positions", {})
        # if self.player_type in positions:
        #     pos = positions[self.player_type]
        #     self.highlight_position(pos["x"], pos["y"])

    def on_position_update(self, data):
        """Handle position updates from the server and update UI."""
        if isinstance(data, str):
            data = json.loads(data)
        
        elif hasattr(data, "to_py"):
            data = data.to_py()

        if "player_type" not in data or "position" not in data:
            print("[ERROR] Invalid position update received.")
            return

        player_type = data["player_type"]
        position = data["position"]

        print(f"[DEBUG] Updating {player_type} position to {position}")

        # self.highlight_position(position["x"], position["y"], player_type)


    def highlight_position(self, x, y, player_type=None):
        """Highlight the player's position on the board."""
        cell = document.getElementById(f"cell_{x}_{y}")
        if cell:
            if player_type is None:
                player_type = self.player_type
            class_name = "hider" if player_type == "hider" else "seeker"
            cell.classList.add(class_name)

    def dehighlight_position(self, x, y):
        """Remove the highlight from the previous position."""
        cell = document.getElementById(f"cell_{x}_{y}")
        if cell:
            cell.classList.remove("hider", "seeker")


    def on_distance_update(self, data):
        """Handle distance updates from the server."""
        if isinstance(data, str):
            data = json.loads(data)  # Convert JSON string to dictionary

        if 'distance' in data:
            self.update_status(f"Distance to opponent: {data['distance']} squares")

    def update_status(self, message):
        """Update the game status."""
        self.status_element.textContent = message

    def is_valid_move(self, current_x, current_y, new_x, new_y):
        """Check if the move is valid (only horizontal or vertical by 1 step)."""
        return (abs(new_x - current_x) == 1 and new_y == current_y) or \
            (abs(new_y - current_y) == 1 and new_x == current_x)

GAME = HideAndSeekGame()
