"""
Two database tables for state unemployment tax (SUTA). SutaLine is one row per state a
client has employees in — it stores that state's gross wages, headcount, and the billing
and cost rates that will be used to calculate the SUTA charge. SutaRate is VHR's master
rate table with one row per state (51 total), holding the threshold, VHR's billing rate,
and VHR's cost rate. Rates are stored as decimals throughout — 0.027 means 2.7%.
"""
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
