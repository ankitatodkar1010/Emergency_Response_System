import asyncio
import json

import redis.asyncio as redis
import websockets


TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5IiwiZXhwIjoxNzg4MDk0MTMyfQ.jp2FHD3zbFZ0HsOCUO_TQjQZbrKPXubc8vddddZcoXw"

REDIS_URL = "redis://localhost:6379/0"
CHANNEL_NAME = "emergency_events"


async def publish_test_event():

    redis_client = redis.from_url(
        REDIS_URL,
        decode_responses=True
    )

    event = {
        "event": "TEST_NOTIFICATION",
        "message": "Hello Responder!",
        "target_user_id": 9
    }

    await redis_client.publish(
        CHANNEL_NAME,
        json.dumps(event)
    )

    print("Redis event published.")

    await redis_client.close()


async def check_websocket():

    uri = f"ws://127.0.0.1:8000/ws?token={TOKEN}"

    print("Connecting to WebSocket...")

    async with websockets.connect(uri) as websocket:

        print("Connected!")

        await asyncio.sleep(1)

        await publish_test_event()

        print("Waiting for WebSocket message...")

        response = await websocket.recv()

        print("Received from WebSocket:")
        print(response)


if __name__ == "__main__":
    asyncio.run(check_websocket())

