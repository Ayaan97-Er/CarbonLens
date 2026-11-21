from app.schemas.auth import Token, TokenPayload, LoginRequest, RegisterRequest, PasswordChangeRequest
from app.schemas.user import UserBase, UserCreate, UserUpdate, UserOut, LeaderboardEntry
from app.schemas.category import (
    CategoryBase,
    CategoryCreate,
    CategoryOut,
    CategoryDetailOut,
    EmissionFactorBase,
    EmissionFactorCreate,
    EmissionFactorOut,
)
from app.schemas.activity import (
    ActivityBase,
    ActivityCreate,
    ActivityUpdate,
    ActivityOut,
    PaginatedActivities,
    ActivityCalculationPreview,
)
from app.schemas.goal import GoalBase, GoalCreate, GoalUpdate, GoalOut, GoalProgressOut
from app.schemas.dashboard import (
    DashboardSummary,
    CategoryEmissions,
    MonthlyTrendPoint,
    DailyEmissionsPoint,
    SustainabilityScoreDetail,
)
from app.schemas.recommendation import RecommendationOut, RecommendationsResponse
from app.schemas.simulator import SimulatorRequest, SimulatorResult, QuickScenarioPreset
from app.schemas.achievement import AchievementOut, UserAchievementOut, AchievementsSummary
from app.schemas.admin import AdminUserOut, AdminUserUpdateRole, SystemStatsOut

__all__ = [
    "Token",
    "TokenPayload",
    "LoginRequest",
    "RegisterRequest",
    "PasswordChangeRequest",
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserOut",
    "LeaderboardEntry",
    "CategoryBase",
    "CategoryCreate",
    "CategoryOut",
    "CategoryDetailOut",
    "EmissionFactorBase",
    "EmissionFactorCreate",
    "EmissionFactorOut",
    "ActivityBase",
    "ActivityCreate",
    "ActivityUpdate",
    "ActivityOut",
    "PaginatedActivities",
    "ActivityCalculationPreview",
    "GoalBase",
    "GoalCreate",
    "GoalUpdate",
    "GoalOut",
    "GoalProgressOut",
    "DashboardSummary",
    "CategoryEmissions",
    "MonthlyTrendPoint",
    "DailyEmissionsPoint",
    "SustainabilityScoreDetail",
    "RecommendationOut",
    "RecommendationsResponse",
    "SimulatorRequest",
    "SimulatorResult",
    "QuickScenarioPreset",
    "AchievementOut",
    "UserAchievementOut",
    "AchievementsSummary",
    "AdminUserOut",
    "AdminUserUpdateRole",
    "SystemStatsOut",
]
