"""Home Credit LAP Voice Agent — Business Rules and Qualification Engine.

This module implements deterministic validation and state management for the
seven Loan Against Property (LAP) preliminary eligibility criteria, transfer
triggers, loan amount caps, and conversation outcome routing according to the
Home Credit LAP assignment specification.
"""

from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Dict, List, Optional, Set, Tuple


class Outcome(str, Enum):
    """The 13 defined call outcomes for the Home Credit LAP agent."""
    IDENTITY_NOT_VERIFIED = "identity_not_verified"
    CALLBACK_REQUESTED = "callback_requested"
    NOT_INTERESTED = "not_interested"
    DO_NOT_CALL = "do_not_call"
    TRANSFER_REFERRAL = "transfer_referral"
    DISQUALIFIED_PROPERTY_TYPE = "disqualified_property_type"
    DISQUALIFIED_OWNERSHIP = "disqualified_ownership"
    DISQUALIFIED_DOCUMENTS = "disqualified_documents"
    DISQUALIFIED_INCOME = "disqualified_income"
    DISQUALIFIED_TENURE = "disqualified_tenure"
    DECLINED_LOAN_CAP = "declined_loan_cap"
    CALL_INCOMPLETE = "call_incomplete"
    QUALIFIED_EXPERT_CALLBACK = "qualified_expert_callback"


class Status(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    TRANSFER_TRIGGER = "TRANSFER_TRIGGER"


@dataclass
class EvalResult:
    status: Status
    normalized_value: Optional[str] = None
    outcome_if_failed: Optional[Outcome] = None
    reason: str = ""


# Max loan amount cap in Lakhs
MAX_LOAN_AMOUNT_LAKH = 75.0
MIN_TENURE_YEARS = 3
MAX_TENURE_YEARS = 15


def parse_inr_amount_to_lakh(text: str) -> Optional[float]:
    """Parses text containing INR amounts (lakh, crore, k, numbers) into Lakhs."""
    t = str(text).lower().strip().replace(",", "")
    
    # Check crore: e.g., "1.2 crore", "1 crore"
    m_cr = re.search(r"(\d+(?:\.\d+)?)\s*(?:cr|crore|crores)", t)
    if m_cr:
        return float(m_cr.group(1)) * 100.0
    
    # Check lakh: e.g., "40 lakh", "75 lakhs", "50 lac"
    m_lakh = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakh|lakhs|lac|lacs|l)", t)
    if m_lakh:
        return float(m_lakh.group(1))
    
    # Check raw numbers: e.g., 4000000, 7500000
    m_num = re.search(r"\b(\d{5,9})\b", t)
    if m_num:
        val = float(m_num.group(1))
        return val / 100000.0
    
    # Check small integer if context is obvious (e.g., "40", "75")
    m_short = re.search(r"\b(\d{1,3})\b", t)
    if m_short:
        val = float(m_short.group(1))
        # If between 1 and 200, assume Lakhs
        if 1.0 <= val <= 200.0:
            return val
            
    return None


def parse_tenure_to_years(text: str) -> Optional[float]:
    """Parses tenure expression in months or years into years."""
    t = str(text).lower().strip()
    
    # Check months: e.g., "36 months"
    m_m = re.search(r"(\d+(?:\.\d+)?)\s*(?:month|months|m)\b", t)
    if m_m:
        months = float(m_m.group(1))
        return months / 12.0
    
    # Check years: e.g., "10 years", "5 yr", "3 yrs"
    m_y = re.search(r"(\d+(?:\.\d+)?)\s*(?:year|years|yr|yrs|y)\b", t)
    if m_y:
        return float(m_y.group(1))
    
    # Plain integer e.g., "10", "20"
    m_num = re.search(r"\b(\d{1,2})\b", t)
    if m_num:
        return float(m_num.group(1))
        
    return None


