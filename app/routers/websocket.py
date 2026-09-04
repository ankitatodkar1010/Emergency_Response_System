from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.websocket_manager import manager
from app.core.security import verify_access_token


router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket
):
    # --------------------------------------------------------
    # 1. Get JWT token from query parameter
    # --------------------------------------------------------

    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=1008)
        return

    # --------------------------------------------------------
    # 2. Verify JWT
    # --------------------------------------------------------

    try:
        user_id = verify_access_token(token)

    except ValueError:
        await websocket.close(code=1008)
        return

    # --------------------------------------------------------
    # 3. Accept and register connection
    # --------------------------------------------------------

    await manager.connect(
        websocket,
        user_id
    )

    print(
        f"WebSocket connected: user_id={user_id}"
    )

    try:

        while True:

            # Keep connection alive.
            # Events are pushed from Redis → WebSocket.
            await websocket.receive_text()

    except WebSocketDisconnect:

        manager.disconnect(
            user_id,
            websocket
        )

        print(
            f"WebSocket disconnected: user_id={user_id}"
        )

    except Exception as e:

        manager.disconnect(
            user_id,
            websocket
        )

        print(
            f"WebSocket error for user_id={user_id}: {e}"
        )