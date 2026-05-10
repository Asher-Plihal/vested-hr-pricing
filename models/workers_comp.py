"""
Four database tables related to workers compensation. WCLine is one row per class code
a client has — state, code, payroll, and headcount. WCLoss is one row per policy period
in the client's loss history. WCRate is the full rate table (~25K rows) used to look up
the cost rate for any state and class code combination. WCGuideline is the underwriting
reference table (~19.5K rows) that provides hazard group and eligibility flags — it is
not used in billing math, just for reference.
"""
from sqlalchemy import Column, Float, ForeignKey, Integer, String
from database import Base


class WCLine(Base):
    __tablename__ = "wc_lines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    state = Column(String)
    wc_code = Column(String)
    wc_description = Column(String)
    hazard_group = Column(String)
    annual_gw = Column(Float, default=0.0)
    ftes = Column(Float, default=0.0)
    ptes = Column(Float, default=0.0)
    current_client_rate = Column(Float, default=0.0)
    # Manual rate from WC Rates table — stored at intake since full WC Rates table not yet imported
    manual_rate = Column(Float, default=0.0)
    flag_100k = Column(String, nullable=True)


class WCLoss(Base):
    __tablename__ = "wc_losses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    coverage_period_start = Column(String)
    coverage_period_end = Column(String)
    total_losses_incurred = Column(Float, default=0.0)
    num_claims = Column(Integer, default=0)
    months_in_policy = Column(Integer, default=0)
    open_claims = Column(Integer, default=0)


class WCRate(Base):
    __tablename__ = "wc_rates"

    id = Column(Integer, primary_key=True)
    carrier = Column(String)
    state = Column(String(2), index=True)
    class_code = Column(String, index=True)
    concat = Column(String, index=True)  # state + class_code, lookup key
    rate = Column(Float)                 # per $100 payroll
    min_premium = Column(Float, nullable=True)
    description = Column(String, nullable=True)
    effective_date = Column(String, nullable=True)


class WCGuideline(Base):
    __tablename__ = "wc_guidelines"

    id = Column(Integer, primary_key=True)
    state = Column(String(2), index=True)
    ncci_code = Column(String)
    lookup_code = Column(String)
    concat = Column(String, index=True)
    irmi_classification = Column(String, nullable=True)
    naics = Column(String, nullable=True)
    hazard_group = Column(String, nullable=True)
    flag_100k = Column(String, nullable=True)  # SUB, RSTD, EXCLD
    effective_date = Column(String, nullable=True)
