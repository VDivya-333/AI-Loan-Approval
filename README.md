# AI-Powered Loan Approval Workflow

An advanced, end-to-end automated loan processing system built with **Python**, **LangGraph**, and **Streamlit**. This system leverages a multi-agent architecture to verify documents, assess credit risk, generate offers, and manage human-in-the-loop (HITL) escalations.

## 🚀 Tech Stack

- **Orchestration:** [LangGraph](https://github.com/langchain-ai/langgraph) (Stateful Multi-Agent Workflows)
- **LLM Framework:** [LangChain](https://github.com/langchain-ai/langchain)
- **Frontend:** [Streamlit](https://streamlit.io/) (Real-time Dashboard)
- **Database:** 
    - **SQLite:** Relational storage for application metadata and history.
    - **ChromaDB:** Vector database for document embedding and similarity checks.
- **Scheduling:** [APScheduler](https://apscheduler.readthedocs.io/) (Background jobs for manager reminders)
- **Environment:** Python 3.10+

## 🏗️ System Architecture & Workflow

The system uses a directed acyclic graph (DAG) to manage the state of a loan application.

### 1. The Workflow Graph
The workflow is defined in `workflow.py` using `AppState`. Nodes represent discrete logic steps or Agentic actions:

1.  **Document Verification:** Initial check of application documents.
2.  **Credit Score Check:** Calculates/retrieves credit health.
3.  **Risk Assessment:** Logic-based routing:
    - **LOW_RISK:** Direct to Offer Generation.
    - **BORDERLINE:** Escalates to Manager Review.
    - **HIGH_RISK:** Requests additional evidence (Bank Statements/Salary Slips).
4.  **Evidence Review:** Specialized agent reviews user-uploaded PDFs stored in ChromaDB.
5.  **Offer Generation:** Calculates interest rates and tenure.
6.  **Disbursement:** Finalizes the transaction.

### 2. Intelligent Agents
- **Document Agent:** Validates text extraction from uploads.
- **Credit Agent:** Analyzes financial history.
- **Risk Agent:** Categorizes the application based on Income-to-Loan ratios.
- **Offer Agent:** Customizes terms based on credit score.
- **Evidence Review Agent:** Specifically triggered for high-risk cases to verify manual uploads.

## 📂 Project Structure

```text
├── agents/               # Individual Agent logic (Prompt templates & Tools)
├── chroma/               # Local Vector Store (ChromaDB)
├── db.py                 # SQLite CRUD operations & Schema migrations
├── workflow.py           # LangGraph definition and node logic
├── scheduler.py          # Background tasks for PENDING_MANAGER follow-ups
├── streamlit_app.py      # Main Dashboard UI
├── main.py               # CLI entry point for automated testing
├── utils.py              # Emailing (SMTP/Console) and helper functions
└── requirements.txt      # Project dependencies
```

## 🛠️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd AI_loan_approval
   ```

2. **Create a Virtual Environment:**
   ```bash
   python -m venv venv
   ./venv/Scripts/activate  # Windows
   source venv/bin/activate # Linux/Mac
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Create a `.env` file in the root directory:
   ```dotenv
   EMAIL_MODE=console # Set to 'smtp' for real emails
   EMAIL_USER=your_email@gmail.com
   EMAIL_PASS=your_app_password
   MANAGER_EMAIL=manager@example.com
   ```

5. **Initialize Database:**
   ```bash
   python seed_db.py
   ```

## 🎮 Usage

### Running the Dashboard
To launch the interactive UI:
```bash
python -m streamlit run streamlit_app.py
```

### Running CLI Demonstrations
The system includes two pre-configured simulation flows:

**Automated High-Risk Flow:**
```bash
python main.py automated
```
**Borderline Case (Manager Escalation):**
```bash
python main.py borderline
```

## 🔔 Automated Reminders
When an application enters the `PENDING_MANAGER` state, the `scheduler.py` initializes a background job. It sends daily email reminders to the configured manager email until the application status changes, ensuring no application is stalled.

