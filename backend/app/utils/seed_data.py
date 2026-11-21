import sys
import os
from pathlib import Path

# Add backend directory to sys.path if run directly
backend_dir = str(Path(__file__).resolve().parent.parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import datetime
import random
import logging
from sqlalchemy.orm import Session
from app.database import engine, Base, SessionLocal
from app.models.user import User
from app.models.category import Category
from app.models.emission_factor import EmissionFactor
from app.models.activity import Activity
from app.models.goal import Goal
from app.models.achievement import Achievement, UserAchievement
from app.auth.security import get_password_hash
from app.config import settings
from app.services.achievement_service import AchievementService

logger = logging.getLogger("carbonlens.seed")

CATEGORIES_DATA = [
    {
        "name": "Transportation",
        "description": "Daily commuting, personal car travel, public transit, trains, and active mobility.",
        "icon": "car",
    },
    {
        "name": "Electricity",
        "description": "Residential grid power consumption, appliance usage, and clean energy offsets.",
        "icon": "zap",
    },
    {
        "name": "Natural Gas",
        "description": "Home heating, water heaters, stoves, and residential natural gas consumption.",
        "icon": "flame",
    },
    {
        "name": "Flights",
        "description": "Commercial passenger aviation across short, medium, and long-haul distances.",
        "icon": "plane",
    },
    {
        "name": "Food & Diet",
        "description": "Daily dietary carbon footprint based on meat, mixed, vegetarian, or plant-based meals.",
        "icon": "utensils",
    },
    {
        "name": "Shopping & Goods",
        "description": "Embodied emissions from purchasing consumer goods, electronics, and clothing.",
        "icon": "shopping-bag",
    },
]

EMISSION_FACTORS_DATA = [
    # Transportation
    {
        "category_name": "Transportation",
        "activity_type": "Car (Gasoline)",
        "unit": "km",
        "factor": 0.192,
        "source": "EPA 2024 GHG Emission Factors Hub",
        "description": "Average gasoline internal combustion passenger vehicle",
    },
    {
        "category_name": "Transportation",
        "activity_type": "Car (Diesel)",
        "unit": "km",
        "factor": 0.171,
        "source": "EPA 2024 GHG Emission Factors Hub",
        "description": "Standard diesel passenger car",
    },
    {
        "category_name": "Transportation",
        "activity_type": "Car (Hybrid)",
        "unit": "km",
        "factor": 0.109,
        "source": "EPA 2024 GHG Hub",
        "description": "Gasoline-electric hybrid car",
    },
    {
        "category_name": "Transportation",
        "activity_type": "Car (Electric / EV)",
        "unit": "km",
        "factor": 0.053,
        "source": "DEFRA 2024 Conversion Factors",
        "description": "Battery electric vehicle accounting for grid generation average",
    },
    {
        "category_name": "Transportation",
        "activity_type": "Motorcycle",
        "unit": "km",
        "factor": 0.113,
        "source": "DEFRA 2024 Conversion Factors",
        "description": "Medium displacement motorcycle",
    },
    {
        "category_name": "Transportation",
        "activity_type": "Bus (Transit)",
        "unit": "km",
        "factor": 0.089,
        "source": "DEFRA 2024 Conversion Factors",
        "description": "Local city transit bus per passenger km",
    },
    {
        "category_name": "Transportation",
        "activity_type": "Train / Rail",
        "unit": "km",
        "factor": 0.041,
        "source": "DEFRA 2024 Conversion Factors",
        "description": "Electric passenger intercity and regional train",
    },
    {
        "category_name": "Transportation",
        "activity_type": "Subway / Metro",
        "unit": "km",
        "factor": 0.035,
        "source": "DEFRA 2024 Conversion Factors",
        "description": "Urban heavy rail and subway systems",
    },
    {
        "category_name": "Transportation",
        "activity_type": "Bicycle",
        "unit": "km",
        "factor": 0.0,
        "source": "Zero Direct Emissions",
        "description": "Active cycling travel (zero tailpipe emissions)",
    },
    {
        "category_name": "Transportation",
        "activity_type": "Walking",
        "unit": "km",
        "factor": 0.0,
        "source": "Zero Direct Emissions",
        "description": "Pedestrian active travel (zero tailpipe emissions)",
    },

    # Electricity
    {
        "category_name": "Electricity",
        "activity_type": "Grid Electricity",
        "unit": "kWh",
        "factor": 0.385,
        "source": "EPA eGRID 2024 National Average",
        "description": "Standard national grid power mix",
    },
    {
        "category_name": "Electricity",
        "activity_type": "Renewable Electricity (Solar/Wind)",
        "unit": "kWh",
        "factor": 0.015,
        "source": "NREL Lifecycle Energy Assessment",
        "description": "Rooftop solar or certified 100% green renewable power tariff",
    },

    # Natural Gas
    {
        "category_name": "Natural Gas",
        "activity_type": "Natural Gas (Heating)",
        "unit": "m3",
        "factor": 2.03,
        "source": "DEFRA 2024 Fuel Conversion Factors",
        "description": "Residential natural gas pipeline delivery",
    },
    {
        "category_name": "Natural Gas",
        "activity_type": "Propane / LPG",
        "unit": "liter",
        "factor": 1.51,
        "source": "EPA 2024 Hub",
        "description": "Bottled propane gas",
    },

    # Flights
    {
        "category_name": "Flights",
        "activity_type": "Flight (Short-Haul < 500km)",
        "unit": "km",
        "factor": 0.255,
        "source": "DEFRA 2024 Aviation Factors",
        "description": "Short flights with high takeoff/landing fuel proportion",
    },
    {
        "category_name": "Flights",
        "activity_type": "Flight (Medium-Haul 500-3700km)",
        "unit": "km",
        "factor": 0.156,
        "source": "DEFRA 2024 Aviation Factors",
        "description": "Domestic and continental passenger flights",
    },
    {
        "category_name": "Flights",
        "activity_type": "Flight (Long-Haul > 3700km)",
        "unit": "km",
        "factor": 0.150,
        "source": "DEFRA 2024 Aviation Factors",
        "description": "Intercontinental long-haul passenger flights",
    },

    # Food & Diet
    {
        "category_name": "Food & Diet",
        "activity_type": "Meal (Meat-Heavy / Beef)",
        "unit": "meals",
        "factor": 3.30,
        "source": "Poore & Nemecek Science (2018)",
        "description": "Meals featuring beef, lamb, or heavy animal protein",
    },
    {
        "category_name": "Food & Diet",
        "activity_type": "Meal (Mixed / Average)",
        "unit": "meals",
        "factor": 1.70,
        "source": "Poore & Nemecek Science (2018)",
        "description": "Standard omnivorous meal with poultry, pork, or dairy",
    },
    {
        "category_name": "Food & Diet",
        "activity_type": "Meal (Vegetarian)",
        "unit": "meals",
        "factor": 0.90,
        "source": "Poore & Nemecek Science (2018)",
        "description": "Meat-free meal containing eggs, dairy, or grains",
    },
    {
        "category_name": "Food & Diet",
        "activity_type": "Meal (Vegan / Plant-Based)",
        "unit": "meals",
        "factor": 0.50,
        "source": "Poore & Nemecek Science (2018)",
        "description": "100% whole plant-based ingredients",
    },

    # Shopping
    {
        "category_name": "Shopping & Goods",
        "activity_type": "Clothing / Apparel Purchase",
        "unit": "USD",
        "factor": 0.45,
        "source": "USEEIO 2.0 Economic Input-Output",
        "description": "Fast fashion and standard retail garments",
    },
    {
        "category_name": "Shopping & Goods",
        "activity_type": "Electronics / Tech Device",
        "unit": "USD",
        "factor": 0.60,
        "source": "USEEIO 2.0 Economic Input-Output",
        "description": "Consumer electronics, smartphones, and computers",
    },
    {
        "category_name": "Shopping & Goods",
        "activity_type": "General Goods & Packaging",
        "unit": "USD",
        "factor": 0.35,
        "source": "USEEIO 2.0 Economic Input-Output",
        "description": "Home goods, packaged items, and accessories",
    },
]


def seed_database():
    """Seed all reference categories, factors, achievements, and demo accounts."""
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # 1. Seed Categories
        cat_map = {}
        for c_data in CATEGORIES_DATA:
            cat = db.query(Category).filter(Category.name == c_data["name"]).first()
            if not cat:
                cat = Category(
                    name=c_data["name"],
                    description=c_data["description"],
                    icon=c_data["icon"],
                    is_active=True,
                )
                db.add(cat)
                db.commit()
                db.refresh(cat)
            cat_map[c_data["name"]] = cat

        # 2. Seed Emission Factors
        for ef_data in EMISSION_FACTORS_DATA:
            cat = cat_map.get(ef_data["category_name"])
            if not cat:
                continue
            factor_obj = db.query(EmissionFactor).filter(
                EmissionFactor.category_id == cat.id,
                EmissionFactor.activity_type == ef_data["activity_type"]
            ).first()
            if not factor_obj:
                factor_obj = EmissionFactor(
                    category_id=cat.id,
                    activity_type=ef_data["activity_type"],
                    unit=ef_data["unit"],
                    factor=ef_data["factor"],
                    source=ef_data["source"],
                    version="1.0",
                    description=ef_data["description"],
                    is_active=True,
                )
                db.add(factor_obj)
        db.commit()

        # 3. Seed Default Achievements
        AchievementService.ensure_default_achievements(db)

        # 4. Seed Admin User
        admin_user = db.query(User).filter(User.email == settings.ADMIN_USER_EMAIL).first()
        if not admin_user:
            admin_user = User(
                full_name=settings.ADMIN_USER_NAME,
                email=settings.ADMIN_USER_EMAIL,
                password_hash=get_password_hash(settings.ADMIN_USER_PASSWORD),
                role="admin",
                is_active=True,
                leaderboard_opt_in=True,
                public_handle="Admin",
            )
            db.add(admin_user)
            db.commit()
        else:
            # Ensure password hash is always valid on restart
            admin_user.password_hash = get_password_hash(settings.ADMIN_USER_PASSWORD)
            admin_user.is_active = True
            db.commit()

        # 5. Seed Demo User
        demo_user = db.query(User).filter(User.email == settings.DEMO_USER_EMAIL).first()
        if not demo_user:
            demo_user = User(
                full_name=settings.DEMO_USER_NAME,
                email=settings.DEMO_USER_EMAIL,
                password_hash=get_password_hash(settings.DEMO_USER_PASSWORD),
                role="user",
                is_active=True,
                leaderboard_opt_in=True,
                public_handle="EcoAlex",
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
        else:
            # Ensure demo password hash is always valid on restart
            demo_user.password_hash = get_password_hash(settings.DEMO_USER_PASSWORD)
            demo_user.is_active = True
            db.commit()
            db.refresh(demo_user)

            # Set Demo User Goal (200 kg CO2e / month)
            goal = Goal(
                user_id=demo_user.id,
                monthly_target=200.0,
                start_date=datetime.date.today() - datetime.timedelta(days=90),
                is_active=True,
            )
            db.add(goal)
            db.commit()

            # Seed realistic multi-month activity log for Demo User
            today = datetime.date.today()
            sample_logs = [
                # Current month activities
                (today - datetime.timedelta(days=1), "Car (Gasoline)", 18.5, "km", "Transportation", "Commute to office"),
                (today - datetime.timedelta(days=1), "Meal (Mixed / Average)", 2.0, "meals", "Food & Diet", "Lunch and dinner"),
                (today - datetime.timedelta(days=2), "Subway / Metro", 24.0, "km", "Transportation", "Downtown client meeting"),
                (today - datetime.timedelta(days=2), "Meal (Vegan / Plant-Based)", 1.0, "meals", "Food & Diet", "Plant bowl lunch"),
                (today - datetime.timedelta(days=3), "Grid Electricity", 12.4, "kWh", "Electricity", "Daily household electricity"),
                (today - datetime.timedelta(days=4), "Bicycle", 8.0, "km", "Transportation", "Weekend grocery run"),
                (today - datetime.timedelta(days=5), "Meal (Meat-Heavy / Beef)", 1.0, "meals", "Food & Diet", "Family barbecue dinner"),
                (today - datetime.timedelta(days=6), "Natural Gas (Heating)", 3.2, "m3", "Natural Gas", "Water heating & cooking"),
                (today - datetime.timedelta(days=7), "Car (Gasoline)", 32.0, "km", "Transportation", "Visit relatives"),
                (today - datetime.timedelta(days=8), "Clothing / Apparel Purchase", 45.0, "USD", "Shopping & Goods", "Organic cotton shirt"),
                (today - datetime.timedelta(days=10), "Train / Rail", 45.0, "km", "Transportation", "Regional day trip"),

                # Previous month activities (Month -1)
                (today - datetime.timedelta(days=32), "Car (Gasoline)", 45.0, "km", "Transportation", "Extended commute in rain"),
                (today - datetime.timedelta(days=33), "Grid Electricity", 15.0, "kWh", "Electricity", "AC and heavy laundry load"),
                (today - datetime.timedelta(days=35), "Meal (Meat-Heavy / Beef)", 2.0, "meals", "Food & Diet", "Steak dinner"),
                (today - datetime.timedelta(days=38), "Flight (Short-Haul < 500km)", 380.0, "km", "Flights", "Weekend conference return"),
                (today - datetime.timedelta(days=42), "Natural Gas (Heating)", 5.0, "m3", "Natural Gas", "Cold spell heating"),
                (today - datetime.timedelta(days=45), "Electronics / Tech Device", 120.0, "USD", "Shopping & Goods", "Wireless headphones"),

                # 2 months ago activities (Month -2)
                (today - datetime.timedelta(days=65), "Car (Gasoline)", 60.0, "km", "Transportation", "Road trip driving"),
                (today - datetime.timedelta(days=68), "Grid Electricity", 16.5, "kWh", "Electricity", "Mid-winter heating auxiliaries"),
                (today - datetime.timedelta(days=72), "Meal (Mixed / Average)", 3.0, "meals", "Food & Diet", "Dining out"),
            ]

            for log_date, act_type, qty, unit, cat_name, notes in sample_logs:
                cat = cat_map.get(cat_name)
                factor_obj = db.query(EmissionFactor).filter(
                    EmissionFactor.activity_type == act_type
                ).first()
                factor = factor_obj.factor if factor_obj else 0.2
                co2 = round(qty * factor, 2)

                act = Activity(
                    user_id=demo_user.id,
                    category_id=cat.id if cat else None,
                    activity_type=act_type,
                    quantity=qty,
                    unit=unit,
                    emission_factor=factor,
                    calculated_co2=co2,
                    activity_date=log_date,
                    notes=notes,
                )
                db.add(act)
            db.commit()

            # Seed sample other community users for vibrant leaderboard
            sample_peers = [
                ("Elena Rostova", "ElenaEco", 88, 120.0),
                ("Marcus Chen", "GreenMarcus", 82, 145.0),
                ("Sophia Patel", "ZeroWasteSophie", 94, 98.0),
                ("Liam O'Connor", "Liam_Track", 68, 185.0),
                ("Zoe Vance", "EcoZoe", 75, 160.0),
            ]
            for name, handle, score, target in sample_peers:
                peer = User(
                    full_name=name,
                    email=f"{handle.lower()}@example.com",
                    password_hash=get_password_hash("Password123!"),
                    role="user",
                    is_active=True,
                    leaderboard_opt_in=True,
                    public_handle=handle,
                )
                db.add(peer)
                db.commit()
                db.refresh(peer)

                # Peer Goal
                db.add(Goal(user_id=peer.id, monthly_target=target, start_date=today - datetime.timedelta(days=60), is_active=True))

                # Peer sample activities
                for offset in [2, 5, 8, 12, 16, 20]:
                    db.add(Activity(
                        user_id=peer.id,
                        category_id=cat_map["Transportation"].id,
                        activity_type="Train / Rail" if score > 80 else "Car (Gasoline)",
                        quantity=25.0,
                        unit="km",
                        emission_factor=0.041 if score > 80 else 0.192,
                        calculated_co2=1.025 if score > 80 else 4.8,
                        activity_date=today - datetime.timedelta(days=offset),
                        notes="Commute",
                    ))
                db.commit()

            # Evaluate achievements for demo user
            AchievementService.evaluate_user_achievements(db, demo_user.id)

        print("[Seed] Database successfully seeded with categories, emission factors, achievements, and demo accounts.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