def check_transfer_trigger(text: str) -> Tuple[bool, Optional[str]]:
    """Checks if utterance mentions property loan transfer, refinance, or EMI reduction.
    
    Unrelated loans (car loan, personal loan, credit card) do NOT trigger a transfer referral.
    """
    t = text.lower()
    
    # Negative check: purely car / personal / credit card loan without property context
    has_unrelated_only = (
        ("car loan" in t or "vehicle loan" in t or "personal loan" in t or "credit card" in t)
        and not any(k in t for k in ["home loan", "property loan", "mortgage", "housing loan", "takeover", "refinanc"])
    )
    if has_unrelated_only:
        return False, None
    
    # Regex and pattern triggers for property loan transfer / refinancing / EMI reduction:
    if re.search(r"\b(?:reduce|lower|cut|decrease)\b.*\b(?:emi|interest|rate)\b", t):
        return True, "EMI or rate reduction requested on property loan"

    if re.search(r"\b(?:balance\s*transfer|loan\s*takeover|take\s*over\s*my\s*loan|refinanc)", t):
        return True, "Balance transfer / refinancing requested"

    if re.search(r"\b(?:existing|already\s*have\s*a)\b.*\b(?:home\s*loan|property\s*loan|mortgage|housing\s*loan)\b", t):
        return True, "Existing property loan detected"

    if re.search(r"\b(?:already\s*have\s*a\s*loan)\b.*\b(?:flat|house|property)\b", t):
        return True, "Existing loan on property detected"

    if re.search(r"\b(?:documents?|originals?|papers?)\b.*\b(?:with|at|held\s*by|pledged\s*to)\b.*\b(?:bank|sbi|hdfc|icici|lender|nbfc)\b", t):
        return True, "Original property documents held by lender against loan"

    triggers = [
        ("balance transfer", "balance transfer requested"),
        ("loan transfer", "loan transfer requested"),
        ("transfer my loan", "loan transfer requested"),
        ("take over", "loan takeover requested"),
        ("takeover", "loan takeover requested"),
        ("refinanc", "refinancing requested"),
        ("existing home loan", "existing home loan balance"),
        ("existing property loan", "existing property loan"),
        ("already have a home loan", "existing home loan balance"),
        ("already have a loan against property", "existing LAP"),
        ("pledged with bank", "documents pledged with bank"),
        ("mortgaged with", "property mortgaged with bank"),
    ]
    for pattern, reason in triggers:
        if pattern in t:
            return True, reason
            
    return False, None


def evaluate_property_type(text: str) -> EvalResult:
    """Criterion 1: Residential, Commercial pass. Agricultural, Industrial fail immediately."""
    t = text.lower()
    if any(k in t for k in ["agricultural", "farmland", "farm land", "village land", "khet", "krishi"]):
        return EvalResult(
            Status.FAIL,
            normalized_value="agricultural",
            outcome_if_failed=Outcome.DISQUALIFIED_PROPERTY_TYPE,
            reason="Agricultural property is ineligible for this LAP offer."
        )

    if any(re.search(rf"\b{re.escape(k)}\b", t) for k in ["industrial", "factory", "warehouse", "industrial shed"]):
        return EvalResult(
            Status.FAIL,
            normalized_value="industrial",
            outcome_if_failed=Outcome.DISQUALIFIED_PROPERTY_TYPE,
            reason="Industrial property is ineligible for this LAP offer."
        )
    
    # Ambiguous terms (plot, land, farmhouse, mixed use) must be checked before generic terms like house
    if any(k in t for k in ["plot", "land", "farmhouse", "mixed use"]):
        return EvalResult(
            Status.NEEDS_CLARIFICATION,
            reason="Ambiguous property type; clarify if residential, commercial, industrial, or agricultural."
        )

    if any(re.search(rf"\b{re.escape(k)}\b", t) for k in ["residential", "flat", "apartment", "house", "villa", "bungalow", "builder floor"]):
        return EvalResult(Status.PASS, normalized_value="residential", reason="Residential property is eligible.")
    
    if any(re.search(rf"\b{re.escape(k)}\b", t) for k in ["commercial", "shop", "office", "showroom", "godown", "retail"]):
        return EvalResult(Status.PASS, normalized_value="commercial", reason="Commercial property is eligible.")
        
    return EvalResult(Status.NEEDS_CLARIFICATION, reason="Property type not recognized.")


