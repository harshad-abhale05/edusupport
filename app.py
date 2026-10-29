import streamlit as st
import pandas as pd
import os

# -------------------------------
# PAGE CONFIGURATION
# -------------------------------

st.set_page_config(
    page_title="EduSupport",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 EduSupport")
st.subheader("Early Identification of Students at Academic Risk")

st.write(
    "An academic support system that helps teachers identify "
    "students who may need additional educational assistance."
)

FILE = "students.csv"

COLUMNS = [
    "Student ID",
    "Student Name",
    "Attendance",
    "Internal Marks",
    "Assignments Completed",
    "Total Assignments",
    "Previous Marks",
    "Risk Score",
    "Risk Level",
    "Recommendation"
]


# -------------------------------
# LOAD STUDENT DATA
# -------------------------------

def load_data():
    if os.path.exists(FILE):
        return pd.read_csv(FILE)

    return pd.DataFrame(columns=COLUMNS)


if "students" not in st.session_state:
    st.session_state.students = load_data()


# -------------------------------
# RISK ASSESSMENT
# -------------------------------

def assess_risk(attendance, marks, completed, total, previous):

    score = 0

    # Attendance assessment
    if attendance < 60:
        score += 2
    elif attendance < 75:
        score += 1

    # Internal marks assessment
    if marks < 35:
        score += 2
    elif marks < 50:
        score += 1

    # Assignment completion assessment
    completion_rate = (completed / total) * 100

    if completion_rate < 40:
        score += 2
    elif completion_rate < 70:
        score += 1

    # Previous academic performance
    if previous < 35:
        score += 2
    elif previous < 50:
        score += 1

    # Classify the academic risk
    if score >= 5:
        risk = "High"
        recommendation = (
            "Arrange academic counselling, remedial classes, "
            "and a meeting with the student."
        )

    elif score >= 3:
        risk = "Medium"
        recommendation = (
            "Monitor progress, provide additional learning "
            "resources, and review attendance."
        )

    else:
        risk = "Low"
        recommendation = (
            "Continue regular academic monitoring "
            "and encourage consistent performance."
        )

    return score, risk, recommendation


# -------------------------------
# SIDEBAR NAVIGATION
# -------------------------------

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Add Student",
        "Student Records"
    ]
)


# -------------------------------
# DASHBOARD
# -------------------------------

if page == "Dashboard":

    df = st.session_state.students

    total = len(df)

    if total > 0:
        high = (df["Risk Level"] == "High").sum()
        medium = (df["Risk Level"] == "Medium").sum()
        low = (df["Risk Level"] == "Low").sum()
    else:
        high = medium = low = 0

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Students", total)
    col2.metric("High Risk", int(high))
    col3.metric("Medium Risk", int(medium))
    col4.metric("Low Risk", int(low))

    st.divider()

    st.subheader("Academic Risk Overview")

    if total > 0:

        chart_data = pd.DataFrame({
            "Risk Level": ["High", "Medium", "Low"],
            "Students": [high, medium, low]
        })

        st.bar_chart(
            chart_data.set_index("Risk Level")
        )

        st.subheader("Students Requiring Attention")

        at_risk = df[df["Risk Level"].isin(["High", "Medium"])]

        if len(at_risk) > 0:
            st.dataframe(
                at_risk[
                    [
                        "Student ID",
                        "Student Name",
                        "Attendance",
                        "Internal Marks",
                        "Risk Level"
                    ]
                ],
                use_container_width=True
            )
        else:
            st.success(
                "No students are currently classified "
                "as medium or high risk."
            )

    else:
        st.info(
            "No student records found. Add a student or load "
            "the demonstration data from the Student Records page."
        )


# -------------------------------
# ADD STUDENT
# -------------------------------

