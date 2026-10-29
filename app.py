import os
from io import StringIO

import pandas as pd
import streamlit as st
import plotly.express as px

# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(
    page_title="EduSupport | Academic Risk Insights",
    page_icon="🎓",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.7rem; padding-bottom: 2rem;}
    div[data-testid="stMetric"] {
        background: #f5f7fb; border: 1px solid #e4e8f0;
        padding: 14px 16px; border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🎓 EduSupport")
st.caption("Early identification of students who may benefit from additional academic support")
st.info(
    "Educational support tool: risk categories are screening indicators, not definitive judgments "
    "about a student's ability. Use them to guide supportive follow-up, not punishment."
)

DATA_FILE = "students.csv"
COLUMNS = [
    "Student ID", "Student Name", "Attendance", "Internal Marks",
    "Assignments Completed", "Total Assignments", "Previous Marks",
    "Risk Score", "Risk Level", "Recommendation",
]
RISK_ORDER = ["High", "Medium", "Low"]


def assess_risk(attendance, marks, completed, total, previous):
    """Transparent rule-based screening score, maximum 8 points."""
    score = 0
    reasons = []

    if attendance < 60:
        score += 2
        reasons.append("attendance is below 60%")
    elif attendance < 75:
        score += 1
        reasons.append("attendance is below 75%")

    if marks < 35:
        score += 2
        reasons.append("internal marks are below 35%")
    elif marks < 50:
        score += 1
        reasons.append("internal marks are below 50%")

    completion_rate = (completed / total) * 100 if total else 0
    if completion_rate < 40:
        score += 2
        reasons.append("assignment completion is below 40%")
    elif completion_rate < 70:
        score += 1
        reasons.append("assignment completion is below 70%")

    if previous < 35:
        score += 2
        reasons.append("previous marks are below 35%")
    elif previous < 50:
        score += 1
        reasons.append("previous marks are below 50%")

    if score >= 5:
        level = "High"
    elif score >= 3:
        level = "Medium"
    else:
        level = "Low"

    recommendations = []
    if attendance < 75:
        recommendations.append("Arrange an attendance check-in and identify any barriers to attending.")
    if marks < 50:
        recommendations.append("Offer targeted practice, revision material, or remedial support.")
    if completion_rate < 70:
        recommendations.append("Agree on a manageable assignment completion plan.")
    if previous < 50:
        recommendations.append("Review earlier learning gaps with a mentor.")
    if not recommendations:
        recommendations.append("Continue regular check-ins and encourage consistent study habits.")

    recommendation = " ".join(recommendations)
    reason_text = "; ".join(reasons) if reasons else "no screening thresholds were triggered"
    return score, level, recommendation, reason_text, completion_rate


def empty_data():
    return pd.DataFrame(columns=COLUMNS)


def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            for col in COLUMNS:
                if col not in df.columns:
                    df[col] = ""
            return df[COLUMNS]
        except (pd.errors.EmptyDataError, pd.errors.ParserError, OSError):
            return empty_data()
    return empty_data()


def save_data(df):
    # On Streamlit Community Cloud, local files may not be durable across restarts.
    df[COLUMNS].to_csv(DATA_FILE, index=False)


def make_demo_data():
    examples = [
        ("S101", "Aarav", 52, 28, 3, 10, 32),
        ("S102", "Priya", 68, 45, 6, 10, 48),
        ("S103", "Rahul", 92, 82, 9, 10, 78),
        ("S104", "Anaya", 74, 54, 7, 10, 61),
        ("S105", "Ishaan", 61, 39, 4, 10, 43),
        ("S106", "Meera", 86, 71, 10, 10, 69),
    ]
    rows = []
    for sid, name, attendance, marks, completed, total, previous in examples:
        score, level, rec, reasons, completion_rate = assess_risk(
            attendance, marks, completed, total, previous
        )
        rows.append({
            "Student ID": sid,
            "Student Name": name,
            "Attendance": attendance,
            "Internal Marks": marks,
            "Assignments Completed": completed,
            "Total Assignments": total,
            "Previous Marks": previous,
            "Risk Score": score,
            "Risk Level": level,
            "Recommendation": rec,
        })
    return pd.DataFrame(rows, columns=COLUMNS)


def normalize_and_reassess(df):
    """Validate imported data and recalculate score fields from academic inputs."""
    required = [
        "Student ID", "Student Name", "Attendance", "Internal Marks",
        "Assignments Completed", "Total Assignments", "Previous Marks",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))

    result = df.copy()
    result["Student ID"] = result["Student ID"].astype(str).str.strip()
    result["Student Name"] = result["Student Name"].astype(str).str.strip()
    numeric_cols = [
        "Attendance", "Internal Marks", "Assignments Completed",
        "Total Assignments", "Previous Marks",
    ]
    for col in numeric_cols:
        result[col] = pd.to_numeric(result[col], errors="coerce")
    if result[required].isna().any().any():
        raise ValueError("Some required fields are blank or not numeric.")
    if (result["Student ID"] == "").any() or (result["Student Name"] == "").any():
        raise ValueError("Student ID and Student Name cannot be blank.")
    if result["Student ID"].duplicated().any():
        raise ValueError("Student IDs must be unique.")
    if not result["Attendance"].between(0, 100).all():
        raise ValueError("Attendance must be between 0 and 100.")
    if not result["Internal Marks"].between(0, 100).all():
        raise ValueError("Internal Marks must be between 0 and 100.")
    if not result["Previous Marks"].between(0, 100).all():
        raise ValueError("Previous Marks must be between 0 and 100.")
    if (result["Total Assignments"] < 1).any():
        raise ValueError("Total Assignments must be at least 1.")
    if (result["Assignments Completed"] < 0).any():
        raise ValueError("Assignments Completed cannot be negative.")
    if (result["Assignments Completed"] > result["Total Assignments"]).any():
        raise ValueError("Assignments Completed cannot exceed Total Assignments.")

    computed = result.apply(
        lambda r: assess_risk(
            r["Attendance"], r["Internal Marks"], r["Assignments Completed"],
            r["Total Assignments"], r["Previous Marks"]
        ),
        axis=1,
    )
    result["Risk Score"] = [x[0] for x in computed]
    result["Risk Level"] = [x[1] for x in computed]
    result["Recommendation"] = [x[2] for x in computed]
    return result[COLUMNS]


