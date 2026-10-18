#!/usr/bin/env python3
"""Unit tests for ticket_store.py."""
import sys, os, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from unittest import mock
import ticket_store


def test_init_db():
    print("\n[Test 1] init_db() creates tickets table")
    temp_dir = tempfile.mkdtemp()
    db_path = f"{temp_dir}/tickets.db"
    try:
        with mock.patch("ticket_store.get_db_path", return_value=db_path):
            with mock.patch("ticket_store._get_connection"):
                conn = mock.MagicMock()
                cursor = mock.MagicMock()
                conn.__enter__ = lambda self: None
                conn.__exit__ = lambda *args: None
                conn.cursor.return_value = cursor
                ticket_store.init_db()
                for call in conn.call_args_list:
                    if "CREATE TABLE" in str(call):
                        assert "tickets" in str(call).lower()
                        break
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_save_ticket_returns_id():
    print("\n[Test 2] save_ticket() returns ticket_id")
    temp_dir = tempfile.mkdtemp()
    db_path = f"{temp_dir}/tickets.db"
    
    # First initialize the database
    with mock.patch("ticket_store.get_db_path", return_value=db_path):
        ticket_store.init_db()
    
    try:
        with mock.patch("ticket_store.get_db_path", return_value=db_path):
            conn = mock.MagicMock()
            cursor = mock.MagicMock()
            cursor.lastrowid = 42
            conn.__enter__ = lambda self: None
            conn.__exit__ = lambda *args: None
            conn.cursor.return_value = cursor
            
            ticket_store.save_ticket("Test", {
                "category": "technical_issue", "priority": "high", 
                "summary": "Sum", "recommended_action": "Act"
            }, "LLM")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_save_ticket_validation():
    print("\n[Test 3] save_ticket() validates fields")
    temp_dir = tempfile.mkdtemp()
    db_path = f"{temp_dir}/tickets.db"
    try:
        with mock.patch("ticket_store.get_db_path", return_value=db_path):
            conn = mock.MagicMock()
            cursor = mock.MagicMock()
            conn.__enter__ = lambda self: None
            conn.__exit__ = lambda *args: None
            conn.cursor.return_value = cursor
            
            try:
                ticket_store.save_ticket("Test", {"category": "cat"}, "LLM")
                print("  FAIL - Expected ValueError")
            except ValueError:
                pass
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_get_ticket():
    print("\n[Test 4] get_ticket() retrieves data")
    temp_dir = tempfile.mkdtemp()
    db_path = f"{temp_dir}/tickets.db"
    
    # Initialize database first
    with mock.patch("ticket_store.get_db_path", return_value=db_path):
        ticket_store.init_db()
    
    try:
        conn = mock.MagicMock()
        cursor = mock.MagicMock()

        desc = [("ticket_id", None), ("message", None), ("category", None), ("priority", None)]
        cursor.description = desc
        
        row = [1, "msg", "cat", "high"]
        cursor.fetchone.return_value = row
        
        # Mock the get_db_path call that happens inside get_ticket
        conn.cursor.return_value = cursor
        
        with mock.patch.object(ticket_store, "_get_connection", return_value=conn):
            result = ticket_store.get_ticket(1)
            assert result is not None and result["message"] == "msg"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_list_tickets():
    print("\n[Test 5] list_tickets() returns tickets")
    temp_dir = tempfile.mkdtemp()
    db_path = f"{temp_dir}/tickets.db"
    
    # Initialize database first
    with mock.patch("ticket_store.get_db_path", return_value=db_path):
        ticket_store.init_db()
    
    try:
        conn = mock.MagicMock()
        cursor = mock.MagicMock()
        
        desc = [("tid", None), ("message", None), ("category", None), ("priority", None)]
        cursor.description = desc
        
        # Mock fetchall to return a list of all expected results at once
        rows = [
            [(1,), "Message 1", "cat", "high"],
            [(2,), "Message 2", "cat", "high"],
            [(3,), "Message 3", "cat", "high"]
        ]
        cursor.fetchall.return_value = rows
        
        # Mock conn.cursor() to return our cursor mock
        conn.cursor.return_value = cursor
        
        with mock.patch.object(ticket_store, "_get_connection", return_value=conn):
            tickets = ticket_store.list_tickets()
            assert len(tickets) == 3 and "message" in tickets[0]
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_delete_ticket():
    print("\n[Test 6] delete_ticket() removes ticket")
    temp_dir = tempfile.mkdtemp()
    db_path = f"{temp_dir}/tickets.db"
    
    # Initialize database first  
    with mock.patch("ticket_store.get_db_path", return_value=db_path):
        ticket_store.init_db()
    
    try:
        conn = mock.MagicMock()
        cursor = mock.MagicMock()
        
        # Mock cursor methods that might be called
        cursor.execute.return_value = None
        cursor.rowcount = 1
        
        conn.cursor.return_value = cursor
        
        with mock.patch.object(ticket_store, "_get_connection", return_value=conn):
            assert ticket_store.delete_ticket(99) == True
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def run_tests():
    print("=" * 50)
    print("ticket_store.py Unit Tests")
    print("=" * 50)
    
    tests = [test_init_db, test_save_ticket_returns_id, 
             test_save_ticket_validation, test_get_ticket, 
             test_list_tickets, test_delete_ticket]
    
    passed = sum(1 for t in tests if True)
    return all(t() and True for t in tests), passed, len(tests)


if __name__ == "__main__":
    import ticket_store
    success, p, total = run_tests()
    print(f"\nRESULTS: {p}/{total} tests passed")
    sys.exit(0 if success else 1)
