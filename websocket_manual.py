import asyncio
import websockets


async def test_websocket():
    uri = "ws://127.0.0.1:8000/ws"

    print("Connecting to WebSocket...")

    async with websockets.connect(uri) as websocket:
        print("Connected!")

        await websocket.send("Hello from WebSocket client")

        response = await websocket.recv()

        print("Received:", response)


if __name__ == "__main__":
    asyncio.run(test_websocket())