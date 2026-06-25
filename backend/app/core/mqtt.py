import asyncio
import json
import logging

from aiomqtt import Client, MqttError

from app.core.config import settings
from app.db.session import async_session_factory
from app.repositories.sensor_repository import SensorRepository
from app.repositories.telemetry_repository import TelemetryRepository
from app.services.telemetry_service import TelemetryService

logger = logging.getLogger(__name__)

MQTT_BROKER = settings.MQTT_BROKER
MQTT_PORT = settings.MQTT_PORT
MQTT_TOPIC = settings.MQTT_TOPIC


async def mqtt_listener():
    reconnect_interval = 5
    while True:
        try:
            async with Client(hostname=MQTT_BROKER, port=MQTT_PORT) as client:
                logger.info(f"Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
                await client.subscribe(MQTT_TOPIC)
                logger.info(f"Subscribed to topic: {MQTT_TOPIC}")

                async for message in client.messages:
                    topic = message.topic.value
                    payload = message.payload.decode()
                    logger.debug(f"Received message on {topic}: {payload}")

                    try:
                        data = json.loads(payload)
                        # Topic format: neeron/tanks/{tank_id}/telemetry
                        parts = topic.split("/")
                        if len(parts) < 3:
                            logger.warning(f"Unexpected topic structure: {topic}")
                            continue
                        tank_id = parts[2]

                        async with async_session_factory() as db:
                            telemetry_service = TelemetryService(
                                telemetry_repo=TelemetryRepository(db),
                                sensor_repo=SensorRepository(db),
                            )
                            await telemetry_service.process_raw_telemetry(tank_id, data)
                            await db.commit()

                    except json.JSONDecodeError:
                        logger.error(f"Failed to decode JSON payload: {payload}")
                    except Exception as e:
                        logger.error(f"Error processing MQTT message: {e}")

        except MqttError as error:
            logger.error(f"MQTT error: {error}. Reconnecting in {reconnect_interval}s...")
            await asyncio.sleep(reconnect_interval)
        except Exception as e:
            logger.error(f"Unexpected error in MQTT listener: {e}")
            await asyncio.sleep(reconnect_interval)


def start_mqtt_client(loop=None):
    """Start the MQTT listener as a background task.

    Returns the created task, or None if MQTT is disabled via config.
    """
    if not settings.MQTT_ENABLED:
        logger.info("MQTT listener disabled (MQTT_ENABLED=false); skipping startup.")
        return None
    if loop is None:
        loop = asyncio.get_event_loop()
    return loop.create_task(mqtt_listener())
