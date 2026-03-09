from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal

class NailServiceBase(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        examples=["Gel Manicure"]
    )
    description: str | None = Field(
        default=None,
        max_length= 500
    )
    duration_minutes: int = Field(
        ...,
        gt=0,
        le=210,
        description="How long the service takes in minutes"
    )
    price: Decimal = Field(
        ...,
        gt= 0,
        decimal_places= 2,
        description="Price in Euros"
    )

class NailServiceCreate(NailServiceBase):
    pass

class NailServiceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    duration_minutes: int | None = Field(default=None, gt=0, le=210)
    price: Decimal | None = Field(default=None, gt=0, decimal_places=2)

class NailServiceResponse(NailServiceBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
