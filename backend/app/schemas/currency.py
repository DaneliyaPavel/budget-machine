from pydantic import BaseModel, ConfigDict

STRICT = ConfigDict(strict=True)
ORM_STRICT = ConfigDict(from_attributes=True, strict=True)


class CurrencyBase(BaseModel):
    code: str
    name: str
    symbol: str
    precision: int = 2

    model_config = STRICT


class CurrencyCreate(CurrencyBase):
    pass


class Currency(CurrencyBase):
    model_config = ORM_STRICT
