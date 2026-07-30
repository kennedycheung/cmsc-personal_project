from pydantic import BaseModel, ConfigDict

from app.models.user_preference import UserPreference


class UserPreferenceUpdate(BaseModel):
    max_budget_per_day: float | None = None
    interests: list[str] | None = None
    travel_style: str | None = None


class UserPreferenceRead(BaseModel):
    max_budget_per_day: float | None = None
    interests: list[str] = []
    travel_style: str | None = None
    updated_at: str

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, preference: UserPreference) -> "UserPreferenceRead":
        return cls(
            max_budget_per_day=preference.max_budget_per_day,
            interests=preference.interest_list(),
            travel_style=preference.travel_style,
            updated_at=preference.updated_at,
        )