def evaluate_ownership(text: str) -> EvalResult:
    """Criterion 2: Sole or joint ownership passes. Non-owner fails."""
    t = text.lower()
    
    if any(k in t for k in ["not in my name", "parent", "father's name", "mother's name", "brother's name only", "friend", "tenant", "rented"]):
        return EvalResult(
            Status.FAIL,
            normalized_value="third_party",
            outcome_if_failed=Outcome.DISQUALIFIED_OWNERSHIP,
            reason="Customer is neither owner nor co-owner of the property."
        )
        
    if any(k in t for k in ["sole", "own name", "my own", "single owner", "only me", "myself", "in my name"]):
        return EvalResult(Status.PASS, normalized_value="sole", reason="Sole ownership is eligible.")
        
    if any(k in t for k in ["joint", "jointly", "co-owner", "with wife", "with husband", "with brother", "with spouse", "with father"]):
        return EvalResult(Status.PASS, normalized_value="joint", reason="Joint ownership is eligible.")
        
    return EvalResult(Status.NEEDS_CLARIFICATION, reason="Clarify whether customer is sole owner or joint owner.")


def evaluate_documents(text: str) -> EvalResult:
    """Criterion 3: Available originals pass. Lost/photocopies fail. Held with lender -> transfer trigger."""
    t = text.lower()
    
    # Check if documents held by bank/lender
    if any(k in t for k in ["with bank", "with sbi", "with hdfc", "with icici", "with lender", "pledged", "mortgaged"]):
        return EvalResult(
            Status.TRANSFER_TRIGGER,
            normalized_value="held_by_lender",
            outcome_if_failed=Outcome.TRANSFER_REFERRAL,
            reason="Documents held by lender against loan; routes to loan-transfer specialist."
        )
        
    if any(k in t for k in ["lost", "photocopy", "photocopies", "copies only", "unavailable", "missing", "destroyed"]):
        return EvalResult(
            Status.FAIL,
            normalized_value="unavailable",
            outcome_if_failed=Outcome.DISQUALIFIED_DOCUMENTS,
            reason="Original property documents are unavailable."
        )
        
    if any(k in t for k in ["available", "yes", "i have them", "with me", "in hand", "original exist", "originals are with me", "have original"]):
        return EvalResult(Status.PASS, normalized_value="available", reason="Original documents available.")
        
    return EvalResult(Status.NEEDS_CLARIFICATION, reason="Clarify if customer can produce original documents.")


def evaluate_loan_amount(text_or_val: str) -> EvalResult:
    """Criterion 4: Up to 75 Lakh passes. Above 75 Lakh triggers cap check."""
    amt_lakh = parse_inr_amount_to_lakh(str(text_or_val))
    if amt_lakh is None:
        return EvalResult(Status.NEEDS_CLARIFICATION, reason="Loan amount not specified or unclear.")
        
    if amt_lakh <= MAX_LOAN_AMOUNT_LAKH:
        return EvalResult(
            Status.PASS,
            normalized_value=f"₹{amt_lakh:.1f} lakh",
            reason=f"Loan amount of ₹{amt_lakh:.1f} lakh is within the ₹{MAX_LOAN_AMOUNT_LAKH:.0f} lakh cap."
        )
    else:
        return EvalResult(
            Status.NEEDS_CLARIFICATION,
            normalized_value=f"₹{amt_lakh:.1f} lakh",
            reason=f"Requested amount ₹{amt_lakh:.1f} lakh exceeds ₹{MAX_LOAN_AMOUNT_LAKH:.0f} lakh cap; offer limit continuation."
        )


