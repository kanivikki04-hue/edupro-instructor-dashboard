import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(
    page_title="EduPro Instructor Performance Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("Instructor Performance and Course Quality Evaluation on EduPro")
st.caption("Instructor Performance | Course Quality | Student Feedback")

# Load Excel dataset automatically
FILE_PATH = "EduPro Instructor Performance Dashboard.xlsx"

@st.cache_data
def load_data(path):
    return pd.read_excel(path, engine="openpyxl")

if not os.path.exists(FILE_PATH):
    st.error(
        f"Excel file not found: {FILE_PATH}. "
        "Add your Excel dataset to the same GitHub repository as app.py."
    )
    st.stop()

try:
    df = load_data(FILE_PATH)
except Exception as e:
    st.error(f"Unable to load Excel file: {e}")
    st.stop()

if df.empty:
    st.warning("The Excel dataset is empty.")
    st.stop()

# Sidebar filters
st.sidebar.header("Dashboard Filters")

filtered_df = df.copy()

def find_column(possible_names):
    for col in df.columns:
        normalized = str(col).strip().lower().replace("_", " ")
        if normalized in possible_names:
            return col
    return None

instructor_col = find_column([
    "instructor", "instructor name", "teacher",
    "teacher name", "faculty", "faculty name"
])

course_col = find_column([
    "course", "course name", "subject", "program"
])

rating_col = find_column([
    "rating", "instructor rating", "course rating",
    "average rating", "satisfaction rating"
])

score_col = find_column([
    "score", "performance score", "evaluation score",
    "quality score"
])

completion_col = find_column([
    "completion rate", "course completion rate",
    "completion percentage", "completion"
])

feedback_col = find_column([
    "feedback", "student feedback", "comments",
    "review", "reviews"
])

if course_col:
    courses = sorted(filtered_df[course_col].dropna().unique().tolist())
    selected_courses = st.sidebar.multiselect(
        "Select Course", courses, default=courses
    )
    filtered_df = filtered_df[
        filtered_df[course_col].isin(selected_courses)
    ]

if instructor_col:
    instructors = sorted(
        filtered_df[instructor_col].dropna().unique().tolist()
    )
    selected_instructors = st.sidebar.multiselect(
        "Select Instructor", instructors, default=instructors
    )
    filtered_df = filtered_df[
        filtered_df[instructor_col].isin(selected_instructors)
    ]

# KPI cards
st.subheader("Key Performance Indicators")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Records", len(filtered_df))

c2.metric(
    "Total Instructors",
    filtered_df[instructor_col].nunique() if instructor_col else "N/A"
)

c3.metric(
    "Total Courses",
    filtered_df[course_col].nunique() if course_col else "N/A"
)

if rating_col:
    ratings = pd.to_numeric(filtered_df[rating_col], errors="coerce")
    c4.metric(
        "Average Rating",
        f"{ratings.mean():.2f}" if ratings.notna().any() else "N/A"
    )
elif score_col:
    scores = pd.to_numeric(filtered_df[score_col], errors="coerce")
    c4.metric(
        "Average Score",
        f"{scores.mean():.2f}" if scores.notna().any() else "N/A"
    )
else:
    c4.metric("Total Columns", len(filtered_df.columns))

st.divider()

# Performance charts
st.subheader("Performance Analysis")

left, right = st.columns(2)

with left:
    if instructor_col and rating_col:
        chart_df = filtered_df.copy()
        chart_df[rating_col] = pd.to_numeric(
            chart_df[rating_col], errors="coerce"
        )
        grouped = chart_df.groupby(instructor_col)[rating_col].mean()
        grouped = grouped.dropna().reset_index()

        if not grouped.empty:
            fig = px.bar(
                grouped,
                x=instructor_col,
                y=rating_col,
                title="Average Rating by Instructor",
                color=rating_col,
                color_continuous_scale="Blues"
            )
            st.plotly_chart(fig, use_container_width=True)

    elif instructor_col and score_col:
        chart_df = filtered_df.copy()
        chart_df[score_col] = pd.to_numeric(
            chart_df[score_col], errors="coerce"
        )
        grouped = chart_df.groupby(instructor_col)[score_col].mean()
        grouped = grouped.dropna().reset_index()

        if not grouped.empty:
            fig = px.bar(
                grouped,
                x=instructor_col,
                y=score_col,
                title="Performance Score by Instructor",
                color=score_col,
                color_continuous_scale="Blues"
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Instructor rating or performance score data is unavailable.")

with right:
    if course_col:
        counts = filtered_df[course_col].value_counts().reset_index()
        counts.columns = ["Course", "Records"]

        if not counts.empty:
            fig = px.pie(
                counts,
                names="Course",
                values="Records",
                title="Records by Course",
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Course information is unavailable.")

# Course completion analysis
if completion_col:
    st.subheader("Course Completion Analysis")

    completion_df = filtered_df.copy()
    completion_df[completion_col] = pd.to_numeric(
        completion_df[completion_col]
        .astype(str)
        .str.replace("%", "", regex=False),
        errors="coerce"
    )

    if course_col:
        grouped = completion_df.groupby(course_col)[completion_col].mean()
        grouped = grouped.dropna().reset_index()

        if not grouped.empty:
            fig = px.bar(
                grouped,
                x=course_col,
                y=completion_col,
                title="Average Course Completion",
                color=completion_col,
                color_continuous_scale="Teal"
            )
            st.plotly_chart(fig, use_container_width=True)

# Dataset table
st.divider()
st.subheader("Detailed Dataset")
st.dataframe(filtered_df, use_container_width=True, hide_index=True)

# Feedback section
if feedback_col:
    st.subheader("Student Feedback")
    feedback_data = filtered_df[feedback_col].dropna()

    if not feedback_data.empty:
        for feedback in feedback_data.head(10):
            st.write(f"• {feedback}")

# Download filtered dataset
csv = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    "Download Filtered Data",
    data=csv,
    file_name="edupro_filtered_data.csv",
    mime="text/csv"
)

st.divider()
st.caption("EduPro | Instructor Performance and Course Quality Evaluation")
