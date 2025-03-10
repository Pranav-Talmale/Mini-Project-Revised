import streamlit as st
import pandas as pd
import os
from pathlib import Path
from dotenv import load_dotenv
import streamlit.components.v1 as components
import json
import requests
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO

def create_dashboard_page(st, sql_alchemy_instance):
    """
    Create a dashboard page that integrates with PowerBI/Tableau or
    creates visualizations with Plotly as an alternative.
    """
    st.title("Student Analytics Dashboard")
    
    with st.container():
        st.markdown("""
        <div style="background-color: #1E1E1E; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
        <h3>Student Data Analytics</h3>
        <p>This dashboard provides insights into student distributions, subject enrollments, and batch formations.</p>
        </div>
        """, unsafe_allow_html=True)

    # Create tabs for different integration options
    tabs = st.tabs(["Built-in Analytics", "PowerBI Integration", "Tableau Integration"])
    
    # Tab 1: Built-in analytics with Plotly
    with tabs[0]:
        st.subheader("Built-in Analytics Dashboard")
        
        # Data Query Section
        with st.expander("Data Sources", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                # Get student count by division
                division_query = """
                SELECT division, COUNT(*) as count 
                FROM students 
                GROUP BY division
                """
                division_data = sql_alchemy_instance.run_query(division_query)
                
                # Get subject enrollment distribution
                subject_query = """
                SELECT sub.subject_name, COUNT(e.id) as enrollment_count
                FROM subjects sub
                JOIN enrollments e ON sub.subject_code = e.subject_code
                GROUP BY sub.subject_name
                ORDER BY enrollment_count DESC
                LIMIT 10
                """
                subject_data = sql_alchemy_instance.run_query(subject_query)
            
            with col2:
                # Get batch distribution
                batch_query = """
                SELECT batch, COUNT(*) as count 
                FROM students 
                WHERE batch IS NOT NULL
                GROUP BY batch
                """
                batch_data = sql_alchemy_instance.run_query(batch_query)
                
                # Get subject type distribution
                subject_type_query = """
                SELECT sub.subject_type, COUNT(e.id) as enrollment_count
                FROM subjects sub
                JOIN enrollments e ON sub.subject_code = e.subject_code
                GROUP BY sub.subject_type
                """
                subject_type_data = sql_alchemy_instance.run_query(subject_type_query)
        
        # Visualizations for the dashboard
        st.subheader("Student Distribution Overview")
        
        # Row 1: Division and Batch distribution
        col1, col2 = st.columns(2)
        
        with col1:
            if isinstance(division_data, pd.DataFrame) and not division_data.empty:
                fig = px.pie(division_data, values='count', names='division', 
                            title='Students by Division',
                            color_discrete_sequence=px.colors.qualitative.Plotly)
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No division data available.")
        
        with col2:
            if isinstance(batch_data, pd.DataFrame) and not batch_data.empty:
                fig = px.bar(batch_data, x='batch', y='count',
                            title='Students by Batch',
                            color='count',
                            color_continuous_scale='Viridis')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No batch data available.")
        
        # Row 2: Subject enrollment and subject type distribution
        col1, col2 = st.columns(2)
        
        with col1:
            if isinstance(subject_data, pd.DataFrame) and not subject_data.empty:
                fig = px.bar(subject_data, x='enrollment_count', y='subject_name', 
                            title='Top 10 Subjects by Enrollment',
                            orientation='h',
                            color='enrollment_count',
                            color_continuous_scale='Viridis')
                fig.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No subject enrollment data available.")
        
        with col2:
            if isinstance(subject_type_data, pd.DataFrame) and not subject_type_data.empty:
                fig = px.pie(subject_type_data, values='enrollment_count', names='subject_type',
                            title='Enrollment by Subject Type',
                            color_discrete_sequence=px.colors.qualitative.Plotly)
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No subject type data available.")
        
        # Row 3: Custom analytical queries
        st.subheader("Custom Analytics")
        
        query_options = [
            "DLO Subject Combinations",
            "Students without Batch Assignments",
            "Batch Distribution by Division",
            "Subject Enrollment Trends"
        ]
        
        selected_query = st.selectbox("Select Analysis", query_options)
        
        if selected_query == "DLO Subject Combinations":
            dlo_combo_query = """
            SELECT 
                s1.subject_name as subject1, 
                s2.subject_name as subject2, 
                COUNT(DISTINCT e1.usn) as student_count
            FROM 
                enrollments e1
            JOIN 
                enrollments e2 ON e1.usn = e2.usn AND e1.subject_code < e2.subject_code
            JOIN 
                subjects s1 ON e1.subject_code = s1.subject_code
            JOIN 
                subjects s2 ON e2.subject_code = s2.subject_code
            WHERE 
                s1.subject_type = 'DLO' AND s2.subject_type = 'DLO'
            GROUP BY 
                s1.subject_name, s2.subject_name
            ORDER BY 
                student_count DESC
            """
            
            combo_data = sql_alchemy_instance.run_query(dlo_combo_query)
            
            if isinstance(combo_data, pd.DataFrame) and not combo_data.empty:
                st.subheader("Popular DLO Subject Combinations")
                
                # Create a heatmap for subject combinations
                pivot_data = combo_data.pivot_table(
                    values='student_count', 
                    index='subject1',
                    columns='subject2', 
                    fill_value=0
                )
                
                fig = px.imshow(pivot_data, 
                                text_auto=True, 
                                aspect="auto",
                                color_continuous_scale='Viridis',
                                title='DLO Subject Combination Heatmap')
                st.plotly_chart(fig, use_container_width=True)
                
                # Also show as a table
                st.dataframe(combo_data, hide_index=True)
            else:
                st.info("No DLO subject combination data available.")
        
        elif selected_query == "Students without Batch Assignments":
            no_batch_query = """
            SELECT usn, name_of_the_student, division
            FROM students
            WHERE batch IS NULL
            """
            
            no_batch_data = sql_alchemy_instance.run_query(no_batch_query)
            
            if isinstance(no_batch_data, pd.DataFrame) and not no_batch_data.empty:
                st.warning(f"{len(no_batch_data)} students do not have batch assignments")
                st.dataframe(no_batch_data, hide_index=True)
            else:
                st.success("All students have been assigned to batches.")
        
        elif selected_query == "Batch Distribution by Division":
            batch_div_query = """
            SELECT division, batch, COUNT(*) as student_count
            FROM students
            WHERE batch IS NOT NULL
            GROUP BY division, batch
            ORDER BY division, batch
            """
            
            batch_div_data = sql_alchemy_instance.run_query(batch_div_query)
            
            if isinstance(batch_div_data, pd.DataFrame) and not batch_div_data.empty:
                fig = px.bar(batch_div_data, 
                            x='batch', 
                            y='student_count',
                            color='division',
                            barmode='group',
                            title='Batch Distribution by Division')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No batch distribution data available.")
        
        elif selected_query == "Subject Enrollment Trends":
            subject_trend_query = """
            SELECT sub.subject_type, sub.subject_name, COUNT(e.id) as enrollment_count
            FROM subjects sub
            JOIN enrollments e ON sub.subject_code = e.subject_code
            GROUP BY sub.subject_type, sub.subject_name
            ORDER BY sub.subject_type, enrollment_count DESC
            """
            
            trend_data = sql_alchemy_instance.run_query(subject_trend_query)
            
            if isinstance(trend_data, pd.DataFrame) and not trend_data.empty:
                fig = px.sunburst(
                    trend_data,
                    path=['subject_type', 'subject_name'],
                    values='enrollment_count',
                    title='Subject Enrollment Hierarchy'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No subject enrollment trend data available.")
    
    # Tab 2: PowerBI Integration
    with tabs[1]:
        st.subheader("PowerBI Dashboard Integration")
        
        # PowerBI integration method
        powerbi_method = st.radio(
            "PowerBI Integration Method:",
            ["Embed Report", "Publish & Share", "Export Data to PowerBI"],
            horizontal=True
        )
        
        if powerbi_method == "Embed Report":
            st.info("To embed a PowerBI report, you'll need:")
            st.markdown("""
            1. A PowerBI Pro account
            2. A published report
            3. The embedded report URL
            """)
            
            powerbi_url = st.text_input(
                "Enter your PowerBI Embedded Report URL",
                placeholder="https://app.powerbi.com/reportEmbed?reportId=..."
            )
            
            if powerbi_url:
                # Using an iframe to embed the PowerBI report
                st.components.v1.iframe(
                    powerbi_url,
                    height=600,
                    scrolling=True
                )
                
                st.caption("If the report doesn't load, check if it's publicly accessible or properly shared.")
            else:
                # Show a placeholder for the PowerBI integration
                st.image("https://via.placeholder.com/800x400.png?text=PowerBI+Dashboard+Preview", 
                        caption="PowerBI Dashboard Placeholder")
        
        elif powerbi_method == "Publish & Share":
            st.subheader("Export Data for PowerBI")
            
            # Query to get data for export
            export_query = st.text_area(
                "Enter SQL query to export data:",
                """SELECT s.usn, s.name_of_the_student, s.division, s.batch, 
                        sub.subject_code, sub.subject_name, sub.subject_type
                 FROM students s
                 JOIN enrollments e ON s.usn = e.usn
                 JOIN subjects sub ON e.subject_code = sub.subject_code"""
            )
            
            if st.button("Preview Export Data"):
                export_data = sql_alchemy_instance.run_query(export_query)
                
                if isinstance(export_data, pd.DataFrame) and not export_data.empty:
                    st.dataframe(export_data.head(10))
                    
                    # Generate CSV for PowerBI
                    csv = export_data.to_csv(index=False)
                    st.download_button(
                        label="Download CSV for PowerBI",
                        data=csv,
                        file_name="docgene_powerbi_data.csv",
                        mime="text/csv"
                    )
                    
                    st.markdown("""
                    ### Next Steps:
                    1. Import this CSV into PowerBI Desktop
                    2. Create your visualizations and dashboard
                    3. Publish to PowerBI Service
                    4. Use "Embed Report" option to integrate with this app
                    """)
                else:
                    st.error("Query returned no data or had an error.")
        
        elif powerbi_method == "Export Data to PowerBI":
            st.subheader("Direct PowerBI Integration")
            st.info("This feature requires the PowerBI API and authenticated access.")
            
            # Simulated PowerBI API integration fields
            powerbi_workspace = st.text_input("PowerBI Workspace ID")
            powerbi_dataset = st.text_input("PowerBI Dataset ID")
            powerbi_api_key = st.text_input("PowerBI API Key", type="password")
            
            if st.button("Push Data to PowerBI") and powerbi_workspace and powerbi_dataset and powerbi_api_key:
                st.success("This would push data to PowerBI in a production environment")
                st.markdown("""
                For actual implementation, you would need:
                1. Azure AD authentication
                2. PowerBI REST API integration
                3. Regular data refresh scheduling
                """)

    # Tab 3: Tableau Integration
    with tabs[2]:
        st.subheader("Tableau Dashboard Integration")
        
        # Tableau integration method
        tableau_method = st.radio(
            "Tableau Integration Method:",
            ["Embed Tableau Public", "Tableau Server Integration", "Export Data to Tableau"],
            horizontal=True
        )
        
        if tableau_method == "Embed Tableau Public":
            st.info("To embed a Tableau Public visualization:")
            st.markdown("""
            1. Publish your dashboard to Tableau Public
            2. Get the embed code (Share button on your viz)
            3. Paste the embed code or URL below
            """)
            
            tableau_url = st.text_input(
                "Enter your Tableau Public URL or Embed Code",
                placeholder="https://public.tableau.com/views/..."
            )
            
            if tableau_url:
                # Extract URL if embed code is provided
                if "<script" in tableau_url:
                    import re
                    url_match = re.search(r'viz=([^"&]+)', tableau_url)
                    if url_match:
                        tableau_url = url_match.group(1)
                
                # Using an iframe to embed the Tableau visualization
                components.iframe(
                    tableau_url,
                    height=800,
                    scrolling=False
                )
            else:
                # Show a placeholder for the Tableau integration
                st.image("https://via.placeholder.com/800x400.png?text=Tableau+Dashboard+Preview", 
                        caption="Tableau Dashboard Placeholder")
        
        elif tableau_method == "Tableau Server Integration":
            st.subheader("Tableau Server Integration")
            st.info("This option requires a Tableau Server or Tableau Online subscription.")
            
            tableau_server = st.text_input("Tableau Server URL", placeholder="https://tableau.yourcompany.com")
            tableau_view = st.text_input("View Path", placeholder="/views/workbook/dashboard")
            tableau_token = st.text_input("Tableau Token (if required)", type="password")
            
            if tableau_server and tableau_view:
                # Build the embed URL
                embed_url = f"{tableau_server}/trusted/{tableau_token if tableau_token else ''}{tableau_view}?:embed=yes"
                
                st.markdown(f"Embedding: `{embed_url}`")
                
                # Using an iframe to embed the Tableau Server visualization
                components.iframe(
                    embed_url,
                    height=700,
                    scrolling=False
                )
            else:
                st.warning("Please enter your Tableau Server details to continue.")
        
        elif tableau_method == "Export Data to Tableau":
            st.subheader("Export Data for Tableau")
            
            # Options for data export
            export_options = st.multiselect(
                "Select data to export:",
                ["Students", "Subjects", "Enrollments", "Batches", "Custom Query"],
                default=["Students", "Subjects"]
            )
            
            custom_query = ""
            if "Custom Query" in export_options:
                custom_query = st.text_area(
                    "Enter custom SQL query:",
                    """SELECT s.*, e.subject_code, sub.subject_name
                       FROM students s
                       JOIN enrollments e ON s.usn = e.usn
                       JOIN subjects sub ON e.subject_code = sub.subject_code"""
                )
            
            if st.button("Generate Tableau Data Extract"):
                # Create a Tableau Data Extract (simulated)
                st.info("Preparing data for Tableau...")
                
                # Create a zip file with CSV exports
                import io
                import zipfile
                
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zf:
                    if "Students" in export_options:
                        students_data = sql_alchemy_instance.run_query("SELECT * FROM students")
                        if isinstance(students_data, pd.DataFrame):
                            zf.writestr("students.csv", students_data.to_csv(index=False))
                    
                    if "Subjects" in export_options:
                        subjects_data = sql_alchemy_instance.run_query("SELECT * FROM subjects")
                        if isinstance(subjects_data, pd.DataFrame):
                            zf.writestr("subjects.csv", subjects_data.to_csv(index=False))
                    
                    if "Enrollments" in export_options:
                        enrollments_data = sql_alchemy_instance.run_query("SELECT * FROM enrollments")
                        if isinstance(enrollments_data, pd.DataFrame):
                            zf.writestr("enrollments.csv", enrollments_data.to_csv(index=False))
                    
                    if "Batches" in export_options:
                        batches_data = sql_alchemy_instance.run_query(
                            "SELECT batch, COUNT(*) as count FROM students GROUP BY batch"
                        )
                        if isinstance(batches_data, pd.DataFrame):
                            zf.writestr("batches.csv", batches_data.to_csv(index=False))
                    
                    if "Custom Query" in export_options and custom_query:
                        custom_data = sql_alchemy_instance.run_query(custom_query)
                        if isinstance(custom_data, pd.DataFrame):
                            zf.writestr("custom_query.csv", custom_data.to_csv(index=False))
                
                zip_buffer.seek(0)
                
                # Provide the zip file for download
                st.download_button(
                    label="Download Data for Tableau",
                    data=zip_buffer,
                    file_name="docgene_tableau_data.zip",
                    mime="application/zip"
                )
                
                st.markdown("""
                ### Steps to use in Tableau:
                1. Extract the zip file
                2. Open Tableau Desktop
                3. Connect to a Text file (CSV)
                4. Import each CSV as needed
                5. Create relationships between tables using common fields
                6. Build your dashboard
                7. Publish to Tableau Public or Tableau Server
                """)
                
                st.info("For a more seamless integration, consider setting up a database connection that Tableau can access directly.")