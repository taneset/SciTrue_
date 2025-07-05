#%%
import streamlit as st
from datetime import datetime
import json
import os

# === CONFIG: Paths to your JSON output files ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

JSON_FILES = {
    "GPT-4o": os.path.join(BASE_DIR, "gpt4o", "gpt4o_results3.json"),
    "Perplexity": os.path.join(BASE_DIR, "perplexity", "sonar_pro_outputs3.json"),
    "SciTrue": os.path.join(BASE_DIR, "scitrue", "scitrue_results.json"),
}
def get_eval_file(source, username):
    filename = f"{username.lower()}_{source.lower().replace('-', '').replace(' ', '')}3.json"
    return os.path.join(BASE_DIR, "eval_output", filename)

def load_json_output(path):
    if not os.path.exists(path):
        st.error(f"JSON file not found: {path}")
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def badge_label(text, bg="#eee"):
    return f'<span style="background-color:{bg}; padding:4px 8px; border-radius:4px; font-weight:bold;">{text}</span>'

def get_value(d, key, fallback=None):
    v = d.get(key, None)
    if v is not None:
        return v
    if "output" in d and isinstance(d["output"], dict):
        return d["output"].get(key, fallback)
    return fallback

def get_subclaims(d):
    if isinstance(d, dict):
        if "subclaims" in d and isinstance(d["subclaims"], list):
            return d["subclaims"]
        if "output" in d and isinstance(d["output"], dict):
            return d["output"].get("subclaims", [])
    return []

def get_first_available(sub, *choices, default=None):
    for name in choices:
        if name in sub:
            val = sub[name]
            if val not in [None, '', []]:
                return val
    return default

def get_list(sub, *choices):
    for name in choices:
        val = sub.get(name)
        if isinstance(val, list) and val:
            return val
    return []

def get_username():
    if "username" not in st.session_state:
        st.session_state["username"] = ""
    st.sidebar.header("👤 User/Login")
    username = st.sidebar.text_input("Enter your username (required):", value=st.session_state["username"])
    if username:
        st.session_state["username"] = username.strip()
    return st.session_state["username"]

def save_or_update_evaluation(result, source, username):
    out_file = get_eval_file(source, username)
    if os.path.exists(out_file):
        with open(out_file, "r", encoding="utf-8") as f:
            all_evals = json.load(f)
    else:
        all_evals = []
    claim_key = result.get("claim", "").strip().lower()
    updated = False
    for i, ev in enumerate(all_evals):
        if ev.get("claim", "").strip().lower() == claim_key:
            all_evals[i] = result
            updated = True
            break
    if not updated:
        all_evals.append(result)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_evals, f, indent=2, ensure_ascii=False)

def load_existing_evals(source, username):
    file = get_eval_file(source, username)
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            all_evals = json.load(f)
        return all_evals
    return []

