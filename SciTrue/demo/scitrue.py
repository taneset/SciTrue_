import sys
import os
import time
import json
import requests
import asyncio
import pandas as pd
from datetime import datetime
from flask import Flask, url_for
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import streamlit as st
import torch
torch.classes.__path__ = []

# Append root directory for module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Local imports
from prompt_makers.claim_extract_prompt import make_claim_extraction_query
from prompt_makers.report_with_link_prompt import make_report_query
from generations.parsing_and_saving_functions import (
    clean_and_convert,
    add_evidence_to_claims,
    update_list_with_journal_and_venue,
)
from calls.one_generation import get_one_completion
from html_functions import (
    render_title,
    render_custom_styles,
    build_html_tree,
    generate_html_code,
    render_accuracy_score,
    render_reason_for_accuracy,
    badge_label,
    badge_fields,
    label_colors
)
from calls.sjr import get_journal_info_dict

# ====== FILE/DIR PATHS =====
base_dir = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.join(base_dir, '..', 'data')
USERS_JSON_PATH = os.path.join(DATA_ROOT, "users.json")
USER_ACTIVITY_PATH = os.path.join(DATA_ROOT, "user_activity.json")
OUTPUTS_DIRS = [
    "outputs/report",
    "outputs/evidence"
]
for d in OUTPUTS_DIRS:
    d = os.path.join(base_dir, '..', d)
    os.makedirs(d, exist_ok=True)
os.makedirs(DATA_ROOT, exist_ok=True)

DATAFRAME_OUTPUT_PATH = os.path.join(base_dir, '..', "outputs/evidence/dataframe_stage_1.parquet")

def save_json(data, file_path):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def load_json(file_path, default=None):
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}

# Flask email verification setup
flask_app = Flask(__name__)
flask_app.config.update(
    SECRET_KEY="YOUR_RANDOM_SECRET_KEY",
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
)
mail = Mail(flask_app)
serializer = URLSafeTimedSerializer(flask_app.config["SECRET_KEY"])

# ----------------- USER MANAGEMENT -----------------

def load_users():
    return load_json(USERS_JSON_PATH, default={})

def save_users(users):
    save_json(users, USERS_JSON_PATH)

@flask_app.route("/send_confirmation/<email>")
def send_confirmation(email):
    try:
        token = serializer.dumps(email, salt="email-confirm")
        link = url_for("confirm_email", token=token, _external=True)
        mail.send(Message("Verify Email", sender=flask_app.config["MAIL_USERNAME"], recipients=[email], body=f"Verify: {link}"))
        return "Email sent!"
    except Exception as e:
        print(f"Error sending email: {e}")
        return f"Error sending email: {e}"

@flask_app.route("/confirm_email/<token>")
def confirm_email(token):
    try:
        email = serializer.loads(token, salt="email-confirm", max_age=3600)
        users = load_users()
        users[email] = {"is_verified": True}
        save_users(users)
        return "Verified! Set a password now."
    except Exception:
        return "Invalid or expired link!"

def start_flask():
    flask_app.run(host="0.0.0.0", port=5002, use_reloader=False)

# ----------------- STREAMLIT UI -----------------

def render_custom_styles(st):
    st.markdown("""
        <style>
        @media (max-width: 600px) {
            .stButton button {
                width: 100% !important;
                margin-top: 10px !important;
            }
        }
        .main-title {
            text-align: center;
            margin-bottom: 1rem;
        }
        textarea {
            border: 1px solid #999 !important;
            border-radius: 6px !important;
            padding: 8px !important;
            background-color: #f8f9fa !important;
        }
        div[data-baseweb="select"] > div {
            border: 1px solid #999 !important;
            border-radius: 6px !important;
            background-color: #f8f9fa !important;
        }
        </style>
    """, unsafe_allow_html=True)

