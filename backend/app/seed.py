"""
Idempotent database bootstrap + demo seed for NEERON.

Usage:
    python -m app.seed

Creates all tables (via SQLAlchemy metadata) and inserts a demo dataset:
roles, an admin user, a farm, zones, tanks, sensors, recent telemetry and
alerts. Safe to run multiple times - it no-ops if the admin user already exists.
"""

import asyncio
import json
import logging
import os
import random
from datetime import datetime, timezone, timedelta

from sqlalchemy import delete, select

from app.db.base import Base
from app.db.session import engine, async_session_factory
import app.models  # noqa: F401  (ensure every model is registered on Base)
from app.models.role import Role
from app.models.user import User
from app.models.farm import Farm
from app.models.zone import Zone
from app.models.tank import Tank
from app.models.sensor import Sensor
from app.models.telemetry import Telemetry
from app.models.alert import Alert
from app.models.ui import UiResource
from app.core.security import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("neeron.seed")

ADMIN_EMAIL = "admin@neeron.io"
ADMIN_PASSWORD = "Admin@12345"

ADMIN_PERMISSIONS = {
    "read:dashboard": True,
    "read:tanks": True,
    "write:tanks": True,
    "read:telemetry": True,
    "read:alerts": True,
    "write:alerts": True,
    "read:biosecurity": True,
    "write:biosecurity": True,
    "read:settings": True,
    "write:settings": True,
    "read:users": True,
    "write:users": True,
}

SENSOR_TYPES = ["temperature", "pH", "dissolved_oxygen", "salinity"]
SENSOR_BASELINES = {
    "temperature": (12.0, 0.4),
    "pH": (7.8, 0.1),
    "dissolved_oxygen": (8.2, 0.3),
    "salinity": (33.0, 0.5),
}


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Tables created (metadata.create_all).")


async def seed():
    async with async_session_factory() as db:
        existing = await db.execute(select(User).where(User.email == ADMIN_EMAIL))
        if existing.scalar_one_or_none():
            logger.info("Seed skipped: admin user already exists.")
            return

        # Roles
        admin_role = Role(name="Administrator", permissions=ADMIN_PERMISSIONS)
        viewer_role = Role(
            name="Viewer",
            permissions={k: v for k, v in ADMIN_PERMISSIONS.items() if k.startswith("read:")},
        )
        db.add_all([admin_role, viewer_role])
        await db.flush()

        # Admin user
        admin = User(
            role_id=admin_role.id,
            email=ADMIN_EMAIL,
            password_hash=hash_password(ADMIN_PASSWORD),
            first_name="Sam",
            last_name="Houston",
            is_active=True,
        )
        db.add(admin)

        # Farm + zones
        farm = Farm(
            name="Neeron Atlantic Site Alpha",
            latitude=60.472,
            longitude=8.4689,
            timezone="UTC",
            carrying_capacity_kg=250000.0,
        )
        db.add(farm)
        await db.flush()

        zones = [
            Zone(farm_id=farm.id, name="North Pen Cluster", description="Exposed northern cages"),
            Zone(farm_id=farm.id, name="South Pen Cluster", description="Sheltered southern cages"),
        ]
        db.add_all(zones)
        await db.flush()

        # Tanks + sensors + telemetry + alerts
        now = datetime.now(timezone.utc)
        tank_count = 0
        for zi, zone in enumerate(zones):
            for ti in range(3):
                tank_count += 1
                tank = Tank(
                    zone_id=zone.id,
                    name=f"Cage {tank_count:02d}",
                    type="Sea Cage",
                    volume_m3=12000.0,
                    max_biomass_kg=180000.0,
                    species="Atlantic Salmon",
                    digital_twin_config={"model": "v2", "calibrated": True},
                )
                db.add(tank)
                await db.flush()

                for stype in SENSOR_TYPES:
                    sensor = Sensor(
                        tank_id=tank.id,
                        hardware_id=f"HW-{tank_count:02d}-{stype[:4].upper()}",
                        type=stype,
                        status="Active",
                        calibration_due_at=now + timedelta(days=30),
                    )
                    db.add(sensor)
                    await db.flush()

                    base, jitter = SENSOR_BASELINES[stype]
                    for minutes_ago in range(0, 120, 15):
                        db.add(Telemetry(
                            sensor_id=sensor.id,
                            time=now - timedelta(minutes=minutes_ago),
                            value=round(base + random.uniform(-jitter, jitter), 3),
                            raw_payload={"src": "seed"},
                        ))

                if tank_count % 3 == 0:
                    db.add(Alert(
                        time=now - timedelta(hours=2),
                        tank_id=tank.id,
                        type="water_quality",
                        severity="Warning",
                        status="Active",
                        message=f"Dissolved oxygen trending low in {tank.name}.",
                    ))

        await db.commit()
        logger.info(
            "Seed complete: %d tanks, %d sensors/tank, admin=%s",
            tank_count, len(SENSOR_TYPES), ADMIN_EMAIL,
        )


async def seed_ui():
    """Load the view-shaped demo content into the ui_resources table (idempotent)."""
    demo_path = os.path.join(os.path.dirname(__file__), "seed_data", "demo.json")
    if not os.path.exists(demo_path):
        logger.warning("UI seed skipped: %s not found", demo_path)
        return
    with open(demo_path, encoding="utf-8") as f:
        data = json.load(f)

    list_collections = [
        "zones", "tanks", "alerts", "recommendations", "biosecurity", "analytics",
    ]
    async with async_session_factory() as db:
        await db.execute(delete(UiResource))
        for cname in list_collections:
            items = data.get(cname, []) or []
            for i, item in enumerate(items):
                db.add(UiResource(
                    collection=cname,
                    item_id=str(item.get("id", i)),
                    ordinal=i,
                    payload=item,
                ))
        if data.get("dashboard"):
            db.add(UiResource(collection="dashboard", item_id="main", ordinal=0, payload=data["dashboard"]))
        await db.commit()
    logger.info("UI content seeded from demo.json.")


async def main():
    await create_tables()
    await seed()
    await seed_ui()


if __name__ == "__main__":
    asyncio.run(main())
