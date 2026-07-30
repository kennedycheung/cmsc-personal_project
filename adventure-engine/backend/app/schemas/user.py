from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    id: int
    email: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)
