from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String
from database import Base


class SutaLine(Base):
    __tablename__ = "suta_lines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    state = Column(String)
    gws = Column(Float, default=0.0)
    total_wses = Column(Float, default=0.0)
    current_client_rate = Column(Float, default=0.0)
    billing_rate = Column(Float, default=0.0)
    cost_rate = Column(Float, default=0.0)
    threshold = Column(Float, default=0.0)
    turnover_pct = Column(Float, default=0.10)


class SutaRate(Base):
    __tablename__ = "suta_rates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    state = Column(String, unique=True, nullable=False)
    threshold = Column(Float)
    vhr_min_rate = Column(Float)
    client_reporting = Column(Boolean, default=False)
    our_cost = Column(Float)
    date_updated = Column(String, nullable=True)
