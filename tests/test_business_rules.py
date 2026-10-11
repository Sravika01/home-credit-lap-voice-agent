"""Automated unit tests for Home Credit LAP Voice Agent business rules.

Validates:
- All seven eligibility criteria logic and boundary conditions.
- Immediate disqualification behavior.
- Property loan transfer triggers vs non-transfer loans.
- Loan amount cap enforcement and crore-to-lakh conversions.
- Busy customer handling.
- Prevention of premature qualified close (qualification gate).
- Static integrity of system prompt and documentation mapping.
"""

from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import file as engine
from file import (
    EvalResult,
    Outcome,
    QualificationState,
    Status,
    check_transfer_trigger,
    evaluate_documents,
    evaluate_loan_amount,
    evaluate_occupation_and_income,
    evaluate_ownership,
    evaluate_property_type,
    evaluate_property_value,
    evaluate_tenure,
    parse_inr_amount_to_lakh,
    parse_tenure_to_years,
)


class TestEligibilityCriteria(unittest.TestCase):
    """Tests the seven preliminary eligibility criteria individually."""

    def test_criterion_1_property_type_pass(self):
        for text in [
            "residential flat in Mumbai",
            "I have an independent house",
            "commercial shop in Chandni Chowk",
            "an office space",
        ]:
            res = evaluate_property_type(text)
            self.assertEqual(res.status, Status.PASS, f"Failed for {text}")

    def test_criterion_1_property_type_disqualify(self):
        for text in [
            "agricultural land in my village",
            "farmland inherited from ancestors",
            "farm land",
            "industrial warehouse",
            "factory shed in MIDC",
            "industrial property",
        ]:
            res = evaluate_property_type(text)
            self.assertEqual(res.status, Status.FAIL, f"Should fail for {text}")
            self.assertEqual(res.outcome_if_failed, Outcome.DISQUALIFIED_PROPERTY_TYPE)

    def test_criterion_1_industrial_property_disqualification(self):
        for text in ["Industrial", "industrial", "industrial shed", "factory"]:
            res = evaluate_property_type(text)
            self.assertEqual(res.status, Status.FAIL, f"Should fail for {text}")
            self.assertEqual(res.outcome_if_failed, Outcome.DISQUALIFIED_PROPERTY_TYPE)

    def test_criterion_1_property_type_clarify(self):
        for text in ["It is a plot", "open land", "farmhouse"]:
            res = evaluate_property_type(text)
            self.assertEqual(res.status, Status.NEEDS_CLARIFICATION, f"Should clarify for {text}")

    def test_criterion_2_ownership_pass(self):
        self.assertEqual(evaluate_ownership("sole owner").status, Status.PASS)
        self.assertEqual(evaluate_ownership("in my own name").status, Status.PASS)
        self.assertEqual(evaluate_ownership("jointly owned with my brother").status, Status.PASS)
        self.assertEqual(evaluate_ownership("co-owner with my wife").status, Status.PASS)

    def test_criterion_2_ownership_disqualify(self):
        res = evaluate_ownership("The property is in my father's name only, not in my name")
        self.assertEqual(res.status, Status.FAIL)
        self.assertEqual(res.outcome_if_failed, Outcome.DISQUALIFIED_OWNERSHIP)

    def test_criterion_3_documents_pass(self):
        res = evaluate_documents("Yes, I have all the original documents with me")
        self.assertEqual(res.status, Status.PASS)
        self.assertEqual(res.normalized_value, "available")

    def test_criterion_3_documents_disqualify(self):
        for text in [
            "The originals were lost in a flood; I only have photocopies",
            "Original papers are missing",
            "Unavailable, only photocopies exist",
        ]:
            res = evaluate_documents(text)
            self.assertEqual(res.status, Status.FAIL, f"Should fail for {text}")
            self.assertEqual(res.outcome_if_failed, Outcome.DISQUALIFIED_DOCUMENTS)

    def test_criterion_3_documents_with_lender(self):
        res = evaluate_documents("The originals are with SBI because of my existing home loan")
        self.assertEqual(res.status, Status.TRANSFER_TRIGGER)
        self.assertEqual(res.outcome_if_failed, Outcome.TRANSFER_REFERRAL)

    def test_criterion_4_loan_amount_and_crore_conversion(self):
        self.assertAlmostEqual(parse_inr_amount_to_lakh("40 lakh"), 40.0)
        self.assertAlmostEqual(parse_inr_amount_to_lakh("75 lakhs"), 75.0)
        self.assertAlmostEqual(parse_inr_amount_to_lakh("1 crore"), 100.0)
        self.assertAlmostEqual(parse_inr_amount_to_lakh("1.2 crore"), 120.0)

        res_pass = evaluate_loan_amount("40 lakh")
        self.assertEqual(res_pass.status, Status.PASS)

        res_boundary = evaluate_loan_amount("75 lakh")
        self.assertEqual(res_boundary.status, Status.PASS)

        res_exceed = evaluate_loan_amount("1 crore")
        self.assertEqual(res_exceed.status, Status.NEEDS_CLARIFICATION)
        self.assertIn("exceeds", res_exceed.reason)

    def test_criterion_5_occupation_and_income_pass(self):
        for text in [
            "salaried, salary credited to bank",
            "I work at an IT firm and receive salary in HDFC bank account",
            "self-employed businessman, income through bank account",
            "I run a shop and all payments come through bank account",
        ]:
            res = evaluate_occupation_and_income(text)
            self.assertEqual(res.status, Status.PASS, f"Failed for {text}")

    def test_criterion_5_occupation_and_income_disqualify(self):
        for text in [
            "I run a small shop, all my income is in cash",
            "income is paid in cash",
            "I am currently unemployed",
            "I am a college student",
        ]:
            res = evaluate_occupation_and_income(text)
            self.assertEqual(res.status, Status.FAIL, f"Should fail for {text}")
            self.assertEqual(res.outcome_if_failed, Outcome.DISQUALIFIED_INCOME)

    def test_criterion_6_property_value_no_threshold(self):
        for val in ["15 lakh", "50 lakh", "1.2 crore", "5 crore"]:
            res = evaluate_property_value(val)
            self.assertEqual(res.status, Status.PASS, f"Failed for {val}")

    def test_criterion_7_tenure_boundaries(self):
        # 3 years (TC-10a)
        self.assertEqual(evaluate_tenure("3 years").status, Status.PASS)
        # 15 years (TC-10b)
        self.assertEqual(evaluate_tenure("15 years").status, Status.PASS)
        # 36 months = 3 years (TC-10c)
        self.assertEqual(parse_tenure_to_years("36 months"), 3.0)
        self.assertEqual(evaluate_tenure("36 months").status, Status.PASS)
        # Middle value
        self.assertEqual(evaluate_tenure("10 years").status, Status.PASS)

        # Disqualifying tenures (TC-09)
        res_20y = evaluate_tenure("20 years")
        self.assertEqual(res_20y.status, Status.FAIL)
        self.assertEqual(res_20y.outcome_if_failed, Outcome.DISQUALIFIED_TENURE)

        res_2y = evaluate_tenure("2 years")
        self.assertEqual(res_2y.status, Status.FAIL)
        self.assertEqual(res_2y.outcome_if_failed, Outcome.DISQUALIFIED_TENURE)


