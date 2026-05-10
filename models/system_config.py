"""
SystemConfig — single-row app-wide config (id=1 always).
Holds FICA/FUTA rates, WC factors, pay period map, commission defaults,
ancillary rates, and additional fee schedules. Seeded by testing/seed.py.
"""
from sqlalchemy import Column, Float, Integer, String, Text
from database import Base


class SystemConfig(Base):
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, default=1)

    # FICA
    ss_rate = Column(Float, default=0.062)
    medicare_rate = Column(Float, default=0.0145)
    ss_wage_base = Column(Float, default=176100)

    # FUTA
    futa_rate = Column(Float, default=0.006)
    futa_wage_base = Column(Float, default=7000)

    # WC factors
    fixed_cost_factor = Column(Float, default=0.39)
    loss_fund_factor = Column(Float, default=0.5)
    combined_cost_factor = Column(Float, default=0.89)
    pte_weight = Column(Float, default=0.75)

    # WC state lists (comma-separated)
    monopolistic_states = Column(String, default="WA,WY,ND,OH")
    mcp_states = Column(String, default="RI,NY,NJ,PA,LA,WI,MN,SD,KS,MT,AZ,UT,NV,CA,OR")
    independent_bureau_states = Column(String, default="CA,DE,PA,MI,NJ,TX")

    # Pay periods JSON: {"weekly":52,"biweekly":26,"semimonthly":24,"monthly":12}
    pay_periods_json = Column(Text, default='{"weekly":52,"biweekly":26,"semimonthly":24,"monthly":12}')

    # Sunz carrier charge — currently 0 in practice, reserved
    wc_policy_adjustment = Column(Float, default=0.0)

    # Business Consultant commissions — system-level defaults shown on config page
    consultant_commission_upfront = Column(Float, default=0.25)  # no-broker only
    consultant_commission_ongoing = Column(Float, default=0.20)  # no-broker only
    admin_commission_pool_pct = Column(Float, default=0.40)      # total pool split between broker + consultant
    consultant_min_ongoing_pct = Column(Float, default=0.10)     # consultant floor when broker is on the deal

    # Ancillary service rates — constant defaults applied to all clients
    tlm_rate     = Column(Float, default=0.0)   # $/WSE/month × 12
    wire_ach_rate = Column(Float, default=0.0)  # $/pay period × pay_periods

    futa_approach = Column(String, default="B")

    # Additional Fees — Payroll
    fee_min_admin_per_cycle = Column(Float, default=50.0)
    fee_delivery_min = Column(Float, default=15.0)
    fee_delivery_max = Column(Float, default=60.0)
    fee_out_of_cycle_payroll = Column(Float, default=25.0)
    fee_returned_check = Column(Float, default=50.0)

    # Additional Fees — Timekeeping
    fee_timekeeping_implementation = Column(Float, default=250.0)
    fee_timekeeping_monthly_per_ee = Column(Float, default=4.50)

    # Additional Fees — HR Technology
    fee_applicant_tracking_implementation = Column(Float, default=250.0)
    fee_online_lms_implementation = Column(Float, default=200.0)
    fee_online_lms_per_ee_monthly = Column(Float, default=1.50)
    fee_mvr_report = Column(Float, default=6.0)
    fee_everify_per_ee = Column(Float, default=5.0)

    # Additional Fees — Workers' Comp
    fee_wc_waiver_subrogation = Column(Float, default=200.0)
    fee_wc_late_reporting = Column(Float, default=250.0)
    fee_wc_alternate_employer_endorsement = Column(Float, default=200.0)

    # Additional Fees — Account
    fee_reactivation = Column(Float, default=500.0)
    fee_late_payroll_submission = Column(Float, default=50.0)