def evaluation_app(entry, source_name, username):

    # Load existing eval if any
    all_existing = load_existing_evals(source_name, username)
    claim_key = entry.get("claim", "").strip().lower()
    existing_eval = None
    for ev in all_existing:
        if ev.get("claim", "").strip().lower() == claim_key:
            existing_eval = ev
            break

    st.title("📝 Summary and Claim Evaluation")
    st.markdown(f"**Evaluating data from:** `{source_name}`  &nbsp;&nbsp;|&nbsp;&nbsp; 👤 **User:** `{username}`")

    st.markdown(
        badge_label("Claim", bg="#ef9a9a") +
        f'<span style="font-size:18px; font-weight:600; margin-left:8px;">{entry.get("claim", "")}</span>',
        unsafe_allow_html=True
    )
    summary = get_value(entry, "summary", "No summary available")
    st.markdown(
        badge_label("Generated Summary", bg="#90caf9") +
        f'<span style="font-size:18px; font-weight:600; margin-left:8px;">{summary}</span>',
        unsafe_allow_html=True
    )

    st.markdown("### Q1: Is the summary traceable to the sources (i.e., when you click the sources, do you get the relevant page)? (Required)")
    summary_attribution = st.radio(
        "",
        options=["Yes", "No"],
        index=0 if (not existing_eval or existing_eval.get("summary_attribution") != "No") else 1,
        key="summary_attribution"
    )
    summary_reason = st.text_area(
        "Reason for your choice (Optional)",
        height=80,
        key="summary_reason",
        value=existing_eval.get("summary_reason", "") if existing_eval else ""
    )

    if summary_attribution == "No":
        
        subclaims = get_subclaims(entry)
        subclaim_ratings = {}
        for i, sub in enumerate(subclaims):
            subclaim_ratings[i] = {
                "source_exists": "No",
                "scientific_check": "No",
                "factual": "No",
                "attribution_contribution": "No",
                "attribution_context_and_assumption": "No",
                "attribution_credibility": "No",
                "combined_reason": "",
            }
        # Count unique articles (for attribution_article_count)
        article_titles = set()
        for sub in subclaims:
            title = get_first_available(sub, 'title', default=None)
            if title:
                article_titles.add(title.strip().lower())
        num_articles = len(article_titles)
        num_subclaims = len(subclaims)
        # Save
        if st.button("💾 Save Evaluation (Summary not attributable)"):
            eval_json = {
                "summary_attribution": summary_attribution,
                "summary_reason": summary_reason,
                "overall_verdict": "No",
                "overall_verdict_reason": "",
                "subclaim_ratings": subclaim_ratings,
                "attribution_article_count": num_articles,
                "attribution_agreement": 1,
                "source": source_name,
                "claim": entry.get("claim", ""),
                "user": username,
                "saved_at": str(datetime.now())
            }
            save_or_update_evaluation(eval_json, source_name, username)
            st.success("Evaluation saved. All fields saved as 'No'.")
        st.stop()

    overall_reason = (
        get_value(entry, "Verdict and Reason", "") or
        get_value(entry, "reason_for_accuracy", "") or
        get_value(entry, "reason_for accuracy", "")
    )
    accuracy = get_value(entry, "accuracy", "")
    if accuracy:
        st.markdown(
            badge_label("Accuracy / Verdict Label", bg="#fbc02d") +
            f'<span style="font-size:18px; font-weight:600; margin-left:8px;">{accuracy}</span>',
            unsafe_allow_html=True
        )

    st.markdown(
        badge_label("Overall Verdict and Reason", bg="#a5d6a7") +
        f'<span style="font-size:17px; font-weight:600; margin-left:8px;">{overall_reason}</span>',
        unsafe_allow_html=True
    )

    st.markdown("### Q2: Does the overall verdict correctly reflect the summary? (Required)")
    overall_verdict = st.radio(
        "",
        options=["Yes", "No"],
        index=0 if (not existing_eval or existing_eval.get("overall_verdict") != "No") else 1,
        key="overall_verdict"
    )
    overall_verdict_reason = st.text_area(
        "Reason for your verdict (Optional)",
        height=80,
        key="overall_verdict_reason",
        value=existing_eval.get("overall_verdict_reason", "") if existing_eval else ""
    )

    st.markdown("## Subclaims Evaluation")
    subclaims = get_subclaims(entry)
    subclaim_ratings = {}

 
    for i, sub in enumerate(subclaims):
        existing_sub = existing_eval["subclaim_ratings"].get(str(i)) if existing_eval and "subclaim_ratings" in existing_eval else None
        # This mapping is critical: field name in JSON -> session_state key
        fields = {
            "source_exists": f"source_exists_{i}",
            "scientific_check": f"scientific_check_{i}",
            "factual": f"factual_{i}",
            "attribution_contribution": f"attribution_contribution_{i}",
            "attribution_context_and_assumption": f"context_and_assumption_{i}",
            "attribution_credibility": f"credibility_{i}",
            "title_inline": f"title_{i}",
            "authors_inline": f"authors_{i}",
        }

        init_flag = f"initialized_{i}"
        if not st.session_state.get(init_flag, False):
            for field_name, state_key in fields.items():
                if state_key not in st.session_state:
                    if existing_sub and existing_sub.get(field_name) in ["Yes", "No"]:
                        st.session_state[state_key] = existing_sub[field_name]
                    else:
                        st.session_state[state_key] = "Yes"
            st.session_state[init_flag] = True

        st.markdown(f"### Subclaim {i + 1}: {get_first_available(sub, 'claim', default='')}")

        with st.expander("Details"):
            for field_label, keynames in [
                ("URL", ("url",)),
                ("Venue", ("venue",)),
                ("Journal Title", ("journal_title",)),
                ("Authors", ("authors",)),
                ("Year", ("year",)),
                ("Title", ("title",)),
                ("Section", ("section",)),
                ("Contribution", ("contribution",)),
                ("Relevant Sentence", ("relevant_sentence", "relevant sentence")),
                ("Paragraph", ("paragraph",)),
                ("Label", ("label",)),
                ("Citation Count", ("citationCount",)),
                ("Abstract", ("abstract",)),
                ("Credibility Score", ("credibility_score",)),
            ]:
                val = get_first_available(sub, *keynames)
                if val:
                    if field_label == "Paragraph":
                        if st.checkbox(f"Show Paragraph (Subclaim {i + 1})", key=f"paragraph_{i}"):
                            st.markdown(val)
                    elif field_label == "Abstract":
                        if st.checkbox(f"Show Abstract (Subclaim {i + 1})", key=f"abstract_{i}"):
                            st.markdown(val)
                    else:
                        st.markdown(f"**{field_label}:** {val}")

            supporting = get_list(sub, "supporting_assumptions", "supporting assumptions")
            if supporting:
                st.markdown(f"**Supporting Assumptions:** {', '.join(str(s) for s in supporting)}")
            refuting = get_list(sub, "refuting_assumptions", "refuting assumptions")
            if refuting:
                st.markdown(f"**Refuting Assumptions:** {', '.join(str(s) for s in refuting)}")
            sjr_info = sub.get("sjr")
            if sjr_info:
                st.markdown("**SJR Info:**")
                if isinstance(sjr_info, dict):
                    for k, v in sjr_info.items():
                        st.markdown(f"- {k}: {v}")
                else:
                    st.markdown(str(sjr_info))

        source_exists_key    = f"source_exists_{i}"
        scientific_check_key = f"scientific_check_{i}"
        factual_key          = f"factual_{i}"
        contrib_key          = f"attribution_contribution_{i}"
        context_key          = f"context_and_assumption_{i}"
        cred_key             = f"credibility_{i}"
        title_inline_key     = f"title_{i}"
        authors_inline_key   = f"authors_{i}"

        lock_keys = [contrib_key, context_key, cred_key]

        if st.session_state.get(factual_key) == "No":
            for k in lock_keys:
                st.session_state[k] = "No"
        factual_val = st.session_state.get(factual_key, "Yes")

        source_exists = st.selectbox(
            "**Does the given URL open an article page?**",
            ["Yes", "No"],
            key=source_exists_key,
            index=1 if st.session_state.get(source_exists_key, "Yes") == "No" else 0
        )
        title_inline = st.selectbox(
            "**Does the title align with the URL?**",
            ["Yes", "No"],
            key=title_inline_key,
            index=1 if st.session_state.get(title_inline_key, "Yes") == "No" else 0
        )
        authors_inline = st.selectbox(
            "**Do the authors align with the URL?**",
            ["Yes", "No"],
            key=authors_inline_key,
            index=1 if st.session_state.get(authors_inline_key, "Yes") == "No" else 0
        )
        scientific_check = st.selectbox(
            "**Is the cited source an academic paper (title, abstract, authors, year)?**",
            ["Yes", "No"],
            key=scientific_check_key,
            index=1 if st.session_state.get(scientific_check_key, "Yes") == "No" else 0
        )
        factual = st.selectbox(
            "**Does the subclaim, or a semantically equivalent version of it, appear in both the summary and the cited article?**",
            ["Yes", "No"],
            key=factual_key,
            index=1 if st.session_state.get(factual_key, "Yes") == "No" else 0,
        )
        factual_val = st.session_state.get(factual_key, "Yes")

        if factual_val == "No" and any(st.session_state.get(k, "Yes") != "No" for k in lock_keys):
            for k in lock_keys:
                st.session_state[k] = "No"
            st.experimental_rerun()

        if factual_val == "No":
            st.info("Because the factual check is **'No'**, the following three answers are locked to 'No'.")

        attribution_contribution = st.selectbox(
            "**Is the contribution label accurate in context?**",
            ["Yes", "No"],
            key=contrib_key,
            index=1 if st.session_state.get(contrib_key, "Yes") == "No" else 0,
            disabled=factual_val == "No"
        )
        attribution_context_and_assumption = st.selectbox(
            "**Does the model correctly detect context and assumptions?**",
            ["Yes", "No"],
            key=context_key,
            index=1 if st.session_state.get(context_key, "Yes") == "No" else 0,
            disabled=factual_val == "No"
        )
        attribution_credibility = st.selectbox(
            "**Is the cited source’s impact accurately represented (±1 for impact factor, ±10 for citations)?**",
            ["Yes", "No"],
            key=cred_key,
            index=1 if st.session_state.get(cred_key, "Yes") == "No" else 0,
            disabled=factual_val == "No"
        )

        combined_reason = st.text_area(
            "Reasoning for above judgments (Optional)",
            key=f"combined_reason_{i}",
            height=80,
            value=existing_sub.get("combined_reason", "") if existing_sub else ""
        )

        subclaim_ratings[i] = {
            "source_exists":              st.session_state[source_exists_key],
            "scientific_check":           st.session_state[scientific_check_key],
            "factual":                    factual_val,
            "attribution_contribution":   st.session_state[contrib_key],
            "attribution_context_and_assumption": st.session_state[context_key],
            "attribution_credibility":    st.session_state[cred_key],
            "title_inline":               st.session_state[title_inline_key],
            "authors_inline":             st.session_state[authors_inline_key],
            "combined_reason":            combined_reason,
        }

        # Optionally remove clutter from top-level keys (clean up)
        entry.pop(f"title_{i}", None)
        entry.pop(f"authors_{i}", None)

