                         title="Bottom 10 Instructors by Teacher Rating")
            fig.update_layout(coloraxis_showscale=False, yaxis_title="")
            st.plotly_chart(fig, use_container_width=True)
        interpretation("Leaderboards use TeacherRating from the Teachers sheet. Transaction volume is a separate activity measure and should not be interpreted as teaching quality.")
        col_c, col_d = st.columns(2)
        with col_c:
            fig = px.histogram(teachers_f, x="TeacherRating", nbins=10,
                               title="Teacher Rating Distribution", labels={"TeacherRating": "Teacher rating"})
            st.plotly_chart(fig, use_container_width=True)
        with col_d:
            tx_counts = tx_f.groupby("TeacherID").size().rename("TransactionCount").reset_index()
            volume = teachers_f.merge(tx_counts, on="TeacherID", how="left", validate="one_to_one")
            volume["TransactionCount"] = volume["TransactionCount"].fillna(0)
            volume = volume.sort_values("TransactionCount", ascending=False).head(15)
            fig = px.bar(volume, x="TeacherName", y="TransactionCount", color="Expertise",
                         title="Instructor Transaction Volume (Top 15)",
                         hover_data=["TeacherRating", "YearsOfExperience"])
            fig.update_layout(xaxis_tickangle=-35, xaxis_title="")
            st.plotly_chart(fig, use_container_width=True)
        fig = px.scatter(
            teachers_f, x="YearsOfExperience", y="TeacherRating", color="Expertise",
            hover_name="TeacherName", hover_data=["Gender", "Age"],
            title="Teaching Experience vs. Teacher Rating",
            labels={"YearsOfExperience": "Teaching experience (years)", "TeacherRating": "Teacher rating"}
        )
        st.plotly_chart(fig, use_container_width=True)
        interpretation("The scatter plot describes association only; it does not prove that experience causes higher ratings.")
        make_download(ranking, "instructor_performance")

with tab_courses:
    st.subheader("Course Quality")
    if courses_f.empty:
        st.info("No courses match the selected category and level filters.")
    else:
        col_a, col_b = st.columns(2)
        with col_a:
            by_category = courses_f.groupby("CourseCategory", dropna=False)["CourseRating"].mean().reset_index()
            by_category = by_category.sort_values("CourseRating", ascending=True)
            fig = px.bar(by_category, x="CourseRating", y="CourseCategory", orientation="h",
                         title="Average Course Rating by Category",
                         labels={"CourseRating": "Average course rating", "CourseCategory": "Category"})
            st.plotly_chart(fig, use_container_width=True)
        with col_b:
            by_level = courses_f.groupby("CourseLevel", dropna=False)["CourseRating"].mean().reset_index()
            fig = px.bar(by_level, x="CourseLevel", y="CourseRating", color="CourseLevel",
                         title="Average Course Rating by Level",
                         labels={"CourseRating": "Average course rating", "CourseLevel": "Course level"})
            st.plotly_chart(fig, use_container_width=True)
        fig = px.histogram(courses_f, x="CourseRating", nbins=10, color="CourseType",
                           title="Course Rating Distribution")
        st.plotly_chart(fig, use_container_width=True)
        col_c, col_d = st.columns(2)
        with col_c:
            st.markdown("**Highest-rated courses**")
            st.dataframe(courses_f.sort_values("CourseRating", ascending=False).head(10)[
                ["CourseName", "CourseCategory", "CourseLevel", "CourseType", "CourseRating"]
            ], use_container_width=True, hide_index=True)
        with col_d:
            st.markdown("**Lowest-rated courses**")
            st.dataframe(courses_f.sort_values("CourseRating", ascending=True).head(10)[
                ["CourseName", "CourseCategory", "CourseLevel", "CourseType", "CourseRating"]
            ], use_container_width=True, hide_index=True)
        interpretation("Course ratings are taken from the Courses sheet, so each course contributes once to course-level averages regardless of transaction volume.")
        make_download(courses_f, "course_quality")

