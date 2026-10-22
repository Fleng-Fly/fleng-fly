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
