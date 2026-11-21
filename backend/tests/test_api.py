import sys
import os
from pathlib import Path

# Add backend directory to sys.path
backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import unittest
import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.activity import Activity
from app.models.category import Category
from app.models.goal import Goal
from app.models.emission_factor import EmissionFactor
from app.models.achievement import Achievement, UserAchievement
from app.auth.security import get_password_hash
from app.services.carbon_calculator import CarbonCalculationService
from app.services.simulator import SimulatorService
from app.services.achievement_service import AchievementService
from app.utils.seed_data import CATEGORIES_DATA, EMISSION_FACTORS_DATA

# In-memory test SQLite database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


class CarbonLensTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=test_engine)
        db = TestingSessionLocal()
        
        # Seed categories
        for c_data in CATEGORIES_DATA:
            cat = Category(name=c_data["name"], description=c_data["description"], icon=c_data["icon"], is_active=True)
            db.add(cat)
        db.commit()

        # Seed emission factors
        for ef in EMISSION_FACTORS_DATA:
            cat = db.query(Category).filter(Category.name == ef["category_name"]).first()
            if cat:
                db.add(EmissionFactor(
                    category_id=cat.id,
                    activity_type=ef["activity_type"],
                    unit=ef["unit"],
                    factor=ef["factor"],
                    source=ef["source"],
                    version="1.0",
                    is_active=True
                ))
        db.commit()

        # Seed achievements
        AchievementService.ensure_default_achievements(db)
        db.close()

        cls.client = TestClient(app, raise_server_exceptions=True)

    def test_01_user_registration(self):
        """Test user registration and duplicate validation."""
        payload = {
            "full_name": "Test Runner",
            "email": "testrunner@carbonlens.dev",
            "password": "SecurePassword123!",
            "public_handle": "TestEcoRunner"
        }
        res = self.client.post("/api/v1/auth/register", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["user"]["email"], "testrunner@carbonlens.dev")
        self.assertEqual(data["user"]["public_handle"], "TestEcoRunner")

        # Test duplicate email rejection
        res_dup = self.client.post("/api/v1/auth/register", json=payload)
        self.assertEqual(res_dup.status_code, 400)
        self.assertIn("already exists", res_dup.json()["detail"])

    def test_02_user_login(self):
        """Test login with valid and invalid credentials."""
        # Valid login
        res = self.client.post("/api/v1/auth/login", json={
            "email": "testrunner@carbonlens.dev",
            "password": "SecurePassword123!"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_token", data)

        # Invalid password
        res_inv = self.client.post("/api/v1/auth/login", json={
            "email": "testrunner@carbonlens.dev",
            "password": "WrongPassword!"
        })
        self.assertEqual(res_inv.status_code, 401)

        # Nonexistent user
        res_non = self.client.post("/api/v1/auth/login", json={
            "email": "unknown@carbonlens.dev",
            "password": "Password123!"
        })
        self.assertEqual(res_non.status_code, 401)

    def test_03_auth_me_endpoint(self):
        """Test retrieving authenticated user profile."""
        login_res = self.client.post("/api/v1/auth/login", json={
            "email": "testrunner@carbonlens.dev",
            "password": "SecurePassword123!"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        res = self.client.get("/api/v1/auth/me", headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["email"], "testrunner@carbonlens.dev")

        # Unauthorized access
        res_unauth = self.client.get("/api/v1/auth/me")
        self.assertEqual(res_unauth.status_code, 401)

    def test_04_carbon_calculation_engine(self):
        """Test carbon calculation service and precision."""
        co2_car = CarbonCalculationService.calculate_co2(100.0, 0.192)
        self.assertEqual(co2_car, 19.2)

        co2_meal = CarbonCalculationService.calculate_co2(3.0, 3.30)
        self.assertEqual(co2_meal, 9.9)

        co2_elec = CarbonCalculationService.calculate_co2(50.0, 0.385)
        self.assertEqual(co2_elec, 19.25)

        co2_walk = CarbonCalculationService.calculate_co2(15.0, 0.0)
        self.assertEqual(co2_walk, 0.0)

    def test_05_activity_crud_and_ownership(self):
        """Test activity creation, listing, updating, deleting, and isolation between users."""
        u1_res = self.client.post("/api/v1/auth/register", json={
            "full_name": "User One",
            "email": "user1@carbonlens.dev",
            "password": "Password123!",
            "public_handle": "UserOne"
        })
        token_u1 = u1_res.json()["access_token"]
        headers_u1 = {"Authorization": f"Bearer {token_u1}"}

        u2_res = self.client.post("/api/v1/auth/register", json={
            "full_name": "User Two",
            "email": "user2@carbonlens.dev",
            "password": "Password123!",
            "public_handle": "UserTwo"
        })
        token_u2 = u2_res.json()["access_token"]
        headers_u2 = {"Authorization": f"Bearer {token_u2}"}

        # 1. Create activity for User 1
        act_payload = {
            "category_id": 1,
            "activity_type": "Car (Gasoline)",
            "quantity": 50.0,
            "unit": "km",
            "activity_date": str(datetime.date.today()),
            "notes": "Driving to work"
        }
        res_create = self.client.post("/api/v1/activities", json=act_payload, headers=headers_u1)
        self.assertEqual(res_create.status_code, 201)
        act_data = res_create.json()
        act_id = act_data["id"]
        self.assertEqual(act_data["calculated_co2"], 9.6)

        # 2. User 1 can see it
        res_get = self.client.get(f"/api/v1/activities/{act_id}", headers=headers_u1)
        self.assertEqual(res_get.status_code, 200)

        # 3. User 2 CANNOT access User 1's activity
        res_forbidden = self.client.get(f"/api/v1/activities/{act_id}", headers=headers_u2)
        self.assertEqual(res_forbidden.status_code, 403)

        # 4. User 2 cannot delete User 1's activity
        res_del_forbidden = self.client.delete(f"/api/v1/activities/{act_id}", headers=headers_u2)
        self.assertEqual(res_del_forbidden.status_code, 403)

        # 5. User 1 updates activity quantity
        res_update = self.client.put(f"/api/v1/activities/{act_id}", json={"quantity": 100.0}, headers=headers_u1)
        self.assertEqual(res_update.status_code, 200)
        self.assertEqual(res_update.json()["calculated_co2"], 19.2)

        # 6. User 1 deletes activity
        res_del = self.client.delete(f"/api/v1/activities/{act_id}", headers=headers_u1)
        self.assertEqual(res_del.status_code, 200)

        # 7. Activity no longer exists
        res_check = self.client.get(f"/api/v1/activities/{act_id}", headers=headers_u1)
        self.assertEqual(res_check.status_code, 404)

    def test_06_goals_and_budget_tracking(self):
        """Test carbon goal target setting and progress."""
        login_res = self.client.post("/api/v1/auth/login", json={
            "email": "user1@carbonlens.dev",
            "password": "Password123!"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        goal_payload = {
            "monthly_target": 180.0,
            "start_date": str(datetime.date.today())
        }
        res_goal = self.client.post("/api/v1/goals", json=goal_payload, headers=headers)
        self.assertEqual(res_goal.status_code, 201)
        self.assertEqual(res_goal.json()["monthly_target"], 180.0)

        res_prog = self.client.get("/api/v1/goals/current", headers=headers)
        self.assertEqual(res_prog.status_code, 200)
        self.assertEqual(res_prog.json()["monthly_target"], 180.0)

    def test_07_what_if_simulator(self):
        """Test What-If simulation service and calculations."""
        db = TestingSessionLocal()
        sim_res = SimulatorService.simulate(
            db=db,
            activity_type="Car (Gasoline)",
            current_quantity=500.0,
            reduction_percentage=20.0,
        )
        db.close()
        self.assertEqual(sim_res["current_monthly_emissions_kg"], 96.0)
        self.assertEqual(sim_res["projected_monthly_emissions_kg"], 76.8)
        self.assertEqual(sim_res["monthly_emissions_saved_kg"], 19.2)
        self.assertEqual(sim_res["annual_emissions_saved_kg"], 230.4)
        self.assertGreater(sim_res["trees_equivalent_annual"], 0)

        res = self.client.post("/api/v1/simulator/calculate", json={
            "activity_type": "Car (Gasoline)",
            "current_quantity": 500.0,
            "reduction_percentage": 20.0
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["annual_emissions_saved_kg"], 230.4)

    def test_08_recommendations_engine(self):
        """Test smart recommendations generator."""
        login_res = self.client.post("/api/v1/auth/login", json={
            "email": "user1@carbonlens.dev",
            "password": "Password123!"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        res = self.client.get("/api/v1/recommendations", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("recommendations", data)
        self.assertGreaterEqual(len(data["recommendations"]), 1)
        self.assertGreater(data["total_potential_monthly_savings_kg"], 0)

    def test_09_achievements_evaluation(self):
        """Test achievements listing and auto-unlocking."""
        login_res = self.client.post("/api/v1/auth/login", json={
            "email": "user1@carbonlens.dev",
            "password": "Password123!"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        self.client.post("/api/v1/activities", json={
            "category_id": 1,
            "activity_type": "Subway / Metro",
            "quantity": 10.0,
            "unit": "km",
            "activity_date": str(datetime.date.today()),
            "notes": "Eco commute"
        }, headers=headers)

        res = self.client.get("/api/v1/achievements", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(data["unlocked_count"], 1)

        first_step = next((a for a in data["items"] if a["slug"] == "first_step"), None)
        self.assertIsNotNone(first_step)
        self.assertTrue(first_step["is_unlocked"])

    def test_10_leaderboard(self):
        """Test privacy-safe leaderboard endpoint."""
        res = self.client.get("/api/v1/leaderboard")
        self.assertEqual(res.status_code, 200)
        items = res.json()
        self.assertIsInstance(items, list)
        if len(items) > 0:
            entry = items[0]
            self.assertIn("rank", entry)
            self.assertIn("display_name", entry)
            self.assertIn("sustainability_score", entry)
            self.assertNotIn("@", entry["display_name"])

    def test_11_dashboard_summary(self):
        """Test full dashboard summary calculation."""
        login_res = self.client.post("/api/v1/auth/login", json={
            "email": "user1@carbonlens.dev",
            "password": "Password123!"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        res = self.client.get("/api/v1/dashboard/summary", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("total_monthly_emissions", data)
        self.assertIn("sustainability_score", data)
        self.assertIn("categories_breakdown", data)
        self.assertIn("monthly_trend", data)
        self.assertIn("goal", data)


if __name__ == "__main__":
    unittest.main()
