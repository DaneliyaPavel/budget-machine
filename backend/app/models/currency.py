from sqlalchemy import Column, String, Integer

from ..database import Base


class Currency(Base):
    __tablename__ = "currencies"

    code = Column(String(3), primary_key=True)
    name = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    precision = Column(Integer, default=2)
