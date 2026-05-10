from sqlalchemy import Column, Float, Integer, String
from database import Base


class AdminRevenueRow(Base):
    __tablename__ = "admin_revenue_rows"

    id       = Column(Integer, primary_key=True, autoincrement=True)
    client   = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    m1  = Column(Float, default=0)
    m2  = Column(Float, default=0)
    m3  = Column(Float, default=0)
    m4  = Column(Float, default=0)
    m5  = Column(Float, default=0)
    m6  = Column(Float, default=0)
    m7  = Column(Float, default=0)
    m8  = Column(Float, default=0)
    m9  = Column(Float, default=0)
    m10 = Column(Float, default=0)
    m11 = Column(Float, default=0)
    m12 = Column(Float, default=0)
    total = Column(Float, default=0)