with tab_expertise:
    st.subheader("Expertise Analysis")
    if teachers_f.empty:
        st.info("No instructors match the current filters.")
    else:
        expertise_summary = teachers_f.groupby("Expertise").agg(
            Instructors=("TeacherID", "nunique"),
            AvgTeacherRating=("TeacherRating", "mean"),
            AvgExperience=("YearsOfExperience", "mean")
        ).reset_index().sort_values("Instructors", ascending=False)
        fig = px.bar(expertise_summary, x="Expertise", y="Instructors", color="AvgTeacherRating",
                     hover_data=["AvgTeacherRating", "AvgExperience"],
                     title="Instructor Expertise Distribution")
        fig.update_layout(xaxis_tickangle=-35, xaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

        # Exact text match is a limited proxy, not a semantic skill-match score.
        expertise_category = tx_f.dropna(subset=["Expertise", "CourseCategory"]).copy()
        expertise_category["ExactLabelMatch"] = (
            expertise_category["Expertise"].astype(str).str.strip().str.casefold()
            == expertise_category["CourseCategory"].astype(str).str.strip().str.casefold()
        )
        if not expertise_category.empty:
            match_summary = expertise_category.groupby("CourseCategory").agg(
                TransactionRows=("TransactionID", "size"),
                ExactLabelMatches=("ExactLabelMatch", "sum")
            ).reset_index()
            match_summary["ExactLabelMatchRatePct"] = (
                match_summary["ExactLabelMatches"] / match_summary["TransactionRows"] * 100
            )
            fig = px.bar(match_summary, x="CourseCategory", y="ExactLabelMatchRatePct",
                         hover_data=["TransactionRows", "ExactLabelMatches"],
                         title="Exact Expertise Label Match by Course Category (%)",
                         labels={"ExactLabelMatchRatePct": "Exact label match (%)", "CourseCategory": "Course category"})
            fig.update_layout(xaxis_tickangle=-35, xaxis_title="")
            st.plotly_chart(fig, use_container_width=True)
            st.caption("This is an exact text-label comparison between the transaction's recorded instructor Expertise and CourseCategory. It is not a validated subject-matter match score; related labels can differ, and matching labels do not prove instructional fit.")
        else:
            st.info("No transaction rows have both instructor expertise and course category available.")
        interpretation("The workbook records TeacherID on transactions, which supports transaction-level attribution. It does not define a permanent instructor-to-course assignment in the Courses catalog.")
        make_download(expertise_summary, "expertise_summary")

with tab_transactions:
    st.subheader("Enrollment & Transactions")
    c1, c2, c3 = st.columns(3)
    c1.metric("Filtered transaction amount", f"{fmt_number(tx_f['Amount'].sum(), 2)}")
    paid_tx = tx_f[tx_f["CourseType"].astype(str).str.casefold() == "paid"]
    free_tx = tx_f[tx_f["CourseType"].astype(str).str.casefold() == "free"]
    c2.metric("Paid transaction amount", f"{fmt_number(paid_tx['Amount'].sum(), 2)}")
    c3.metric("Free transaction rows", f"{len(free_tx):,}")

    if tx_f.empty:
        st.info("No transactions match the current filters and date range.")
    else:
        monthly = tx_f.dropna(subset=["TransactionDate"]).copy()
        monthly["Month"] = monthly["TransactionDate"].dt.to_period("M").dt.to_timestamp()
        monthly_summary = monthly.groupby("Month").agg(
            Transactions=("TransactionID", "size"),
            RecordedAmount=("Amount", "sum")
        ).reset_index()
        fig = go.Figure()
        fig.add_trace(go.Bar(x=monthly_summary["Month"], y=monthly_summary["Transactions"],
                             name="Transactions", yaxis="y"))
        fig.add_trace(go.Scatter(x=monthly_summary["Month"], y=monthly_summary["RecordedAmount"],
                                 name="Recorded amount", mode="lines+markers", yaxis="y2"))
        fig.update_layout(
            title="Monthly Transactions and Recorded Amount",
            xaxis_title="Month",
            yaxis=dict(title="Transaction rows"),
            yaxis2=dict(title="Recorded amount", overlaying="y", side="right"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)

        col_a, col_b = st.columns(2)
        with col_a:
            cat_tx = tx_f.groupby("CourseCategory").size().reset_index(name="Transactions").sort_values("Transactions", ascending=False)
            fig = px.bar(cat_tx, x="CourseCategory", y="Transactions", color="Transactions",
                         title="Transactions by Course Category")
            fig.update_layout(xaxis_tickangle=-35, xaxis_title="")
            st.plotly_chart(fig, use_container_width=True)
        with col_b:
            level_tx = tx_f.groupby("CourseLevel").size().reset_index(name="Transactions")
            fig = px.bar(level_tx, x="CourseLevel", y="Transactions", color="CourseLevel",
                         title="Transactions by Course Level")
            st.plotly_chart(fig, use_container_width=True)

        free_paid = tx_f.groupby("CourseType").agg(
            Transactions=("TransactionID", "size"),
            RecordedAmount=("Amount", "sum")
        ).reset_index()
        fig = px.bar(free_paid, x="CourseType", y="Transactions", color="CourseType",
                     hover_data=["RecordedAmount"], title="Free vs Paid Course Activity")
        st.plotly_chart(fig, use_container_width=True)
