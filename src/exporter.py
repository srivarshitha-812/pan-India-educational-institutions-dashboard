"""
Comprehensive Exporter for Master Database, Quality Reports, and Verification Summaries.
"""
import pandas as pd
import sqlite3
from typing import Dict, Any, List
from config import (
    DB_PATH, MASTER_COLUMNS, OUTPUT_MASTER_XLSX, OUTPUT_MASTER_CSV,
    OUTPUT_VERIFICATION_REPORT, OUTPUT_QUALITY_REPORT,
    OUTPUT_STATE_SUMMARY, OUTPUT_SOURCE_SUMMARY
)
from src.database import Database
from src.logger import logger

class Exporter:
    def __init__(self, db: Database):
        self.db = db

    def export_all(self):
        """Generates all 6 required deliverable files."""
        logger.info("Generating master exports and analytical reports...")
        self.export_master_files()
        self.export_verification_report()
        self.export_data_quality_report()
        self.export_state_summary()
        self.export_source_summary()
        logger.info("All export files generated successfully in data/processed/")

    def export_master_files(self):
        """Exports master_institutions.xlsx and master_institutions.csv."""
        with self.db.get_connection() as conn:
            query = "SELECT * FROM institutions ORDER BY state, district, name;"
            df = pd.read_sql_query(query, conn)

        if df.empty:
            logger.warning("No records found in master institutions table to export.")
            # Create empty template with headers
            empty_df = pd.DataFrame(columns=MASTER_COLUMNS)
            empty_df.to_csv(OUTPUT_MASTER_CSV, index=False, encoding="utf-8-sig")
            empty_df.to_excel(OUTPUT_MASTER_XLSX, index=False, engine="openpyxl")
            return

        # Map SQLite column names to MASTER_COLUMNS
        col_mapping = {
            "institution_id": "Institution ID",
            "name": "Institution Name",
            "education_level": "Education Level",
            "institution_type": "Institution Type",
            "institution_category": "Institution Category",
            "management_type": "Management Type",
            "official_institution_id": "Official Institution ID",
            "udise_code": "UDISE Code",
            "aishe_code": "AISHE Code",
            "aicte_id": "AICTE ID",
            "nmc_id": "NMC ID",
            "ncte_id": "NCTE ID",
            "other_regulator_id": "Other Regulator ID",
            "state": "State",
            "district": "District",
            "block_mandal": "Block/Mandal",
            "city_town_village": "City/Town/Village",
            "full_address": "Full Address",
            "pincode": "PIN Code",
            "latitude": "Latitude",
            "longitude": "Longitude",
            "university_affiliation": "University Affiliation",
            "board_affiliation": "Board/Affiliation",
            "courses_programmes": "Courses/Programmes",
            "year_established": "Year Established",
            "website": "Website",
            "email": "Email",
            "phone": "Phone",
            "recognition_status": "Recognition Status",
            "recognition_authority": "Recognition Authority",
            "approval_status": "Approval Status",
            "approval_authority": "Approval Authority",
            "source_database": "Source Database",
            "source_url": "Source URL",
            "collection_date": "Collection Date",
            "last_verification_date": "Last Verification Date",
            "verification_status": "Verification Status",
            "remarks": "Remarks"
        }

        export_df = df.rename(columns=col_mapping)
        
        # Ensure all master columns exist in order
        for col in MASTER_COLUMNS:
            if col not in export_df.columns:
                export_df[col] = ""
        export_df = export_df[MASTER_COLUMNS]

        # Export CSV
        export_df.to_csv(OUTPUT_MASTER_CSV, index=False, encoding="utf-8-sig")
        logger.info("Exported CSV: %s (Rows: %d)", OUTPUT_MASTER_CSV, len(export_df))

        # Export Excel
        export_df.to_excel(OUTPUT_MASTER_XLSX, index=False, engine="openpyxl")
        logger.info("Exported XLSX: %s (Rows: %d)", OUTPUT_MASTER_XLSX, len(export_df))

    def export_verification_report(self):
        """Exports verification_report.xlsx with audit log."""
        with self.db.get_connection() as conn:
            query = """
            SELECT 
                i.institution_id AS "Institution ID",
                i.name AS "Institution Name",
                i.education_level AS "Education Level",
                i.state AS "State",
                i.district AS "District",
                i.official_institution_id AS "Official ID",
                i.verification_status AS "Verification Status",
                i.recognition_authority AS "Recognition Authority",
                i.approval_authority AS "Approval Authority",
                v.rule_name AS "Verification Rule Applied",
                v.evidence AS "Statutory Evidence / Audit Findings",
                v.verified_at AS "Verification Timestamp"
            FROM institutions i
            LEFT JOIN verification v ON i.institution_id = v.institution_id
            ORDER BY i.state, i.district, i.name;
            """
            df = pd.read_sql_query(query, conn)

        with pd.ExcelWriter(OUTPUT_VERIFICATION_REPORT, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Verification Audit", index=False)
            
            # Summary sheet by verification status
            if not df.empty:
                summary = df.groupby(["Education Level", "Verification Status"]).size().reset_index(name="Count")
                summary.to_excel(writer, sheet_name="Status Summary", index=False)
                
        logger.info("Exported Verification Report: %s", OUTPUT_VERIFICATION_REPORT)

    def export_data_quality_report(self):
        """Exports comprehensive data_quality_report.xlsx."""
        with self.db.get_connection() as conn:
            df = pd.read_sql_query("SELECT * FROM institutions;", conn)
            runs_df = pd.read_sql_query("SELECT * FROM collection_runs;", conn)

        total_inst = len(df)
        
        metrics = [
            {"Metric": "Total institutions", "Value": total_inst},
            {"Metric": "Unique Official IDs", "Value": df["official_institution_id"].replace("", None).nunique() if not df.empty else 0},
            {"Metric": "Missing names", "Value": (df["name"].isna() | (df["name"] == "")).sum() if not df.empty else 0},
            {"Metric": "Missing addresses", "Value": (df["full_address"].isna() | (df["full_address"] == "")).sum() if not df.empty else 0},
            {"Metric": "Missing state", "Value": (df["state"].isna() | (df["state"] == "")).sum() if not df.empty else 0},
            {"Metric": "Missing district", "Value": (df["district"].isna() | (df["district"] == "")).sum() if not df.empty else 0},
            {"Metric": "Missing official ID", "Value": (df["official_institution_id"].isna() | (df["official_institution_id"] == "")).sum() if not df.empty else 0},
            {"Metric": "Missing website", "Value": (df["website"].isna() | (df["website"] == "")).sum() if not df.empty else 0},
            {"Metric": "Missing phone", "Value": (df["phone"].isna() | (df["phone"] == "")).sum() if not df.empty else 0},
            {"Metric": "Missing email", "Value": (df["email"].isna() | (df["email"] == "")).sum() if not df.empty else 0},
            {"Metric": "Verified institutions", "Value": (df["verification_status"] == "VERIFIED").sum() if not df.empty else 0},
            {"Metric": "Partially Verified institutions", "Value": (df["verification_status"] == "PARTIALLY VERIFIED").sum() if not df.empty else 0},
            {"Metric": "Needs Verification institutions", "Value": (df["verification_status"] == "NEEDS VERIFICATION").sum() if not df.empty else 0},
            {"Metric": "De-recognised institutions", "Value": (df["verification_status"] == "DE-RECOGNISED").sum() if not df.empty else 0},
            {"Metric": "Closed/inactive institutions", "Value": (df["verification_status"] == "CLOSED/INACTIVE").sum() if not df.empty else 0},
            {"Metric": "Duplicate entities resolved", "Value": (df["verification_status"] == "DUPLICATE").sum() if not df.empty else 0},
            {"Metric": "Failed source requests", "Value": (runs_df["status"] == "FAILED").sum() if not runs_df.empty else 0},
        ]

        overview_df = pd.DataFrame(metrics)

        with pd.ExcelWriter(OUTPUT_QUALITY_REPORT, engine="openpyxl") as writer:
            overview_df.to_excel(writer, sheet_name="Quality Overview", index=False)
            
            if not df.empty:
                # By Education Level
                by_level = df.groupby("education_level").size().reset_index(name="Total Institutions")
                by_level.to_excel(writer, sheet_name="By Education Level", index=False)

                # By Institution Type
                by_type = df.groupby("institution_type").size().reset_index(name="Total Institutions")
                by_type.to_excel(writer, sheet_name="By Institution Type", index=False)

                # By State & District
                by_state_dist = df.groupby(["state", "district"]).size().reset_index(name="Total Institutions")
                by_state_dist.to_excel(writer, sheet_name="By State & District", index=False)

        logger.info("Exported Data Quality Report: %s", OUTPUT_QUALITY_REPORT)

    def export_state_summary(self):
        """Exports state_summary.xlsx."""
        with self.db.get_connection() as conn:
            df = pd.read_sql_query("SELECT * FROM institutions;", conn)

        with pd.ExcelWriter(OUTPUT_STATE_SUMMARY, engine="openpyxl") as writer:
            if not df.empty:
                state_pivot = pd.pivot_table(
                    df,
                    index="state",
                    columns="education_level",
                    values="institution_id",
                    aggfunc="count",
                    fill_value=0
                )
                state_pivot["Total"] = state_pivot.sum(axis=1)
                state_pivot.reset_index().to_excel(writer, sheet_name="State vs Level", index=False)

                # State verification breakdown
                verif_pivot = pd.pivot_table(
                    df,
                    index="state",
                    columns="verification_status",
                    values="institution_id",
                    aggfunc="count",
                    fill_value=0
                )
                verif_pivot["Total"] = verif_pivot.sum(axis=1)
                verif_pivot.reset_index().to_excel(writer, sheet_name="State vs Verification", index=False)
            else:
                pd.DataFrame({"Message": ["No data available"]}).to_excel(writer, sheet_name="Summary", index=False)

        logger.info("Exported State Summary: %s", OUTPUT_STATE_SUMMARY)

    def export_source_summary(self):
        """Exports source_summary.xlsx."""
        with self.db.get_connection() as conn:
            df = pd.read_sql_query("SELECT * FROM institutions;", conn)
            runs_df = pd.read_sql_query("SELECT * FROM collection_runs;", conn)

        with pd.ExcelWriter(OUTPUT_SOURCE_SUMMARY, engine="openpyxl") as writer:
            if not df.empty:
                src_df = df.groupby(["source_database", "recognition_authority"]).agg(
                    Total_Records=("institution_id", "count"),
                    Verified_Count=("verification_status", lambda s: (s == "VERIFIED").sum()),
                    Partially_Verified=("verification_status", lambda s: (s == "PARTIALLY VERIFIED").sum()),
                    States_Covered=("state", "nunique"),
                    Districts_Covered=("district", "nunique")
                ).reset_index()
                src_df.to_excel(writer, sheet_name="Source Summary", index=False)
            else:
                pd.DataFrame({"Message": ["No data available"]}).to_excel(writer, sheet_name="Source Summary", index=False)

            if not runs_df.empty:
                runs_df.to_excel(writer, sheet_name="Collection Runs Checkpoint", index=False)

        logger.info("Exported Source Summary: %s", OUTPUT_SOURCE_SUMMARY)
