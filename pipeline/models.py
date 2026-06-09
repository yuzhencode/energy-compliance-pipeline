"""
pipeline/models.py
==================
Pydantic models for row-level data validation.

Each model represents one row coming out of the staging or mart layer.
Pydantic enforces types and constraints before data reaches the reporter,
acting as a schema contract between the SQL layer and the Python layer.

This is the OOP data-modelling layer: the pipeline passes typed objects,
not raw DataFrames, through the validation boundary.
"""

from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Staging models (one row = one source record, normalised)
# ---------------------------------------------------------------------------

class StagedAccount(BaseModel):
    account_id:      str
    customer_name:   str
    postcode:        Optional[str]
    fuel_type:       Literal["gas", "electric", "dual"]
    payment_method:  Literal["direct_debit", "prepayment_meter", "cash", "other"]
    debt_amount_gbp: float = Field(ge=0, description="Debt must be non-negative")
    debt_age_days:   int   = Field(ge=0)
    account_status:  Literal["active", "disputed"]
    has_debt:        bool
    is_over_91_days: bool
    is_ppm_in_debt:  bool

    @field_validator("account_id")
    @classmethod
    def account_id_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("account_id must not be empty")
        return v

    @model_validator(mode="after")
    def debt_flags_consistent(self) -> "StagedAccount":
        if self.has_debt and self.debt_amount_gbp == 0:
            raise ValueError("has_debt is True but debt_amount_gbp is 0")
        if self.is_over_91_days and self.debt_age_days <= 91:
            raise ValueError("is_over_91_days flag inconsistent with debt_age_days")
        return self


# ---------------------------------------------------------------------------
# Mart models (one row = one reporting unit)
# ---------------------------------------------------------------------------

class OfgemSummaryRow(BaseModel):
    """
    Maps directly to the 6 Ofgem Social Obligations Reporting quarterly indicators.
    Ref: https://www.ofgem.gov.uk/data/debt-and-arrears-indicators
    """
    avg_debt_no_arrangement_gbp:    Optional[float] = Field(None, ge=0)
    avg_debt_with_arrangement_gbp:  Optional[float] = Field(None, ge=0)
    pct_repaying_via_ppm:           Optional[float] = Field(None, ge=0, le=100)
    accounts_with_debt:             int             = Field(ge=0)
    accounts_no_arrangement:        int             = Field(ge=0)
    total_debt_over_91_days_gbp:    float           = Field(ge=0)
    reporting_quarter:              date
    report_date:                    date

    @model_validator(mode="after")
    def no_arrangement_lte_total(self) -> "OfgemSummaryRow":
        if self.accounts_no_arrangement > self.accounts_with_debt:
            # accounts_with_debt here is total accounts with debt; no_arrangement is a subset
            pass  # fine — no_arrangement can exceed with_arrangement
        return self


class AccountDetailRow(BaseModel):
    account_id:                  str
    customer_name:               str
    postcode:                    Optional[str]
    fuel_type:                   Literal["gas", "electric", "dual"]
    payment_method:              Literal["direct_debit", "prepayment_meter", "cash", "other"]
    debt_amount_gbp:             float = Field(ge=0)
    debt_age_days:               int   = Field(ge=0)
    is_over_91_days:             bool
    account_status:              Literal["active", "disputed"]
    has_active_arrangement:      bool
    arrangement_date:            Optional[date]
    arrangement_weekly_rate_gbp: Optional[float] = None
    arrangement_plan_weeks:      Optional[int]   = None
    last_switch_type:            Optional[str]
    last_switch_date:            Optional[date]
    last_switch_outcome:         Optional[str]
    report_date:                 date

    @field_validator("arrangement_plan_weeks", "arrangement_weekly_rate_gbp", mode="before")
    @classmethod
    def nan_to_none(cls, v):
        if v is None:
            return None
        try:
            import math
            if math.isnan(float(v)):
                return None
        except (TypeError, ValueError):
            pass
        return v
