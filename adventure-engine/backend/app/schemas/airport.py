from pydantic import BaseModel, ConfigDict


class AirportRead(BaseModel):
    id: int
    destination_id: int
    iata_code: str
    name: str
    distance_km: float
    ground_transport_cost_usd: float
    ground_transport_minutes: float
    baseline_fare_usd: float
    is_primary: bool

    model_config = ConfigDict(from_attributes=True)
