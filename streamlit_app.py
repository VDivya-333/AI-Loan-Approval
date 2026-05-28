import streamlit as st
from db import init_db, save_application, list_applications, get_application, update_application_status, save_document, delete_application, update_application_history, clear_application_history
from workflow import run_workflow

st.set_page_config(page_title="Loan Workflow", layout="wide")
init_db()

st.title("Loan Approval Workflow — Dashboard")

with st.sidebar:
    st.header("New Application")
    name = st.text_input("Applicant name")
    email = st.text_input("Personal Email")
    income = st.number_input("Monthly income", min_value=0, step=1000)
    loan_amount = st.number_input("Loan amount", min_value=0, step=1000)
    if st.button("Submit Application"):
        if not name or not email or not "@" in email or loan_amount <= 0:
            st.warning("Please enter name, email, and a valid loan amount.")
        else:
            app_id = save_application(name, int(income), int(loan_amount), email)
            
            history_log = []
            app_data = get_application(app_id)
            for log_entry in run_workflow(dict(app_data)):
                history_log.append(log_entry)
            update_application_history(app_id, "\n".join(history_log))

            st.success(f"Application #{app_id} submitted and processing started.")
            st.rerun()

st.header("Applications")
apps = list_applications()
if not apps:
    st.info("No applications found.")
else:
    for app in apps:
        with st.expander(f"#{app['id']} — {app['name']} — {app['status']}"):
            st.write(f"**Applicant:** {app['name']} ({app.get('email')})")
            st.write(f"**Income:** {app['income']}  |  **Loan:** {app['loan_amount']}")
            st.write(f"Credit Score: {app.get('credit_score')}")
            st.write("Notes:", app.get("notes") or "-")

            if st.button("Show Workflow Log", key=f"log_{app['id']}"):
                st.subheader("Workflow Log")
                log_content = app.get("history", "No workflow log found.")
                st.text_area("Log", log_content, height=300, key=f"log_area_{app['id']}")

            # New button to clear only the workflow log
            if st.button("Clear Workflow Log", key=f"clear_log_{app['id']}", help="Deletes only the workflow log for this application, not the application itself."):
                clear_application_history(app['id'])
                st.success(f"Workflow log for application #{app['id']} cleared.")
                st.rerun()

            if app['status'] == 'PENDING_INFO':
                st.warning(f"This application is considered high-risk. An email has been sent to {app.get('email')} requesting additional documents.")
                
                st.subheader("Upload Required Documents Here")
                uploaded_files = st.file_uploader(
                    "Upload PDFs (e.g., bank statements, salary slips)",
                    type=["pdf"],
                    accept_multiple_files=True,
                    key=f"uploader_{app['id']}"
                )
                if st.button("Submit Documents", key=f"submit_docs_{app['id']}"):
                    if uploaded_files:
                        for f in uploaded_files:
                            save_document(app["id"], f.name, f.read())
                        
                        st.info("Documents uploaded. Resuming workflow...")
                        history_log = (app.get("history", "") or "").splitlines()
                        app_data = get_application(app["id"])
                        for log_entry in run_workflow(dict(app_data)):
                            history_log.append(log_entry)
                        update_application_history(app["id"], "\n".join(history_log))

                        update_application_status(app["id"], "APPROVED", "Documents reviewed and automatically approved by manager.")

                        st.success(f"Documents for application #{app['id']} submitted and approved!")
                        st.rerun()

            cols = st.columns(4)
            if cols[0].button("Approve (manual)", key=f"approve_{app['id']}"):
                update_application_status(app['id'], "APPROVED", notes="Manually approved")
                st.success("Marked APPROVED")
                st.rerun()
            if cols[1].button("Reject (manual)", key=f"reject_{app['id']}"):
                update_application_status(app['id'], "REJECTED", notes="Manually rejected")
                st.success("Marked REJECTED")
                st.rerun()
            if cols[2].button("Delete Application", key=f"delete_{app['id']}", help="Deletes the entire application record and its associated documents."): # Changed label and removed type="primary"
                delete_application(app['id'])
                st.success(f"Application #{app['id']} deleted.")
                st.rerun()
            if cols[3].button("Refresh", key=f"refresh_{app['id']}"):
                st.rerun()
