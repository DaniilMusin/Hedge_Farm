from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime

class PriceRequest(BaseModel):
    culture: Literal["wheat"] = Field(default="wheat", description="Crop type for hedging")
    volume_t: int = Field(gt=0, le=1000000, description="Volume in tons")
    term_m: int = Field(default=6, ge=1, le=12, description="Term in months")

class PriceResponse(BaseModel):
    culture: str = Field(description="Crop type")
    volume_t: int = Field(description="Volume in tons")
    term_m: int = Field(description="Term in months")
    floor_futures_rubkg: float = Field(description="Floor price with futures hedge, RUB/kg")
    floor_put_rubkg: float = Field(description="Floor price with PUT option hedge, RUB/kg")
    floor_forward_rubkg: float = Field(description="Floor price with forward hedge, RUB/kg")
    recommended: Literal["futures", "put", "put_ladder", "forward"] = Field(description="Recommended instrument")
    calculated_at: datetime = Field(description="Calculation timestamp")