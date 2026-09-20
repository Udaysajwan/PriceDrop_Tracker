from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Union, Any
from backend.app.schemas.price_history import PriceHistoryResponse


class ProductBase(BaseModel):
    title: Optional[str] = None
    url: str
    target_price: float


class ProductCreate(BaseModel):
    url: str
    target_price: float
    title: Optional[str] = None


class ProductUpdate(BaseModel):
    target_price: Optional[float] = None
    title: Optional[str] = None


class ProductResponse(BaseModel):
    id: Union[str, int]
    user_id: Union[str, int]
    title: str
    url: str
    target_price: float
    current_price: Optional[float] = None
    currency: str = "INR"
    image_url: Optional[str] = None
    in_stock: bool = True
    last_scraped_at: Optional[Union[str, Any]] = None
    created_at: Optional[Union[str, Any]] = None
    updated_at: Optional[Union[str, Any]] = None
    price_dropped: bool = False
    percent_change_from_target: Optional[float] = None

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class ProductSummary(BaseModel):
    product_id: Union[str, int]
    title: str
    target_price: float
    current_price: Optional[float]
    lowest_price: Optional[float]
    highest_price: Optional[float]
    average_price: Optional[float]
    total_checks: int
    price_dropped: bool
    savings_amount: Optional[float] = None
    savings_percent: Optional[float] = None
    first_recorded_price: Optional[float] = None
    percent_change_overall: Optional[float] = None
