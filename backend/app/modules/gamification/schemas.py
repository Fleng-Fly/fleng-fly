from datetime import date, datetime

from app.core.schemas import CamelModel


class StreakResponse(CamelModel):
    current: int
    longest: int
    last_activity_date: date | None
    timezone: str


class AchievementResponse(CamelModel):
    code: str
    title: str
    awarded_at: datetime | None


class LeaderboardEntry(CamelModel):
    rank: int
    display_name: str
    xp: int
    lessons_completed: int
    streak: int
    is_current_user: bool


class LeaderboardResponse(CamelModel):
    entries: list[LeaderboardEntry]
    current_user: LeaderboardEntry | None
    total: int