def welcome_page():
    render_title(st)
    render_custom_styles(st)
    st.markdown("""
                🚀 **Welcome to SciTrue** – your agentic AI science assistant.

                ---

                🧠 **SciTrue** can help:
                - ✅ Explain and reason scientific claims.
                - 🛡️ Fight misinformation using trustworthy sources.
                - 🌍 Make science accessible to everyone.
                - ✨ Empowering scientific discovery.

                ---

                🔓 **Get started by logging in  below:**
                """)
    st.markdown("###")
    query_params = st.query_params
    access = query_params.get("access", None)
    if access == "EMNLP2025DEMO":
        if st.button("🔐 EMNLP 2025 Login"):
            st.session_state["page"] = "emnlp_login"
            st.rerun()
    else:
        if st.button("🔐 User Login"):
            st.session_state["page"] = "login"
            st.rerun()
    #     if st.button("✉️ Register with Email"):
    #         st.session_state["page"] = "verify"
    #         st.rerun()
    # st.markdown("---")
    # st.info("New here? Tap **Register** to verify your email. Already signed up? Just **Login**.")

def email_login():
    st.header("Email Verification")
    email = st.text_input("Email", key="verify_email_input")
    if st.button("Send Verification"):
        requests.get(f"https://scitrue.streamlit.app/send_confirmation/{email}")
        st.session_state["user_email"] = email
        st.success("Email sent! Check your inbox.")
    if st.button("Check Verification"):
        users = load_users()
        if users.get(email, {}).get("is_verified"):
            st.session_state["verified"] = True
            st.session_state["page"] = "set_password"
            st.rerun()
        else:
            st.warning("Not verified yet.")

def set_password():
    st.header("Set Password")
    pw1 = st.text_input("Password", type="password")
    pw2 = st.text_input("Confirm Password", type="password")
    if st.button("Save Password"):
        if pw1 and pw1 == pw2:
            email = st.session_state["user_email"]
            users = load_users()
            users[email]["password"] = pw1
            save_users(users)
            st.success("Password set successfully!")
            st.session_state["page"] = "login"
            st.rerun()
        else:
            st.error("Passwords do not match or are empty!")


def emnlp_login():
    st.session_state["logged_in_user"] = "emnlp"
    st.session_state["page"] = "main"
    st.rerun()

def user_login():
    st.header("Login")
    email = st.text_input("Email", key="login_email_input")
    pw = st.text_input("Password", type="password")
    cols = st.columns(8)

    with cols[0]:
        login_clicked = st.button("Login")
    with cols[1]:
        back_clicked = st.button("Back")

    if login_clicked:
        users = load_users()
        if users.get(email, {}).get("password") == pw:
            st.session_state["logged_in_user"] = email
            st.session_state["page"] = "main"
            st.rerun()
        else:
            st.error("Invalid credentials")

    if back_clicked:
        st.session_state["page"] = "welcome"
        st.rerun()

# ----------------- MAIN FUNCTIONALITY -----------------

def log_activity(entry):
    logs = load_json(USER_ACTIVITY_PATH, default=[])
    logs.append(entry)
    save_json(logs, USER_ACTIVITY_PATH)

def get_activity_history(email):
    logs = load_json(USER_ACTIVITY_PATH, default=[])
    user_logs = [log for log in logs if log.get("email") == email]
    return user_logs

def show_history(email):
    st.header("📜 Claim History")
    if st.button("Back to Search"):
        st.session_state["page"] = "main"
        st.rerun()
    history = get_activity_history(email)
    if not history:
        st.info("No history found!")
        return
    for idx, entry in enumerate(reversed(history)):
        with st.expander(f"{entry.get('claim', 'No claim')} ({entry.get('timestamp', '')})"):
            st.markdown(f"### Claim")
            st.write(entry.get("claim"))
            st.markdown(f"### Summary")
            st.markdown(entry.get("summary"), unsafe_allow_html=True)
            if "subclaims" in entry:
                st.markdown("### Subclaims")
                for sub in entry["subclaims"]:
                    st.write("•", sub.get("claim", ""))
            if st.button(f"See full page for this", key=f"details_{idx}"):
                st.session_state["history_details"] = entry
                st.session_state["page"] = "history_details"
                st.rerun()
        