def evaluate_occupation_and_income(text: str) -> EvalResult:
    """Criterion 5: Salaried or self-employed + bank credit pass. Cash or unemployed fails."""
    t = text.lower()
    
    # Disqualification: purely cash income
    if any(k in t for k in ["cash only", "all in cash", "entirely cash", "income in cash", "cash income", "paid in cash", "all my income is in cash"]):
        return EvalResult(
            Status.FAIL,
            normalized_value="cash_income",
            outcome_if_failed=Outcome.DISQUALIFIED_INCOME,
            reason="Income received in cash is not eligible."
        )
        
    # Disqualification: non-earning (student, unemployed)
    if any(k in t for k in ["unemployed", "student", "no income", "not working", "jobless"]):
        return EvalResult(
            Status.FAIL,
            normalized_value="unemployed",
            outcome_if_failed=Outcome.DISQUALIFIED_INCOME,
            reason="Applicant must be salaried or self-employed."
        )
        
    # Check valid occupation
    is_salaried = any(k in t for k in ["salaried", "job", "salary", "employed"])
    is_self_employed = any(k in t for k in ["self-employed", "self employed", "business", "shop", "practice", "professional"])
    
    # Check bank mode
    has_bank = any(k in t for k in ["bank", "account", "direct credit", "cheque", "neft", "rtgs", "credited"])
    
    if (is_salaried or is_self_employed) and has_bank:
        occ = "salaried" if is_salaried else "self-employed"
        return EvalResult(
            Status.PASS,
            normalized_value=f"{occ}_bank",
            reason=f"{occ.capitalize()} with income credited to bank account passes."
        )
        
    if is_salaried or is_self_employed:
        return EvalResult(
            Status.NEEDS_CLARIFICATION,
            reason="Occupation captured, but bank credit mode requires confirmation."
        )
        
    return EvalResult(Status.NEEDS_CLARIFICATION, reason="Clarify occupation and income receipt mode.")


def evaluate_property_value(text_or_val: str) -> EvalResult:
    """Criterion 6: Any positive estimate passes. No minimum threshold."""
    amt_lakh = parse_inr_amount_to_lakh(str(text_or_val))
    if amt_lakh is not None and amt_lakh > 0:
        return EvalResult(
            Status.PASS,
            normalized_value=f"₹{amt_lakh:.1f} lakh",
            reason=f"Estimated market value of ₹{amt_lakh:.1f} lakh accepted without threshold."
        )
        
    t = str(text_or_val).lower()
    if any(k in t for k in ["don't know", "dont know", "not sure", "refuse", "won't say", "no idea"]):
        return EvalResult(
            Status.NEEDS_CLARIFICATION,
            reason="Customer unsure or refusing property value; requires one targeted re-ask."
        )
        
    return EvalResult(Status.NEEDS_CLARIFICATION, reason="Clarify property market value estimate.")


def evaluate_tenure(text_or_val: str) -> EvalResult:
    """Criterion 7: 3 to 15 years inclusive pass. Outside 3-15 years fails."""
    years = parse_tenure_to_years(str(text_or_val))
    if years is None:
        return EvalResult(Status.NEEDS_CLARIFICATION, reason="Tenure unclear or missing.")
        
    if MIN_TENURE_YEARS <= years <= MAX_TENURE_YEARS:
        return EvalResult(
            Status.PASS,
            normalized_value=f"{years:.0f} years",
            reason=f"Tenure of {years:.0f} years is within the allowed {MIN_TENURE_YEARS}–{MAX_TENURE_YEARS} year range."
        )
    else:
        return EvalResult(
            Status.FAIL,
            normalized_value=f"{years:.0f} years",
            outcome_if_failed=Outcome.DISQUALIFIED_TENURE,
            reason=f"Tenure of {years:.0f} years is outside the permitted {MIN_TENURE_YEARS} to {MAX_TENURE_YEARS} year range."
        )


