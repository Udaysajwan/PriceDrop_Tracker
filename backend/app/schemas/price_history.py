from pydantic import BaseModel, ConfigDict
from typing import Union, Any


class PriceHistoryBase(BaseModel):
    price: float


class PriceHistoryCreate(PriceHistoryBase):
    product_id: Union[str, int]


class PriceHistoryResponse(PriceHistoryBase):
    id: Union[str, int]
    product_id: Union[str, int]
    scraped_at: Union[str, Any]

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