def show_history_details():
    entry = st.session_state.get("history_details")
    if entry:
        if st.button("Back to history"):
            st.session_state["page"] = "history"
            st.rerun()
        st.header("📑 Past Claim Details")
        st.markdown(badge_label("Claim", bg=label_colors["Claim"]) +
            f'<span style="font-size:17px;font-weight:600;vertical-align:middle;margin-left:8px;">{entry["claim"]}</span>',
            unsafe_allow_html=True
        )
        st.markdown(
            badge_label("Articles", bg=label_colors["Articles"]) +
            f'<span style="font-size:17px;font-weight:600;vertical-align:middle;margin-left:8px;">{entry["articles"]}</span>',
            unsafe_allow_html=True
        )
        st.markdown(
            badge_label("Summary", bg=label_colors["Summary"]) +
            f'<span style="font-size:17px;font-weight:600;vertical-align:middle;margin-left:8px;">{entry["summary"]}</span>',
            unsafe_allow_html=True
        )
        st.markdown(
            badge_label("Overall Accuracy", bg=label_colors["Overall Accuracy"]) +
            f'<span style="font-size:17px;font-weight:600;vertical-align:middle;margin-left:8px;">{entry["overall accuracy"]}</span>',
            unsafe_allow_html=True
        )
        st.markdown(
            badge_label("Verdict and Reason", bg=label_colors["Verdict and Reason"]) +
            f'<span style="font-size:17px;font-weight:600;vertical-align:middle;margin-left:8px;">{entry["overall reason for accuracy"]}</span>',
            unsafe_allow_html=True
        )
        for idx, subclaim in enumerate(entry.get("subclaims", [])):
            st.markdown(
                badge_label(f"Subclaim {idx+1}", bg="#ffa000") +
                f'<span style="font-size:18px;font-weight:600;vertical-align:middle;margin-left:8px;">{subclaim["claim"]}</span>',
                unsafe_allow_html=True
            )
            for field in [
                ("Accuracy", "accuracy"),
                ("Verdict and Reason", "reason for accuracy"),
                ("Contribution", "contribution"),
                ("Title", "title"),
                ("Authors", "authors"),
                ("Year", "year"),
                ("Venue", "venue"),
                ("Relevance", "relevance"),
                ("Relevant Sentence", "relevant sentence"),
                ("Type", "type"),
                ("Label", "label"),
                ("Journal Title", "journal_title"),
                ("Paragraph", "paragraph"),
                ("Relevant Sentence Type","relevant sentence type"),
                ("Type Reason", "function_reason"),
                ("Relation", "relation"),
                ("Relation Reason", "relation_reason"),

            ]:
                label, key = field
                value = subclaim.get(key, 'N/A')
                if value:  # show only if present
                    if key == "paragraph":
                        parts = value.split('\n\n')
                        value = ''.join(
                            f'<div style="font-size:17px;font-weight:600;vertical-align:middle;margin-left:8px;">{part.strip()}</div>' for part in parts
                        )
                if value:
                    st.markdown(
                        badge_label(label, label_colors.get(label, "#757575")) +
                        f'<span style="font-size:17px;font-weight:600;vertical-align:middle;margin-left:8px;">{value}</span>',
                        unsafe_allow_html=True
                    )
            for assumption in subclaim.get("supporting assumptions", []):
                st.markdown(
                    badge_label("Supporting Assumption", bg=label_colors["Supporting"]) +
                     f'<span style="font-size:17px;font-weight:600;margin-left:8px;">{assumption}</span>',
                    unsafe_allow_html=True
                )
            for assumption in subclaim.get("refuting assumptions", []):
                st.markdown(
                    badge_label("Refuting Assumption", bg=label_colors["Refuting"]) +
                    f'<span style="font-size:17px;font-weight:600;margin-left:8px;">{assumption}</span>',
                    unsafe_allow_html=True
                )
            if "sjr" in subclaim:
                sjr_info = subclaim.get("sjr", {})
                st.markdown(badge_label("SJR Details", bg="#424242"), unsafe_allow_html=True)
                if isinstance(sjr_info, dict):
                    for key, value in sjr_info.items():
                        st.markdown(
                            badge_label(str(key), bg='#616161') +
                             f'<span style="font-size:16px; font-weight:600; margin-left:8px;">{value}</span>',
                            unsafe_allow_html=True
                        )
                else:
                     st.markdown(f"<span style='font-weight:600;'>{sjr_info}</span>", unsafe_allow_html=True)
            st.markdown("---")
        if st.button("Back to Search"):
            st.session_state["page"] = "main"
            st.rerun()
    else:
        st.warning("No details to show")
        st.session_state["page"] = "history"
        st.rerun()