class TestTransferAndReferralTriggers(unittest.TestCase):
    """Tests balance transfer, refinancing, and specialist referral triggers."""

    def test_property_loan_transfer_triggers(self):
        phrases = [
            "Can I do a balance transfer for my home loan?",
            "I already have a home loan on this flat, can you take it over?",
            "I want to refinance my current property loan",
            "Can you reduce my home loan EMI?",
            "I already have a loan against property with ICICI",
            "The original papers are with SBI for an existing mortgage",
        ]
        for p in phrases:
            has_trigger, reason = check_transfer_trigger(p)
            self.assertTrue(has_trigger, f"Expected transfer trigger for: {p}")

    def test_unrelated_loans_do_not_trigger_transfer(self):
        unrelated = [
            "I have a car loan with HDFC",
            "I have an active personal loan",
            "I use credit cards",
        ]
        for p in unrelated:
            has_trigger, _ = check_transfer_trigger(p)
            self.assertFalse(has_trigger, f"Should NOT trigger transfer for: {p}")


class TestQualificationStateMachine(unittest.TestCase):
    """Tests the state machine, gating, and outcome determination."""

    def test_happy_path_qualified_close(self):
        state = QualificationState(identity_verified=True)
        state.property_type = evaluate_property_type("residential apartment")
        state.ownership = evaluate_ownership("sole owner")
        state.original_documents = evaluate_documents("all originals are available")
        state.loan_amount = evaluate_loan_amount("40 lakh")
        state.occupation_income = evaluate_occupation_and_income("salaried, bank credit")
        state.property_value = evaluate_property_value("1.2 crore")
        state.tenure = evaluate_tenure("10 years")

        self.assertTrue(state.all_seven_passed())
        self.assertEqual(state.determine_call_outcome(), Outcome.QUALIFIED_EXPERT_CALLBACK)

    def test_gate_blocks_premature_qualification(self):
        state = QualificationState(identity_verified=True)
        state.property_type = evaluate_property_type("residential apartment")
        state.ownership = evaluate_ownership("sole owner")
        state.original_documents = evaluate_documents("originals available")
        # 4 missing criteria
        self.assertFalse(state.all_seven_passed())
        self.assertNotEqual(state.determine_call_outcome(), Outcome.QUALIFIED_EXPERT_CALLBACK)

    def test_unverified_identity_outcome(self):
        state = QualificationState(identity_verified=False)
        self.assertEqual(state.determine_call_outcome(), Outcome.IDENTITY_NOT_VERIFIED)

    def test_busy_customer_outcome(self):
        state = QualificationState(identity_verified=True, busy_callback_time="tomorrow at 6 PM")
        self.assertEqual(state.determine_call_outcome(), Outcome.CALLBACK_REQUESTED)

    def test_immediate_disqualification_property_type(self):
        state = QualificationState(identity_verified=True)
        state.property_type = evaluate_property_type("agricultural land")
        self.assertEqual(state.determine_call_outcome(), Outcome.DISQUALIFIED_PROPERTY_TYPE)

        state_ind = QualificationState(identity_verified=True)
        state_ind.property_type = evaluate_property_type("Industrial")
        self.assertEqual(state_ind.determine_call_outcome(), Outcome.DISQUALIFIED_PROPERTY_TYPE)

    def test_immediate_disqualification_documents(self):
        state = QualificationState(identity_verified=True)
        state.property_type = evaluate_property_type("residential flat")
        state.original_documents = evaluate_documents("photocopies only, originals lost")
        self.assertEqual(state.determine_call_outcome(), Outcome.DISQUALIFIED_DOCUMENTS)

    def test_declined_loan_cap(self):
        state = QualificationState(identity_verified=True, loan_cap_declined=True)
        self.assertEqual(state.determine_call_outcome(), Outcome.DECLINED_LOAN_CAP)


