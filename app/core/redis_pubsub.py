import asyncio
import json

import redis.asyncio as redis

from app.core.config import (
    REDIS_URL,
    REDIS_CHANNEL_NAME
)

from app.core.websocket_manager import manager


# ============================================================
# REDIS CONNECTION
# ============================================================

redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True
)


# ============================================================
# PUBLISH EVENT
# ============================================================

async def publish_event(event: dict):
    """
    Publish an event to Redis.

    Redis is used for real-time communication.

    A Redis failure should not crash
    the main API operation.
    """

    message = json.dumps(event)

    try:

        await redis_client.publish(
            REDIS_CHANNEL_NAME,
            message
        )

    except Exception as e:

        print(
            f"Redis publish failed: {e}"
        )


# ============================================================
# SUBSCRIBE TO EVENTS
# ============================================================

async def subscribe_to_events():
    """
    Listen for Redis events and broadcast them
    to connected WebSocket clients.
    """

    pubsub = redis_client.pubsub()

    try:

        await pubsub.subscribe(
            REDIS_CHANNEL_NAME
        )

        while True:

            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=1.0
            )

            if message:

                data = json.loads(
                    message["data"]
                )

                # ------------------------------------------------
                # Send event to specific user
                # ------------------------------------------------

                target_user_id = data.get(
                    "target_user_id"
                )

                if target_user_id is not None:

                    await manager.send_to_user(
                        int(target_user_id),
                        data
                    )

                # ------------------------------------------------
                # Broadcast event to everyone
                # ------------------------------------------------

                else:

                    await manager.broadcast(
                        data
                    )

            await asyncio.sleep(0.01)

    # ========================================================
    # SHUTDOWN
    # ========================================================

    except asyncio.CancelledError:

        print(
            "Redis subscriber shutting down..."
        )

        raise

    # ========================================================
    # ERROR
    # ========================================================

    except Exception as e:

        print(
            f"Redis subscriber error: {e}"
        )

    # ========================================================
    # CLEANUP
    # ========================================================

    finally:

        try:

            await pubsub.unsubscribe(
                REDIS_CHANNEL_NAME
            )

            await pubsub.close()

        except Exception as e:

            print(
                f"Redis cleanup error: {e}"
            )