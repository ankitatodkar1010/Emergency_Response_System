from fastapi import WebSocket


class ConnectionManager:

    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(
        self,
        websocket: WebSocket,
        user_id: int
    ):
        """
        Register the latest WebSocket connection for a user.

        A user can only have one active connection in this
        process. If a new connection arrives, the old connection
        is replaced.
        """

        await websocket.accept()

        old_websocket = self.active_connections.get(user_id)

        if old_websocket is not None and old_websocket is not websocket:
            try:
                await old_websocket.close(
                    code=1000,
                    reason="Replaced by a newer connection"
                )
            except Exception:
                pass

        self.active_connections[user_id] = websocket

    def disconnect(
        self,
        user_id: int,
        websocket: WebSocket | None = None
    ):
        """
        Remove a connection safely.

        If a websocket is provided, remove it only when that exact
        websocket is still the current connection for the user.

        This prevents an old connection from accidentally removing
        a newer connection belonging to the same user.
        """

        current_websocket = self.active_connections.get(user_id)

        if current_websocket is None:
            return

        if websocket is not None and current_websocket is not websocket:
            return

        self.active_connections.pop(user_id, None)

    async def send_to_user(
        self,
        user_id: int,
        message: dict
    ):
        websocket = self.active_connections.get(user_id)

        if websocket is None:
            return

        try:
            await websocket.send_json(message)

        except Exception:
            self.disconnect(
                user_id,
                websocket
            )

    async def broadcast(
        self,
        message: dict
    ):
        disconnected = []

        for user_id, websocket in list(
            self.active_connections.items()
        ):
            try:
                await websocket.send_json(message)

            except Exception:
                disconnected.append(
                    (user_id, websocket)
                )

        for user_id, websocket in disconnected:
            self.disconnect(
                user_id,
                websocket
            )


manager = ConnectionManager()