if "students" not in st.session_state:
    st.session_state.students = load_data()

if "flash_message" in st.session_state and st.session_state.flash_message:
    st.success(st.session_state.flash_message)
    st.session_state.flash_message = ""

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Add Student", "Student Records", "About & Data"],
)
st.sidebar.caption("Demo data is fictional. Avoid entering sensitive student information.")

# -----------------------------
# Dashboard
# -----------------------------
if page == "Dashboard":
    df = st.session_state.students.copy()
    total = len(df)
    if total:
        high = int((df["Risk Level"] == "High").sum())
        medium = int((df["Risk Level"] == "Medium").sum())
        low = int((df["Risk Level"] == "Low").sum())
        avg_attendance = pd.to_numeric(df["Attendance"], errors="coerce").mean()
        avg_marks = pd.to_numeric(df["Internal Marks"], errors="coerce").mean()
    else:
        high = medium = low = 0
        avg_attendance = avg_marks = 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Students", total)
    c2.metric("High Risk", high)
    c3.metric("Medium Risk", medium)
    c4.metric("Low Risk", low)
    c5.metric("Average Attendance", f"{avg_attendance:.1f}%")

    if total:
        st.subheader("Academic Risk Overview")
        left, right = st.columns(2)
        risk_counts = pd.DataFrame({
            "Risk Level": ["High", "Medium", "Low"],
            "Students": [high, medium, low],
        })
        with left:
            fig = px.bar(
                risk_counts, x="Risk Level", y="Students", color="Risk Level",
                category_orders={"Risk Level": RISK_ORDER},
                title="Students by risk category",
                text="Students",
            )
            fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Number of students")
            st.plotly_chart(fig, use_container_width=True)
        with right:
            fig = px.scatter(
                df, x="Attendance", y="Internal Marks", color="Risk Level",
                hover_name="Student Name", hover_data=["Student ID", "Previous Marks"],
                title="Attendance vs internal marks",
                category_orders={"Risk Level": RISK_ORDER},
                labels={"Attendance": "Attendance (%)", "Internal Marks": "Internal marks (%)"},
            )
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Students Who May Need Support")
        at_risk = df[df["Risk Level"].isin(["High", "Medium"])].copy()
        if not at_risk.empty:
            st.dataframe(
                at_risk[["Student ID", "Student Name", "Attendance", "Internal Marks",
                         "Risk Score", "Risk Level", "Recommendation"]],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.success("No students currently meet the medium- or high-risk screening thresholds.")
        st.caption(
            "Risk levels are produced by transparent rules, not a clinically or academically validated prediction model."
        )
    else:
        st.info("No student records found. Add a student or load fictional demonstration data from Student Records.")

# -----------------------------
# Add Student
# -----------------------------
elif page == "Add Student":
    st.subheader("Add a student and assess support needs")
    with st.form("student_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            student_id = st.text_input("Student ID", placeholder="e.g. S107")
            name = st.text_input("Student Name", placeholder="e.g. Student A")
            attendance = st.number_input("Attendance (%)", 0.0, 100.0, 75.0, step=1.0)
            marks = st.number_input("Internal Marks (%)", 0.0, 100.0, 60.0, step=1.0)
        with c2:
            completed = st.number_input("Assignments Completed", 0, 100, 8, step=1)
            total_assignments = st.number_input("Total Assignments", 1, 100, 10, step=1)
            previous = st.number_input("Previous Semester Marks (%)", 0.0, 100.0, 60.0, step=1.0)
        submitted = st.form_submit_button("Assess Academic Risk", type="primary")

    if submitted:
        current = st.session_state.students.copy()
        if not student_id.strip() or not name.strip():
            st.error("Please enter both Student ID and Student Name.")
        elif student_id.strip() in current["Student ID"].astype(str).values:
            st.error("This Student ID already exists. Use a unique ID.")
        elif completed > total_assignments:
            st.error("Completed assignments cannot exceed total assignments.")
        else:
            score, level, recommendation, reasons, completion_rate = assess_risk(
                attendance, marks, completed, total_assignments, previous
            )
            new_row = pd.DataFrame([{
                "Student ID": student_id.strip(),
                "Student Name": name.strip(),
                "Attendance": attendance,
                "Internal Marks": marks,
                "Assignments Completed": completed,
                "Total Assignments": total_assignments,
                "Previous Marks": previous,
                "Risk Score": score,
                "Risk Level": level,
                "Recommendation": recommendation,
            }], columns=COLUMNS)
            updated = pd.concat([current, new_row], ignore_index=True)
            st.session_state.students = updated
            save_data(updated)
            st.success("Assessment completed.")
            m1, m2, m3 = st.columns(3)
            m1.metric("Screening Score", f"{score}/8")
            m2.metric("Risk Category", level)
            m3.metric("Assignment Completion", f"{completion_rate:.0f}%")
            st.write("**Factors flagged**")
            st.write(reasons.capitalize() + ".")
            st.write("**Suggested support plan**")
            st.write(recommendation)
            st.caption("This result is a screening aid; a teacher or mentor should review the context.")

# -----------------------------
# Student records
# -----------------------------
elif page == "Student Records":
    st.subheader("Student Records")
    df = st.session_state.students.copy()

    top1, top2 = st.columns([2, 1])
    with top1:
        search = st.text_input("Search by student ID or name", placeholder="Type to filter records")
    with top2:
        risk_filter = st.selectbox("Filter by risk", ["All", "High", "Medium", "Low"])

    shown = df.copy()
    if search.strip():
        term = search.strip().lower()
        shown = shown[
            shown["Student ID"].astype(str).str.lower().str.contains(term, na=False)
            | shown["Student Name"].astype(str).str.lower().str.contains(term, na=False)
        ]
    if risk_filter != "All":
        shown = shown[shown["Risk Level"] == risk_filter]

    st.write(f"Showing **{len(shown)}** of **{len(df)}** records.")
    if not shown.empty:
        st.dataframe(shown, use_container_width=True, hide_index=True)
        st.download_button(
            "⬇️ Download filtered report (CSV)",
            data=shown.to_csv(index=False).encode("utf-8"),
            file_name="edusupport_student_report.csv",
            mime="text/csv",
            type="primary",
        )
    else:
        st.info("No matching records. Add a student or load demonstration data.")

    st.divider()
    st.subheader("Import or create demo records")
    up = st.file_uploader("Import student data from CSV", type=["csv"])
    if up is not None:
        if st.button("Validate and import CSV"):
            try:
                imported = normalize_and_reassess(pd.read_csv(up))
                combined = pd.concat([df, imported], ignore_index=True)
                if combined["Student ID"].astype(str).duplicated().any():
                    st.error("Import cancelled: one or more Student IDs already exist.")
                else:
                    st.session_state.students = combined[COLUMNS]
                    save_data(st.session_state.students)
                    st.success(f"Imported {len(imported)} records successfully.")
                    st.rerun()
            except Exception as exc:
                st.error(f"Could not import this file: {exc}")

    b1, b2 = st.columns(2)
    with b1:
        if st.button("Load demonstration data", use_container_width=True):
            demo = make_demo_data()
            existing_ids = set(df["Student ID"].astype(str))
            demo = demo[~demo["Student ID"].astype(str).isin(existing_ids)]
            updated = pd.concat([df, demo], ignore_index=True)
            st.session_state.students = updated[COLUMNS]
            save_data(st.session_state.students)
            st.session_state.flash_message = (
                f"Added {len(demo)} fictional demonstration records."
                if len(demo) else "Demo IDs already exist; no new records were added."
            )
            st.rerun()
    with b2:
        if st.button("Clear all records", use_container_width=True):
            st.session_state.confirm_clear = True
    if st.session_state.get("confirm_clear", False):
        st.warning("This removes all records from the current app data file. Download a backup first if needed.")
        yes, no = st.columns(2)
        with yes:
            if st.button("Confirm clear records", type="primary"):
                st.session_state.students = empty_data()
                save_data(st.session_state.students)
                st.session_state.confirm_clear = False
                st.session_state.flash_message = "All records cleared."
                st.rerun()
        with no:
            if st.button("Cancel clear"):
                st.session_state.confirm_clear = False
                st.rerun()

# -----------------------------
# About
# -----------------------------
else:
    st.subheader("About EduSupport")
    st.markdown(
        """
        **Purpose:** help educators identify students who may benefit from early academic support.

        **Inputs:** attendance, internal marks, assignment completion, and previous semester marks.

        **Current method:** transparent rule-based screening. The score is out of 8:
        - Attendance below 60%: +2; below 75%: +1
        - Internal marks below 35%: +2; below 50%: +1
        - Assignment completion below 40%: +2; below 70%: +1
        - Previous marks below 35%: +2; below 50%: +1
        - Score 5–8: High; score 3–4: Medium; score 0–2: Low

        **Limitations:** these thresholds are illustrative and must be reviewed by educators. This version
        does not claim to be a validated machine-learning prediction system. Synthetic demo records are fictional.
        """
    )
    st.warning(
        "Data persistence note: this version saves records to students.csv. Streamlit Community Cloud's local "
        "filesystem is not guaranteed to persist across restarts. For reliable shared records, connect a hosted database."
    )
    st.download_button(
        "Download blank CSV template",
        data=pd.DataFrame(columns=[
            "Student ID", "Student Name", "Attendance", "Internal Marks",
            "Assignments Completed", "Total Assignments", "Previous Marks",
        ]).to_csv(index=False).encode("utf-8"),
        file_name="edusupport_import_template.csv",
        mime="text/csv",
    )
