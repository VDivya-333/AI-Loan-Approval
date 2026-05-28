from typing import TypedDict, Annotated, List
import operator
import os
from dotenv import load_dotenv

from langchain_core.messages import BaseMessage

from langgraph.graph import StateGraph, END

from agents.document_agent import document_verification_agent
from agents.credit_agent import credit_score_agent 
from db import update_application_credit_score, update_application_status, save_document
from agents.risk_agent import risk_assessment_agent # manager_review_agent is not used directly as a node
from agents.offer_agent import offer_generation_agent
from agents.disbursement_agent import disbursement_agent
from agents.evidence_review_agent import evidence_review_agent
from utils import send_email

load_dotenv()

class AppState(TypedDict):
    """The state of our loan application workflow."""
    application: dict
    documents_ok: bool
    credit_score: int
    risk_level: str
    manager_decision: str
    offer: dict
    final_status: str
    notes: str

# --- Node Functions ---

def document_verification_node(state: AppState):
    print("--- Node: Document Verification ---")
    app = state["application"]
    doc_text = "This is a valid payslip document text."
    docs_ok, _ = document_verification_agent(app["id"], doc_text)
    note = "Initial document check passed." if docs_ok else "Initial document check failed."
    print(note)
    return {"documents_ok": docs_ok, "notes": note}

def credit_score_node(state: AppState):
    print("--- Node: Credit Score Check ---")
    app = state["application"]
    credit_score = credit_score_agent(app)
    note = f"Credit score checked: {credit_score}"
    print(note)
    update_application_credit_score(app["id"], credit_score)
    return {"credit_score": credit_score, "notes": note}

def risk_assessment_node(state: AppState):
    print("--- Node: Risk Assessment ---")
    app = state["application"]
    risk = risk_assessment_agent(app["income"], app["loan_amount"], state["credit_score"])
    note = f"Risk assessed as: {risk}"
    print(note)
    return {"risk_level": risk, "notes": note}

def manager_review_node(state: AppState):
    print("--- Node: Manager Review ---")
    # In a fully automated flow, we simulate the manager's approval.
    notes = "Application was borderline, automatically approved for offer generation."
    print("Manager automatically approved the application.")
    return {"manager_decision": "approve", "notes": notes}

def offer_generation_node(state: AppState):
    print("--- Node: Offer Generation ---")
    app = state["application"]
    # Add credit score to app dict for the agent
    app_with_score = {**app, "credit_score": state["credit_score"]}
    offer_details = offer_generation_agent(app_with_score)
    note = f"Loan offer generated: Amount ${offer_details.get('loan_amount', 'N/A')}, Rate {offer_details.get('interest_rate', 'N/A')}%, Tenure {offer_details.get('tenure_months', 'N/A')} months."
    print(note)
    return {"offer": offer_details, "notes": note}

def disbursement_node(state: AppState):
    print("--- Node: Disbursement ---")
    msg = disbursement_agent(state["application"]["name"])
    print(msg)
    # The agent already returns a human-friendly message
    return {"notes": msg} 

def approved_node(state: AppState):
    print("--- Node: Approved ---")
    notes = "Application approved and loan disbursed."
    print(f"Final Status: APPROVED. Notes: {notes}")
    update_application_status(state["application"]["id"], "APPROVED", notes)
    return {"final_status": "APPROVED", "notes": notes}

def rejected_node(state: AppState):
    print("--- Node: Rejected ---")
    notes = state.get("notes", "Rejected via automated workflow.")
    print(f"Final Status: REJECTED. Notes: {notes}")
    update_application_status(state["application"]["id"], "REJECTED", notes)
    return {"final_status": "REJECTED", "notes": f"Application rejected. {notes}"}

def request_additional_info_node(state: AppState):
    print("--- Node: Request Additional Info ---")
    app = state["application"]
    notes = "High risk detected. Please provide additional evidence (e.g., bank statements)."
    update_application_status(app["id"], "PENDING_INFO", notes)

    # Automatically email the candidate to request more info
    send_email(
        to=app["email"],
        subject=f"Action Required: Additional Documents for Loan Application #{app['id']}",
        body=f"""Dear {app['name']},

Thank you for your loan application. To proceed with the evaluation, we require some additional documentation due to the risk profile assessed.

Please provide your last 3 months of bank statements and salary slips.

Sincerely,
The Loan-Bot Team"""
    )
    return {"notes": notes, "final_status": "PENDING_INFO"}

