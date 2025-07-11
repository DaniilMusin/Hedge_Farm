from pydantic import BaseModel

class PriceRequest(BaseModel):
    culture: str = "wheat"
    volume_t: int
    term_m: int = 6

class PriceResponse(BaseModel):
    culture: str
    volume_t: int
    term_m: int
    floor_futures: float
    floor_put: float
    floor_forward: float
    recommended: str