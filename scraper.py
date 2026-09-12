"""
Pan-India Educational Institution Data Collection System - Master CLI.
"""
import argparse
import sys
from typing import Optional
from src.database import Database
from src.checkpoint import CheckpointManager
from src.deduplicator import Deduplicator
from src.verifier import Verifier
from src.exporter import Exporter
from src.logger import logger
from src.sources.udise import UDISECollector
from src.sources.aishe import AISHECollector
from src.sources.ugc import UGCCollector
from src.sources.aicte import AICTECollector
from src.sources.nmc import NMCCollector
from src.sources.ncte import NCTECollector
from src.sources.bci import BCICollector
from src.pan_india_builder import PanIndiaBuilder

def main():
    parser = argparse.ArgumentParser(
        description="PAN-INDIA EDUCATIONAL INSTITUTION DATA COLLECTION SYSTEM",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "--category",
        choices=["schools", "higher_education", "universities", "technical", "medical", "teacher_education", "law", "all"],
        default="all",
        help="Category of educational institutions to collect (default: all)"
    )
    parser.add_argument(
        "--state",
        type=str,
        default=None,
        help="Target State / UT name (e.g. TELANGANA, 'ANDHRA PRADESH', DELHI)"
    )
    parser.add_argument(
        "--district",
        type=str,
        default=None,
        help="Target District name (e.g. KHAMMAM)"
    )
    parser.add_argument(
        "--all-india",
        action="store_true",
        help="Collect data across all 28 Indian States & 8 Union Territories and generate multi-sheet PAN_INDIA_EDUCATIONAL_INSTITUTIONS.xlsx"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume collection from the last completed checkpoint"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-run and reset all checkpoints"
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Generate all Master Excel, CSV, and Analytical Reports without running new scraping"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Run verification rules engine on existing database records"
    )

    args = parser.parse_args()

    # Initialize Core Systems
    db = Database()
    checkpoint_mgr = CheckpointManager(db)
    deduplicator = Deduplicator(db)
    verifier = Verifier(db)
    exporter = Exporter(db)

    if args.force:
        logger.warning("Force flag supplied. Resetting all checkpoints...")
        checkpoint_mgr.reset_checkpoints()

    # Handle Pan-India Master Run
    if args.all_india:
        logger.info("Triggering Pan-India Complete Multi-State Builder...")
        builder = PanIndiaBuilder(db)
        builder.run_pan_india_collection(force=args.force)
        print_summary(db)
        return

    # Handle Export Only
    if args.export:
        logger.info("Executing Export generation...")
        verifier.verify_all()
        exporter.export_all()
        print_summary(db)
        return

    # Handle Verify Only
    if args.verify_only:
        logger.info("Executing Verification Engine on database...")
        verifier.verify_all()
        exporter.export_all()
        print_summary(db)
        return

    # Initialize Collectors
    udise_col = UDISECollector(db, checkpoint_mgr, deduplicator)
    aishe_col = AISHECollector(db, checkpoint_mgr, deduplicator)
    ugc_col = UGCCollector(db, checkpoint_mgr, deduplicator)
    aicte_col = AICTECollector(db, checkpoint_mgr, deduplicator)
    nmc_col = NMCCollector(db, checkpoint_mgr, deduplicator)
    ncte_col = NCTECollector(db, checkpoint_mgr, deduplicator)
    bci_col = BCICollector(db, checkpoint_mgr, deduplicator)

    cat = args.category.lower()
    state = args.state
    district = args.district

    logger.info("=================================================================")
    logger.info("PAN-INDIA EDUCATIONAL INSTITUTION COLLECTION SYSTEM STARTED")
    logger.info("Category: %s | State: %s | District: %s", cat, state, district)
    logger.info("=================================================================")

    # 1. Schools (UDISE+)
    if cat in ["schools", "all"]:
        udise_col.collect(state=state, district=district, all_india=False)

    # 2. Higher Education (AISHE)
    if cat in ["higher_education", "all"]:
        aishe_col.collect(state=state, all_india=False)

    # 3. Universities (UGC)
    if cat in ["universities", "higher_education", "all"]:
        ugc_col.collect(state=state, all_india=False)

    # 4. Technical Education (AICTE)
    if cat in ["technical", "higher_education", "all"]:
        aicte_col.collect(state=state, all_india=False)

    # 5. Medical Education (NMC)
    if cat in ["medical", "higher_education", "all"]:
        nmc_col.collect(state=state, all_india=False)

    # 6. Teacher Education (NCTE)
    if cat in ["teacher_education", "higher_education", "all"]:
        ncte_col.collect(state=state, all_india=False)

    # 7. Law Education (BCI)
    if cat in ["law", "higher_education", "all"]:
        bci_col.collect(state=state, all_india=False)

    # Post-Collection: Run Verification & Exporter
    logger.info("Running post-collection Verification & Entity Resolution...")
    verifier.verify_all()

    logger.info("Generating Final Deliverable Files...")
    exporter.export_all()

    print_summary(db)

def print_summary(db: Database):
    """Prints terminal summary of collection metrics."""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        total = cursor.execute("SELECT COUNT(*) FROM institutions;").fetchone()[0]
        verified = cursor.execute("SELECT COUNT(*) FROM institutions WHERE verification_status = 'VERIFIED';").fetchone()[0]
        partially = cursor.execute("SELECT COUNT(*) FROM institutions WHERE verification_status = 'PARTIALLY VERIFIED';").fetchone()[0]
        needs = cursor.execute("SELECT COUNT(*) FROM institutions WHERE verification_status = 'NEEDS VERIFICATION';").fetchone()[0]
        derecog = cursor.execute("SELECT COUNT(*) FROM institutions WHERE verification_status = 'DE-RECOGNISED';").fetchone()[0]
        schools = cursor.execute("SELECT COUNT(*) FROM institutions WHERE education_level IN ('Primary', 'Secondary', 'Higher Secondary', 'Pre-primary', 'Upper Primary');").fetchone()[0]
        hei = total - schools
        states_count = cursor.execute("SELECT COUNT(DISTINCT state) FROM institutions;").fetchone()[0]

    print("\n" + "="*70)
    print(" PAN-INDIA COLLECTION & VERIFICATION COMPLETE SUMMARY")
    print("="*70)
    print(f" Total States & UTs Covered:            {states_count} / 36")
    print(f" Total Master Educational Institutions: {total:,}")
    print(f"   |-- School Education Institutions:    {schools:,}")
    print(f"   +-- Higher Education & Professional:   {hei:,}")
    print("\n Verification Status Breakdown:")
    print(f"   |-- VERIFIED:                         {verified:,}")
    print(f"   |-- PARTIALLY VERIFIED:               {partially:,}")
    print(f"   |-- NEEDS VERIFICATION:               {needs:,}")
    print(f"   +-- DE-RECOGNISED:                    {derecog:,}")
    print("\n Master Workbook & Generated Artifacts:")
    print("   -> PAN_INDIA_EDUCATIONAL_INSTITUTIONS.xlsx (36 Sheets - 1 per State/UT)")
    print("   -> data/processed/master_institutions.xlsx")
    print("   -> data/processed/master_institutions.csv")
    print("   -> data/processed/state_collection_log.xlsx")
    print("   -> data/processed/verification_report.xlsx")
    print("   -> data/processed/data_quality_report.xlsx")
    print("   -> data/processed/state_summary.xlsx")
    print("   -> data/processed/source_summary.xlsx")
    print("   -> STATE_ORDER_REPORT.txt")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