@dataclass
class QualificationState:
    """Maintains the 7 preliminary qualification data points."""
    property_type: Optional[EvalResult] = None
    ownership: Optional[EvalResult] = None
    original_documents: Optional[EvalResult] = None
    loan_amount: Optional[EvalResult] = None
    occupation_income: Optional[EvalResult] = None
    property_value: Optional[EvalResult] = None
    tenure: Optional[EvalResult] = None
    
    identity_verified: bool = False
    busy_callback_time: Optional[str] = None
    transfer_trigger_detected: bool = False
    transfer_reason: Optional[str] = None
    loan_cap_declined: bool = False

    def all_seven_passed(self) -> bool:
        slots = [
            self.property_type,
            self.ownership,
            self.original_documents,
            self.loan_amount,
            self.occupation_income,
            self.property_value,
            self.tenure,
        ]
        return all(s is not None and s.status == Status.PASS for s in slots)

    def get_first_failed_criterion(self) -> Optional[Tuple[str, EvalResult]]:
        slots = [
            ("property_type", self.property_type),
            ("ownership", self.ownership),
            ("original_documents", self.original_documents),
            ("loan_amount", self.loan_amount),
            ("occupation_income", self.occupation_income),
            ("property_value", self.property_value),
            ("tenure", self.tenure),
        ]
        for name, res in slots:
            if res is not None and res.status == Status.FAIL:
                return name, res
        return None

    def determine_call_outcome(self) -> Outcome:
        """Determines the final call outcome based on the state machine rules."""
        if not self.identity_verified:
            return Outcome.IDENTITY_NOT_VERIFIED
            
        if self.busy_callback_time:
            return Outcome.CALLBACK_REQUESTED
            
        if self.transfer_trigger_detected:
            return Outcome.TRANSFER_REFERRAL
            
        if self.loan_cap_declined:
            return Outcome.DECLINED_LOAN_CAP
            
        failed = self.get_first_failed_criterion()
        if failed:
            _, res = failed
            if res.outcome_if_failed:
                return res.outcome_if_failed
                
        if self.all_seven_passed():
            return Outcome.QUALIFIED_EXPERT_CALLBACK
            
        return Outcome.CALL_INCOMPLETE


def run_demo():
    """Runs a quick diagnostic self-test."""
    print("Running Home Credit LAP Business Rules Evaluator Self-Test...")
    state = QualificationState(identity_verified=True)
    state.property_type = evaluate_property_type("residential flat in my own name")
    state.ownership = evaluate_ownership("sole owner")
    state.original_documents = evaluate_documents("all originals are with me")
    state.loan_amount = evaluate_loan_amount("40 lakh")
    state.occupation_income = evaluate_occupation_and_income("salaried, salary credited to bank")
    state.property_value = evaluate_property_value("1.2 crore")
    state.tenure = evaluate_tenure("10 years")
    
    assert state.all_seven_passed() is True
    assert state.determine_call_outcome() == Outcome.QUALIFIED_EXPERT_CALLBACK
    print("Happy path qualification check: PASS ->", state.determine_call_outcome().value)

    # Check tenure boundaries
    assert evaluate_tenure("3 years").status == Status.PASS
    assert evaluate_tenure("15 years").status == Status.PASS
    assert evaluate_tenure("36 months").status == Status.PASS
    assert evaluate_tenure("20 years").status == Status.FAIL
    assert evaluate_tenure("2 years").status == Status.FAIL
    print("Tenure boundary checks (3y, 15y, 36m, 20y, 2y): PASS")

    # Check agricultural and industrial disqualification
    assert evaluate_property_type("agricultural land").status == Status.FAIL
    assert evaluate_property_type("industrial property").status == Status.FAIL
    assert evaluate_property_type("industrial warehouse").outcome_if_failed == Outcome.DISQUALIFIED_PROPERTY_TYPE
    print("Agricultural and industrial property disqualification: PASS")

    # Check cash income disqualification
    assert evaluate_occupation_and_income("all my income is in cash").status == Status.FAIL
    print("Cash income disqualification: PASS")

    # Check transfer trigger
    has_trigger, reason = check_transfer_trigger("I want to reduce my home loan EMI")
    assert has_trigger is True
    print("Transfer trigger check: PASS ->", reason)

    # Check unrelated loan (car loan)
    has_trigger, _ = check_transfer_trigger("I have a car loan with SBI")
    assert has_trigger is False
    print("Unrelated loan (car loan) non-transfer check: PASS")

    print("\nAll evaluator self-tests passed successfully!")


if __name__ == "__main__":
    run_demo()