def find_cached_summary(claim, articles):
    logs = load_json(USER_ACTIVITY_PATH, default=[])
    for log in logs:
        if (
            log.get("claim", "").strip().lower() == claim.strip().lower()
            and int(log.get("articles", 0)) == int(articles)
        ):
            return log
    return None




def run_app(username, email):
    with st.sidebar:
        st.markdown(f"👤 **Email:** `{email}`")
        if st.button("🕓 History"):
            st.session_state["page"] = "history"
            st.rerun()
        if st.button("🚪 Logout"):
            st.session_state.clear()
            st.session_state["page"] = "welcome"
            st.rerun()
    render_title(st)
    render_custom_styles(st)
    st.write("""
    🔍 ***SciTrue*** is an AI-powered tool that generates summaries as explanations of claims based on scientific papers.
    You can explore the context and assumptions behind each piece of evidence in the summary.
    Simply enter a claim along with the number of articles you'd like to consider.
    """)

    with st.form("summary_form"):
        claim = st.text_input('Enter a scientific claim:', max_chars=135).strip()
        k_str = st.text_input('Enter a number of articles to be considered:').strip()
        submitted = st.form_submit_button("Generate Summary")

    input_valid = False
    if claim and k_str:
        try:
            k = int(k_str)
            if k <= 0 or k > 15:
                st.error('Please enter a number between 1-15.')
            else:
                input_valid = True
                st.success(f'The process usually takes between  {3 * k} and  {5 * k + 8} seconds for {k} papers.')
        except ValueError:
            st.error('Please enter a valid number.')
    if submitted:
        if not claim:
            st.error('Please enter a claim.')
        if not k_str:
            st.error('Please enter a number.')
        if claim and k_str and input_valid:
            k = int(k_str)
            cached_entry = find_cached_summary(claim, k)
            if cached_entry:
                st.success("✅ Retrieved from global cache/history for this claim and number of articles!")
                st.subheader("Summary:")
                st.markdown(cached_entry['summary'], unsafe_allow_html=True)
                st.markdown(badge_label("Overall Accuracy", bg=label_colors["Overall Accuracy"]) +
                            f'<span style="font-size:17px;font-weight:600;vertical-align:middle;margin-left:8px;">{cached_entry["overall accuracy"]}</span>',
                            unsafe_allow_html=True
                        )
                st.markdown(badge_label("Verdict and Reason", bg=label_colors["Verdict and Reason"]) +
                             f'<span style="font-size:17px;font-weight:600;vertical-align:middle;margin-left:8px;">{cached_entry["overall reason for accuracy"]}</span>',
                            unsafe_allow_html=True
                        )
                if 'subclaims' in cached_entry:
                    st.markdown("### Subclaims")
                    for idx, sub in enumerate(cached_entry['subclaims']):
                        st.markdown(
                           badge_label(f"Subclaim {idx+1}", bg="#ffa000") +
                           f'<span style="font-size:18px;font-weight:600;vertical-align:middle;">{sub.get("claim","")}</span>',
                           unsafe_allow_html=True
                        )
                        for field in badge_fields:
                            sub_key = field.lower().replace(" ", "_")
                            value = sub.get(sub_key, "")
                            if value:
                                st.markdown(
                                    badge_label(field, bg=label_colors.get(field, "#757575")) +
                                     f'<span style="font-size:17px; font-weight:600; vertical-align:middle; margin-left:8px;">{value}</span>',
                                    unsafe_allow_html=True,
                                )
                        for assumption in sub.get("supporting assumptions", []):
                            st.markdown(
                                badge_label("Supporting Assumptions", bg="#1de9b6") +
                                f'<span style="font-size:17px; font-weight:600; margin-left:8px;">{assumption}</span>',
                                unsafe_allow_html=True
                            )
                        for assumption in sub.get("refuting assumptions", []):
                            st.markdown(
                                badge_label("Refuting Assumptions", bg="#d32f2f") +
                                f'<span style="font-size:17px; font-weight:600; margin-left:8px;">{assumption}</span>',
                                unsafe_allow_html=True
                            )
                        if "sjr" in sub:
                            sjr_info = sub.get("sjr", {})
                            st.markdown(badge_label("SJR Details", bg="#424242"), unsafe_allow_html=True)
                            if isinstance(sjr_info, dict):
                                for key, value in sjr_info.items():
                                    st.markdown(
                                        badge_label(key, bg='#616161') +
                                         f'<span style="font-size:16px; font-weight:600; margin-left:8px;">{value}</span>',
                                        unsafe_allow_html=True
                                    )
                            else:
                                 st.markdown(f"<span style='font-weight:600;'>{sjr_info}</span>", unsafe_allow_html=True)
                return   # DO NOT RUN GENERATION if cache hit!
            start_time = time.time()
            progress_bar = st.progress(0)
            progress_bar.progress(20)
            prompt, result, hint = make_report_query(claim, k)
            cleaned_data = None
            if result is True:
                if hint:
                    st.warning(hint)
                completion = asyncio.run(get_one_completion(prompt))
                progress_bar.progress(50)
                cleaned_data = clean_and_convert(completion)
                progress_bar.progress(80)
            if result is True and cleaned_data:
                st.subheader("Summary:")
                st.markdown(cleaned_data['executive summary'], unsafe_allow_html=True)
                summary_end_time = time.time()
                elapsed_time = summary_end_time - start_time
                st.success(f"Summary generated successfully in {elapsed_time:.2f} seconds!")
                accuracy_html = render_accuracy_score(cleaned_data["accuracy"])
                reason_html = render_reason_for_accuracy(
                    cleaned_data["reason for accuracy"],
                    accuracy_html.split('border: 2px solid ')[1].split(';')[0]
                )
                # st.markdown(accuracy_html, unsafe_allow_html=True)
                st.markdown(reason_html, unsafe_allow_html=True)
                df = pd.read_parquet(DATAFRAME_OUTPUT_PATH)
                sub_claims = make_claim_extraction_query(cleaned_data["executive summary"], claim)
                completion = asyncio.run(get_one_completion(sub_claims))
                completion = completion.replace('```json', '').replace('```', '').strip().replace("\n", "").replace("Empty string", "").strip()
                try:
                    clean_ext_sub_claims = json.loads(completion)
                except json.JSONDecodeError as e:
                    st.error(f"JSON decoding error: {e}")
                    st.write("Raw JSON output:")
                    st.write(completion)
                    clean_ext_sub_claims = []
                output = add_evidence_to_claims(cleaned_data, clean_ext_sub_claims)
                extended_output = update_list_with_journal_and_venue(df, output)
                for item in extended_output:
                    journal_name = item.get('journal_title', '').strip()
                    venue_name = item.get('venue', '').strip()
                    if journal_name and '&' in journal_name or venue_name and '&' in venue_name:
                        if journal_name:
                            journal_name = journal_name.replace('&', 'and').strip()
                        if venue_name:
                            venue_name = venue_name.replace('&', 'and').strip()
                    if journal_name or venue_name:
                        if not journal_name:
                            journal_name = venue_name
                        elif not venue_name:
                            venue_name = journal_name
                        try:
                            journal_info = get_journal_info_dict(journal_name)
                            if isinstance(journal_info, dict):
                                sjr_value = journal_info['SJR']
                                sjr_country = journal_info["Country"]
                                sjr_h_index = journal_info["H index"]
                                sjr_help = "https://www.scimagojr.com/help.php"

                                item['sjr'] = {
                                    "SCImago Journal Rank": sjr_value,
                                    "Country": sjr_country,
                                    "Journal  H index": sjr_h_index,
                                    "Metric Definitions": sjr_help
                                }

                            

                        
                            else:
                                print(f"[WARN] No SJR info found for journal: '{journal_name}'")
                        except Exception as e:
                            print(f"[ERROR] Failed to fetch SJR info for '{journal_name}': {e}")
                html_tree = build_html_tree(extended_output)
                html_code = generate_html_code(html_tree)
                st.components.v1.html(html_code, height=0, scrolling=True)
                final_end_time = time.time()
                elapsed_time = final_end_time - start_time
                st.success(f"The process has been completed successfully in {elapsed_time:.2f} seconds!")
                st.write("""⚠️ **Warning**  
This is an **agentic AI system**—it operates autonomously and may occasionally generate incomplete or incorrect information.
""")
                progress_bar.progress(100)
                log_entry = {
                    "user": username,
                    "email": email,
                    "claim": claim,
                    "articles": k,
                    "summary": cleaned_data['executive summary'],
                    "overall accuracy": cleaned_data.get("accuracy", ""),
                    "overall reason for accuracy": cleaned_data.get("reason for accuracy", ""),
                    "subclaims": clean_ext_sub_claims,
                    "timestamp": str(datetime.now())
                }
                log_activity(log_entry)
            else:
                progress_bar.empty()
                if hint:
                    st.warning(hint)
                else:
                    st.warning("❗ Hmm... That doesn't seem to be a clear scientific claim. Please rephrase and try again. If the problem continues, try again later.")

