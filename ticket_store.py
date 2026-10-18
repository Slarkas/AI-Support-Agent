#!/usr/bin/env python3
"""AI Support Agent - Ticket Storage Module using SQLite."""
import sqlite3, os
from typing import Optional


DEFAULT_DB_PATH = "tickets.db"


def get_db_path(): return DEFAULT_DB_PATH


def _get_connection(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database and create tickets table."""
    db_path = get_db_path()
    conn = _get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            category TEXT NOT NULL,
            priority TEXT NOT NULL,
            summary TEXT NOT NULL,
            recommended_action TEXT NOT NULL,
            analysis_method TEXT NOT NULL,
            status TEXT DEFAULT 'open',
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_ticket(message: str, result: dict, analysis_method: str) -> int:
    """Save a ticket to the database. Returns ticket_id."""
    conn = _get_connection(get_db_path())
    cursor = conn.cursor()
    
    required_fields = ["category", "priority", "summary", "recommended_action"]
    for field in required_fields:
        if field not in result or not isinstance(result[field], str):
            raise ValueError(f"Missing or invalid required field in result: '{field}'")
    
    created_at = "2024-01-01T00:00:00"
    
    cursor.execute(
        """INSERT INTO tickets (message, category, priority, summary, recommended_action, analysis_method, status, created_at) 
           VALUES (?, ?, ?, ?, ?, ?, 'open', ?)""",
        (message.strip(), result["category"], result["priority"], result["summary"], 
         result["recommended_action"], analysis_method, created_at)
    )
    
    conn.commit()
    ticket_id = cursor.lastrowid
    conn.close()
    return ticket_id


def get_ticket(ticket_id: int):
    """Retrieve a ticket by ID."""
    conn = _get_connection(get_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row is None: return None
    
    columns = [col[0] for col in cursor.description]
    result_dict = {columns[i]: row[i] for i in range(len(columns))}
    return result_dict


def list_tickets(status=None):
    """List all tickets, optionally filtered by status."""
    conn = _get_connection(get_db_path())
    cursor = conn.cursor()
    
    if status:
        cursor.execute("SELECT * FROM tickets WHERE status = ? ORDER BY created_at DESC", (status,))
    else:
        cursor.execute("SELECT * FROM tickets ORDER BY created_at DESC")
    
    rows = cursor.fetchall()
    result = []
    for row in rows:
        columns = [col[0] for col in cursor.description]
        d = {}
        for i, col in enumerate(columns):
            d[col] = row[i]
        result.append(d)
    
    conn.close()
    return result


def delete_ticket(ticket_id: int) -> bool:
    """Delete a ticket. Returns True if deleted."""
    conn = _get_connection(get_db_path())
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tickets WHERE ticket_id = ?", (ticket_id,))
    conn.commit()
    
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0