# ───────────────────────── SUBCLAIM LOOP END ─────────────────────────

    # ---------- Attribution Counting Section (NEW QUESTION) ----------
    article_titles = set()
    for sub in subclaims:
        title = get_first_available(sub, 'title', default=None)
        if title:
            article_titles.add(title.strip().lower())

    num_articles = len(article_titles)
    num_subclaims = len(subclaims)

    if num_articles < num_subclaims:
        st.markdown(
            f"#### Attribution includes **{num_articles}** different articles for {num_subclaims} subclaims "
            "<span style='color:red; font-weight:bold;'>(Fewer articles than subclaims!)</span>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(f"#### Attribution includes **{num_articles}** different articles for {num_subclaims} subclaims.")

    attribution_agreement = st.radio(
        "How many articles for the subclaims?",
        options=[1,2,3,4,5,6],
        key="attribution_agreement",
        index=(
            [1,2,3,4,5,6].index(existing_eval.get("attribution_agreement",1))
            if existing_eval else 0
        )
    )

    
    # ---------------------------------------------------------------

    if st.button("💾 Save Evaluation"):
        errors = []

        if summary_attribution not in ["Yes", "No"]:
            errors.append("Please answer Q1: Summary attribution.")

        if overall_verdict not in ["Yes", "No"]:
            errors.append("Please answer Q2: Overall verdict.")

        for idx, ratings in subclaim_ratings.items():
            for field in [
                "source_exists",
                "scientific_check",
                "factual",
                "attribution_contribution",
                "attribution_context_and_assumption",
                "attribution_credibility",
            ]:
                if ratings[field] not in ["Yes", "No"]:
                    errors.append(f"Please answer '{field.replace('_', ' ').capitalize()}' for Subclaim {idx + 1}.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            eval_json = {
                "summary_attribution": summary_attribution,
                "summary_reason": summary_reason,
                "overall_verdict": overall_verdict,
                "overall_verdict_reason": overall_verdict_reason,
                "subclaim_ratings": subclaim_ratings,
                "attribution_article_count": num_articles,
                "attribution_agreement": attribution_agreement,
                "source": source_name,
                "claim": entry.get("claim", ""),
                "user": username,
                "saved_at": str(datetime.now())
            }
            save_or_update_evaluation(eval_json, source_name, username)
            st.success("Evaluation saved successfully!")
            st.json(eval_json)

def main():
    st.set_page_config(page_title="Summary Evaluation", layout="wide")
    username = get_username()
    if not username:
        st.warning("Please enter your username to start evaluating.")
        st.stop()

    st.sidebar.header("🔍 Select JSON Source")
    json_choice = st.sidebar.selectbox("Choose a system output to evaluate:", list(JSON_FILES.keys()))
    selected_json_path = JSON_FILES[json_choice]

    data = load_json_output(selected_json_path)
    if not data:
        st.stop()

    existing_evals = load_existing_evals(json_choice, username)
    evaluated_claims = set(ev.get("claim", "").strip().lower() for ev in existing_evals)

    options = []
    for i, entry in enumerate(data):
        claim = entry.get('claim', '').strip()
        mark = "✔️ " if claim.lower() in evaluated_claims else ""
        options.append(f"{mark}Claim {i+1}: {claim[:70]}")

    choice = st.selectbox("Which claim would you like to evaluate?", options)
    selected_idx = options.index(choice)
    selected_entry = data[selected_idx]
    selected_claim = selected_entry.get("claim", "").strip().lower()

    if "last_loaded_claim" not in st.session_state:
        st.session_state["last_loaded_claim"] = ""
    if st.session_state["last_loaded_claim"] != selected_claim:
        for k in list(st.session_state.keys()):
            if any(prefix in k for prefix in [
                "source_exists_", "scientific_check_", "factual_",
                "attribution_contribution_", "context_and_assumption_",
                "credibility_", "title_", "authors_", "combined_reason_",
                "initialized_"
            ]):
                del st.session_state[k]
        st.session_state["last_loaded_claim"] = selected_claim

    if selected_claim in evaluated_claims:
        st.info("This claim has already been evaluated by you. Submitting will update your previous evaluation.")
    else:
        st.warning("This claim has NOT yet been evaluated by you.")

    evaluation_app(selected_entry, json_choice, username)

if __name__ == "__main__":
    main()
# %%