def evidence_review_node(state: AppState):
    """
    A new node that is triggered after a user uploads documents.
    It uses an agent to verify if the documents are sufficient.
    """
    print("--- Node: Evidence Review ---")
    app_id = state["application"]["id"]
    ok, msg = evidence_review_agent(app_id)
    
    status_notes = f"Review of submitted documents: {msg}" # Initialize with the message from the agent

    if ok:
        # Update status to show it's ready for manager review
        status_notes = "Additional documents verified. Ready for manager review."
        # The status will be set to PENDING_MANAGER in the next node.

        # Automatically notify the manager
        app = state["application"]
        manager_email = os.getenv("MANAGER_EMAIL", "manager@example.com")

        send_email( # This could be moved to the manager_review_node if preferred
            to=manager_email,
            subject=f"Action Required: Review Submitted Documents for Loan Application #{app['id']}",
            body=f"""Dear Manager,

The applicant {app['name']} has submitted the additional documents requested for loan application #{app['id']}.

Please review the application and the new evidence to make a decision.
"""
        )

    return {"documents_ok": ok, "notes": status_notes}

def simulate_document_submission_node(state: AppState):
    """
    A new node to simulate the user uploading documents.
    This makes the workflow fully automatic.
    """
    print("--- Node: Simulating Document Submission ---")
    app_id = state["application"]["id"]
    # Simulate saving a dummy PDF document for the application
    save_document(app_id, f"simulated_bank_statement_{app_id}.pdf", b"%PDF-...")
    print(f"Simulated document submission for application #{app_id}.")
    note = f"Simulated document submission for application #{app_id}."
    return {"notes": note}

# --- Conditional Edges ---

def should_proceed_after_docs(state: AppState):
    if state["documents_ok"]:
        return "continue"
    return "fail"

def route_by_risk(state: AppState):
    return state["risk_level"]

def route_by_manager_decision(state: AppState):
    return "approve" 

# --- Build the Graph ---

def get_workflow_graph():
    workflow = StateGraph(AppState)

    # Add nodes
    workflow.add_node("document_verification", document_verification_node)
    workflow.add_node("credit_score", credit_score_node) # New node
    workflow.add_node("risk_assessment", risk_assessment_node) # New node
    workflow.add_node("manager_review", manager_review_node)
    workflow.add_node("offer_generation", offer_generation_node)
    workflow.add_node("disbursement", disbursement_node)
    workflow.add_node("approve_final", approved_node)
    workflow.add_node("request_additional_info", request_additional_info_node)
    workflow.add_node("reject_final", rejected_node)
    workflow.add_node("evidence_review", evidence_review_node)
    workflow.add_node("simulate_document_submission", simulate_document_submission_node)

    # Define edges
    workflow.set_entry_point("document_verification")

    workflow.add_conditional_edges(
        "document_verification",
        should_proceed_after_docs,
        {"continue": "credit_score", "fail": "reject_final"}
    )
    workflow.add_edge("credit_score", "risk_assessment")

    workflow.add_conditional_edges(
        "risk_assessment",
        route_by_risk,
        {
            "HIGH_RISK": "request_additional_info",
            "BORDERLINE": "manager_review",
            "LOW_RISK": "offer_generation"
        }
    )

    # For high-risk, request info, then simulate submission, then review evidence.
    workflow.add_edge("request_additional_info", "simulate_document_submission")
    workflow.add_edge("simulate_document_submission", "evidence_review")

    workflow.add_conditional_edges(
        "evidence_review",
        should_proceed_after_docs,
        # If evidence is ok, go to manager review. If not, loop back to request info again.
        {"continue": "manager_review", "fail": "reject_final"} # Fail and reject if docs are bad
    )

    # After manager review, route to approval (or rejection, though we've hardcoded approval)
    workflow.add_conditional_edges(
        "manager_review",
        route_by_manager_decision,
        {"approve": "offer_generation", "reject": "reject_final"}
    )

    workflow.add_edge("offer_generation", "disbursement")
    workflow.add_edge("disbursement", "approve_final")

    # Terminal nodes
    workflow.add_edge("approve_final", END)
    workflow.add_edge("reject_final", END)
    return workflow.compile()

def run_workflow(app: dict) -> iter:
    """
    Compiles and runs the loan approval workflow graph for a given application.
    This function is a generator that yields human-readable log messages.
    """
    yield "-> Starting workflow..."
    yield "[Start Workflow]"
    workflow = get_workflow_graph()

    start_node = "evidence_review" if app.get("status") == "PENDING_INFO" else None # Default entry point is used if None

    # Initial state for the graph, starting from a specific node if needed
    initial_state = {"application": app, "notes": ""}

    # stream_mode="updates" yields the node name and its output for each step
    for update in workflow.stream(initial_state, {"recursion_limit": 25}, stream_mode="updates", from_nodes=start_node):
        if not update:
            continue
        yield "     |"
        # The output is a dictionary with one key: the name of the node that just ran
        node_name = list(update.keys())[0]
        node_output = list(update.values())[0]
        note = node_output.get("notes", "No details provided.")
        yield f"     +--> [{node_name.replace('_', ' ').title()}]"
        yield f"          - {note}"

    yield "[Workflow Finished]"