# ----------------- STREAMLIT ENTRY -----------------

def main():
    st.set_page_config(
        page_title="SciTrue - Your Scientific Claims Assistant",
        page_icon="📚",
        layout="centered"
    )
    if "page" not in st.session_state:
        st.session_state["page"] = "welcome"
    page = st.session_state["page"]
    if page == "welcome":
        welcome_page()
    elif page == "login":
        user_login()
    elif page == "emnlp_login":
        emnlp_login()
    elif page == "verify":
        email_login()
    elif page == "set_password":
        set_password()
    elif page == "main":
        email = st.session_state.get("logged_in_user", "unknown@example.com")
        run_app(username=email, email=email)
    elif page == "history":
        email = st.session_state.get("logged_in_user", "unknown@example.com")
        show_history(email)
    elif page == "history_details":
        show_history_details()

from threading import Thread

if __name__ == "__main__":
    OPENAI_API_KEY = os.getenv("OPEN_API_KEY")
    S2_API_KEY = os.getenv("S2_API_KEY")

    if not OPENAI_API_KEY:
        raise EnvironmentError("Environment variable 'OPEN_API_KEY' is not set.")
    if not S2_API_KEY:
        raise EnvironmentError("Environment variable 'S2_API_KEY' is not set.")
    if os.environ.get("FLASK_STARTED") != "1":
        Thread(target=start_flask, daemon=True).start()
        os.environ["FLASK_STARTED"] = "1"
    main()