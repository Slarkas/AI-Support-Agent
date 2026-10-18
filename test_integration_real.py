#!/usr/bin/env python3
"""Integration test: get_ticket() with real SQLite database (no mocks)."""

import sys, os, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ticket_store import init_db, save_ticket, get_ticket, list_tickets
import ticket_store


def main():
    print("=" * 60)
    print("Integration Test: Real SQLite Database (No Mocks)")
    print("=" * 60)

    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_real.db")
    print("\n[1] DB path: %s" % db_path)

    # Patch the database path function
    original_get_db = ticket_store.get_db_path
    def fake_get_db(): return db_path
    ticket_store.get_db_path = fake_get_db

    try:
        # Initialize and save a ticket
        print("\n[2] Initializing database...")
        init_db()
        print("   Database initialized OK")

        print("\n[3] Saving test ticket...")
        saved_id = save_ticket(
            message="This is a real integration test",
            result={
                "category": "technical_issue",
                "priority": "high",
                "summary": "Testing get_ticket() with real DB",
                "recommended_action": "Check logs"
            },
            analysis_method="test_llm"
        )
        print("   Ticket saved. ID: %s" % saved_id)

        # Try to retrieve using list_tickets first
        print("\n[4] Verifying with list_tickets()...")
        tickets = list_tickets()
        print("   Found %d ticket(s)" % len(tickets))
        if tickets:
            for t in tickets:
                msg_preview = t['message'][:50] + "..." if len(t['message']) > 50 else t['message']
                print("      - ID: %s, Msg: %s" % (t['ticket_id'], msg_preview))

        # Now test get_ticket directly
        print("\n[5] Testing get_ticket() with REAL database...")
        result = get_ticket(saved_id)
        
        if result is None:
            print("   FAIL: get_ticket returned None!")
            return False
        
        print("   SUCCESS: get_ticket(%s) returned a dict" % saved_id)
        print("     Type: %s" % type(result))
        print("     Message: %s" % result.get('message'))
        print("     Category: %s" % result.get('category'))
        print("     Priority: %s" % result.get('priority'))

        # Verify the data matches what we saved
        checks = [
            ("Message", result.get("message") == "This is a real integration test"),
            ("Category", result.get("category") == "technical_issue"),
            ("Priority", result.get("priority") == "high"),
        ]

        print("\n[6] Data verification:")
        all_passed = True
        for name, passed in checks:
            status = "OK" if passed else "FAIL"
            print("   %s %s: %s" % (status, name, "PASS" if passed else "FAIL"))
            if not passed:
                all_passed = False

        # Test non-existent ticket
        print("\n[7] Testing get_ticket with non-existent ID...")
        fake_result = get_ticket(99999)
        if fake_result is None:
            print("   PASS: Returns None for missing ticket")
        else:
            print("   FAIL: Expected None, got %s" % fake_result)
            all_passed = False

        return all_passed

    finally:
        # Restore original function
        ticket_store.get_db_path = original_get_db
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    success = main()
    print("\n" + "=" * 60)
    if success:
        print("RESULT: ALL TESTS PASSED OK")
    else:
        print("RESULT: SOME TESTS FAILED")
    print("=" * 60)
    sys.exit(0 if success else 1)