elif page == "Add Student":

    st.subheader("Enter Student Academic Information")

    with st.form("student_form"):

        student_id = st.text_input("Student ID")
        name = st.text_input("Student Name")

        attendance = st.number_input(
            "Attendance (%)",
            min_value=0.0,
            max_value=100.0,
            value=75.0
        )

        marks = st.number_input(
            "Internal Marks (%)",
            min_value=0.0,
            max_value=100.0,
            value=60.0
        )

        completed = st.number_input(
            "Assignments Completed",
            min_value=0,
            max_value=100,
            value=8
        )

        total_assignments = st.number_input(
            "Total Assignments",
            min_value=1,
            max_value=100,
            value=10
        )

        previous = st.number_input(
            "Previous Semester Marks (%)",
            min_value=0.0,
            max_value=100.0,
            value=60.0
        )

        submitted = st.form_submit_button(
            "Assess Academic Risk"
        )

    if submitted:

        if not student_id.strip() or not name.strip():
            st.error("Please enter both Student ID and Student Name.")

        elif completed > total_assignments:
            st.error(
                "Completed assignments cannot exceed total assignments."
            )

        elif student_id in st.session_state.students["Student ID"].astype(str).values:
            st.error("This Student ID already exists.")

        else:

            score, risk, recommendation = assess_risk(
                attendance,
                marks,
                completed,
                total_assignments,
                previous
            )

            new_student = pd.DataFrame([{
                "Student ID": student_id,
                "Student Name": name,
                "Attendance": attendance,
                "Internal Marks": marks,
                "Assignments Completed": completed,
                "Total Assignments": total_assignments,
                "Previous Marks": previous,
                "Risk Score": score,
                "Risk Level": risk,
                "Recommendation": recommendation
            }])

            st.session_state.students = pd.concat(
                [
                    st.session_state.students,
                    new_student
                ],
                ignore_index=True
            )

            st.session_state.students.to_csv(
                FILE,
                index=False
            )

            st.success("Student assessment completed!")

            st.metric("Academic Risk Score", f"{score}/8")

            if risk == "High":
                st.error(f"Risk Level: {risk}")
            elif risk == "Medium":
                st.warning(f"Risk Level: {risk}")
            else:
                st.success(f"Risk Level: {risk}")

            st.write("**Recommended Support:**")
            st.write(recommendation)


# -------------------------------
# STUDENT RECORDS
# -------------------------------

elif page == "Student Records":

    st.subheader("Student Records")

    df = st.session_state.students

    if len(df) > 0:

        st.dataframe(
            df,
            use_container_width=True
        )

        csv_data = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download Student Report (CSV)",
            data=csv_data,
            file_name="edusupport_report.csv",
            mime="text/csv"
        )

        if st.button("Load Demonstration Data"):

            demo_data = pd.DataFrame([
                {
                    "Student ID": "S101",
                    "Student Name": "Aarav",
                    "Attendance": 52,
                    "Internal Marks": 28,
                    "Assignments Completed": 3,
                    "Total Assignments": 10,
                    "Previous Marks": 32
                },
                {
                    "Student ID": "S102",
                    "Student Name": "Priya",
                    "Attendance": 68,
                    "Internal Marks": 45,
                    "Assignments Completed": 6,
                    "Total Assignments": 10,
                    "Previous Marks": 48
                },
                {
                    "Student ID": "S103",
                    "Student Name": "Rahul",
                    "Attendance": 92,
                    "Internal Marks": 82,
                    "Assignments Completed": 9,
                    "Total Assignments": 10,
                    "Previous Marks": 78
                }
            ])

            for col in [
                "Risk Score",
                "Risk Level",
                "Recommendation"
            ]:
                demo_data[col] = ""

            for index, row in demo_data.iterrows():

                score, risk, recommendation = assess_risk(
                    row["Attendance"],
                    row["Internal Marks"],
                    row["Assignments Completed"],
                    row["Total Assignments"],
                    row["Previous Marks"]
                )

                demo_data.at[index, "Risk Score"] = score
                demo_data.at[index, "Risk Level"] = risk
                demo_data.at[index, "Recommendation"] = recommendation

            st.session_state.students = pd.concat(
                [
                    st.session_state.students,
                    demo_data[COLUMNS]
                ],
                ignore_index=True
            )

            st.session_state.students.to_csv(
                FILE,
                index=False
            )

            st.rerun()

    else:

        st.info("No records available yet.")

        if st.button("Load Demonstration Data"):

            demo_data = pd.DataFrame([
                {
                    "Student ID": "S101",
                    "Student Name": "Aarav",
                    "Attendance": 52,
                    "Internal Marks": 28,
                    "Assignments Completed": 3,
                    "Total Assignments": 10,
                    "Previous Marks": 32
                },
                {
                    "Student ID": "S102",
                    "Student Name": "Priya",
                    "Attendance": 68,
                    "Internal Marks": 45,
                    "Assignments Completed": 6,
                    "Total Assignments": 10,
                    "Previous Marks": 48
                },
                {
                    "Student ID": "S103",
                    "Student Name": "Rahul",
                    "Attendance": 92,
                    "Internal Marks": 82,
                    "Assignments Completed": 9,
                    "Total Assignments": 10,
                    "Previous Marks": 78
                }
            ])

            for col in [
                "Risk Score",
                "Risk Level",
                "Recommendation"
            ]:
                demo_data[col] = ""

            for index, row in demo_data.iterrows():

                score, risk, recommendation = assess_risk(
                    row["Attendance"],
                    row["Internal Marks"],
                    row["Assignments Completed"],
                    row["Total Assignments"],
                    row["Previous Marks"]
                )

                demo_data.at[index, "Risk Score"] = score
                demo_data.at[index, "Risk Level"] = risk
                demo_data.at[index, "Recommendation"] = recommendation

            st.session_state.students = demo_data[COLUMNS]

            st.session_state.students.to_csv(
                FILE,
                index=False
            )

            st.rerun()