class TestSystemPromptIntegrity(unittest.TestCase):
    """Performs static checks on the system prompt file."""

    def setUp(self):
        self.prompt_path = ROOT / "prompts" / "home_credit_lap_system_prompt.md"
        self.assertTrue(self.prompt_path.exists(), "Prompt file must exist")
        self.content = self.prompt_path.read_text(encoding="utf-8")
        m = re.search(r"<!-- BEGIN SYSTEM PROMPT -->(.*)<!-- END SYSTEM PROMPT -->", self.content, re.S)
        self.assertIsNotNone(m, "BEGIN/END SYSTEM PROMPT markers missing")
        self.body = m.group(1)

    def test_required_phrases_present(self):
        required = [
            "will call them back shortly with the exact interest rates",
            "referring them to the loan-transfer specialist",
            "seventy-five lakh",
            "From three to fifteen years, inclusive",
        ]
        for phrase in required:
            self.assertIn(phrase, self.body, f"Mandatory phrase missing: {phrase!r}")

    def test_forbidden_terms_absent(self):
        forbidden = [
            "{{conversation_history}}",
            "{{customer_utterance}}",
            "{{current_date}}",
            "{{current_day}}",
            "{{current_time}}",
            "transfer_to_",
            "qualified_handoff",
        ]
        for bad in forbidden:
            self.assertNotIn(bad, self.body, f"Forbidden token present: {bad!r}")

    def test_allowed_dynamic_variables_exact(self):
        expected_vars = {
            "company_name",
            "customer_name",
            "agent_name",
            "agent_gender",
            "language_to_speak",
            "additional_context_from_rag",
            "current_time_Asia/Kolkata",
            "current_calendar_Asia/Kolkata",
        }
        used_vars = set(re.findall(r"\{\{([\w/]+)\}\}", self.body))
        self.assertEqual(used_vars, expected_vars, "Prompt variable set mismatch")

    def test_end_call_instruction_present(self):
        self.assertIn("end_call", self.body)


if __name__ == "__main__":
    unittest.main()

