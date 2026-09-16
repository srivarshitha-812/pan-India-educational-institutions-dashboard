import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

def run_tests():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("Navigating to http://127.0.0.1:8000...")
        page.goto("http://127.0.0.1:8000", wait_until="networkidle")
        page.wait_for_timeout(2000)

        # ===================================================================
        # PART 1: PENDING DATASETS VERIFICATION
        # ===================================================================
        print("\n--- PART 1: PENDING DATASETS PAGE ---")
        
        # 1. Sidebar check
        pending_nav = page.locator("#nav-pending")
        nav_text = pending_nav.inner_text()
        print(f"Sidebar Nav Text: {repr(nav_text.strip())}")
        assert "Pending Datasets" in nav_text, "Sidebar does not say 'Pending Datasets'"
        
        badge_count = page.locator("#badge-pending-count").inner_text()
        print(f"Sidebar Badge Count: {repr(badge_count.strip())}")
        assert badge_count.strip() == "7", f"Sidebar badge is '{badge_count}', expected '7'"

        # Navigate to Pending Datasets
        pending_nav.click()
        page.wait_for_timeout(500)

        # 2. Page Title in Top Header
        page_title = page.locator("#page-title").inner_text()
        print(f"Top Header Page Title: {repr(page_title.strip())}")
        assert page_title.strip() == "Pending Datasets", f"Top header title is '{page_title}', expected 'Pending Datasets'"

        # 3. Check for Duplicate Title
        headings_in_pending = page.locator("#view-pending h1, #view-pending h2, #view-pending h3").all_inner_texts()
        print(f"H1/H2/H3 in view-pending: {headings_in_pending}")
        for h in headings_in_pending:
            assert "Pending Datasets" not in h, f"Found duplicate title in view-pending: {h}"
            assert "Dataset Collection Roadmap" not in h, f"Found outdated title in view-pending: {h}"

        # 4. Check Pending Cards Count and Content
        pending_cards = page.locator("#pending-grid .pending-card")
        card_count = pending_cards.count()
        print(f"Pending Portals Count: {card_count}")
        assert card_count == 7, f"Expected 7 pending cards, found {card_count}"

        expected_authorities = [
            "AISHE / Ministry of Education",
            "AICTE",
            "NCTE",
            "NCVET / DGT MIS",
            "Dental Council of India (DCI)",
            "Veterinary Council of India (VCI)",
            "Indian Council of Agricultural Research (ICAR)"
        ]

        for i in range(card_count):
            card = pending_cards.nth(i)
            auth = card.locator(".pending-authority").inner_text()
            title = card.locator(".pending-title").inner_text()
            status_row = card.locator(".pending-status-row").inner_text()
            cleaned_row = status_row.strip().replace("\n", " ")
            print(f"  [{i+1}] {auth} | {title} | {cleaned_row}")
            assert any(ea.lower() in auth.lower() for ea in expected_authorities), f"Unexpected authority: {auth}"
            assert "Count not established" in status_row, f"Card missing 'Count not established': {status_row}"

        # 5. Verify Completed & Integrated Portals is NOT on page
        completed_section = page.locator("#completed-grid")
        assert completed_section.count() == 0, "completed-grid still exists in DOM!"
        body_text_pending = page.locator("#view-pending").inner_text()
        assert "Completed & Integrated Portals" not in body_text_pending, "Completed & Integrated Portals found on Pending page!"
        print("  [OK] Completed & Integrated Portals completely removed from Pending page.")

        # ===================================================================
        # PART 2: STATE / UT EXPLORER MOBILE RESPONSIVENESS
        # ===================================================================
        print("\n--- PART 2: STATE / UT EXPLORER RESPONSIVENESS ---")

        # Navigate to State / UT Explorer
        page.locator("#nav-states").click()
        page.wait_for_timeout(1000)

        # Select a state with diverse sectors e.g. Meghalaya or Telangana or Maharashtra
        page.locator(".state-item", has_text="Meghalaya").click()
        page.wait_for_timeout(1000)

        target_widths = [1366, 768, 480, 414, 390, 375, 320]

        for width in target_widths:
            height = 800 if width > 500 else 700
            page.set_viewport_size({"width": width, "height": height})
            page.wait_for_timeout(500)

            # Check page-wide horizontal overflow
            scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
            client_width = page.evaluate("() => document.documentElement.clientWidth")
            inner_width = page.evaluate("() => window.innerWidth")
            
            print(f"\nTesting Viewport {width}x{height}:")
            print(f"  - document.scrollWidth: {scroll_width}px | clientWidth: {client_width}px | innerWidth: {inner_width}px")
            
            # Check overflow tolerance (max 1px due to rounding/scrollbar)
            assert scroll_width <= width + 1, f"Horizontal page overflow detected at {width}px! scrollWidth={scroll_width}"

            # Check State Header and Badges
            state_header = page.locator(".state-header-banner")
            header_box = state_header.bounding_box()
            print(f"  - State Banner Box: width={header_box['width']}px, fits in viewport={header_box['width'] <= width}")
            assert header_box['width'] <= width, f"State header banner exceeds viewport at {width}px"

            badges = page.locator(".state-meta-badges .kpi-badge")
            for b_idx in range(badges.count()):
                badge_box = badges.nth(b_idx).bounding_box()
                assert badge_box['x'] + badge_box['width'] <= width + 1, f"Badge {b_idx} overflows right edge at {width}px"

            # Check Available Sector Cards
            sector_chips = page.locator("#state-category-chips .category-chip")
            sector_count = sector_chips.count()
            print(f"  - Available Sector Cards ({sector_count} cards):")
            for c_idx in range(sector_count):
                chip = sector_chips.nth(c_idx)
                box = chip.bounding_box()
                assert box['width'] <= width, f"Sector chip {c_idx} width ({box['width']}px) exceeds viewport ({width}px)"
                assert box['x'] + box['width'] <= width + 2, f"Sector chip {c_idx} right edge ({box['x'] + box['width']}px) exceeds viewport"

            # Check Gap message
            missing_chips = page.locator("#state-missing-chips")
            missing_box = missing_chips.bounding_box()
            assert missing_box['x'] + missing_box['width'] <= width + 2, f"Sector gap container overflows at {width}px"

            # Check Institutions Roster container
            roster_wrapper = page.locator(".state-roster-wrapper")
            roster_box = roster_wrapper.bounding_box()
            assert roster_box['x'] + roster_box['width'] <= width + 2, f"Roster wrapper overflows at {width}px"

            # Check Roster Search Box
            search_box = page.locator("#state-inst-search").bounding_box()
            assert search_box['x'] + search_box['width'] <= width + 2, f"Roster search input overflows at {width}px"

            # Check Top Header Elements
            top_header = page.locator(".top-header")
            top_box = top_header.bounding_box()
            assert top_box['width'] <= width + 1, f"Top header width exceeds viewport at {width}px"

            refresh_btn = page.locator("#btn-refresh").bounding_box()
            assert refresh_btn['x'] + refresh_btn['width'] <= width + 1, f"Refresh button overflows header at {width}px"

            print(f"  [OK] Viewport {width}px passed all responsive assertions!")

        # Also test another state with all categories present e.g. Karnataka / Maharashtra
        print("\nTesting State with 9/9 categories (Dynamic Gap Calculation)...")
        page.locator(".state-item", has_text="Maharashtra").click()
        page.wait_for_timeout(1000)
        gap_text = page.locator("#state-missing-chips").inner_text()
        print(f"  Maharashtra Gap Status: {repr(gap_text.strip())}")
        assert "final-list categories have representation" in gap_text, f"Unexpected gap message: {gap_text}"

        # Test search filter on State Institution Roster
        print("\nTesting State Institution Roster search filter...")
        page.locator("#state-inst-search").fill("College")
        page.wait_for_timeout(600)
        roster_rows = page.locator("#state-institutions-body tr").count()
        print(f"  Filtered roster rows for 'College': {roster_rows}")
        assert roster_rows > 0, "Search filter returned 0 rows"

        browser.close()
        print("\n=======================================================")
        print(">>> ALL VALIDATION TESTS PASSED 100%! <<<")
        print("=======================================================")

if __name__ == "__main__":
    run_tests()
