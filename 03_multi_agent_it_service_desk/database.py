import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'it_service_desk.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize SQLite tables and seed demo data."""
    conn = get_db()
    cursor = conn.cursor()

    # 1. Employees Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        department TEXT NOT NULL,
        role TEXT NOT NULL,
        status TEXT DEFAULT 'Active',
        clearance_level TEXT DEFAULT 'Standard'
    )
    """)

    # 2. Devices Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_email TEXT NOT NULL,
        hostname TEXT NOT NULL,
        os_version TEXT NOT NULL,
        ip_address TEXT,
        mac_address TEXT,
        vpn_status TEXT DEFAULT 'Disconnected',
        serial_number TEXT,
        FOREIGN KEY (employee_email) REFERENCES employees(email)
    )
    """)

    # 3. Knowledge Base Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS knowledge_base (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        title TEXT NOT NULL,
        symptoms TEXT NOT NULL,
        troubleshooting_steps TEXT NOT NULL,
        solution_type TEXT DEFAULT 'Self-Service'
    )
    """)

    # 4. Tickets Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_number TEXT UNIQUE NOT NULL,
        employee_name TEXT,
        employee_email TEXT,
        request_text TEXT NOT NULL,
        category TEXT,
        urgency TEXT,
        status TEXT DEFAULT 'OPEN',
        assigned_agent TEXT,
        is_escalated INTEGER DEFAULT 0,
        resolution_notes TEXT,
        agent_trace TEXT,
        created_at TEXT,
        closed_at TEXT
    )
    """)

    conn.commit()

    # Seed Initial Data if empty
    cursor.execute("SELECT COUNT(*) FROM employees")
    if cursor.fetchone()[0] == 0:
        _seed_data(cursor, conn)

    conn.close()

def _seed_data(cursor, conn):
    """Seed initial realistic IT helpdesk data."""
    # Seed Employees
    employees = [
        ("Alex Chen", "alex.chen@company.com", "Engineering", "Senior Backend Engineer", "Active", "High"),
        ("Sarah Jenkins", "sarah.j@company.com", "Marketing", "Content Specialist", "Active", "Standard"),
        ("Michael Ross", "michael.r@company.com", "Sales", "Account Executive", "Active", "Standard"),
        ("Elena Rostova", "elena.r@company.com", "DevOps", "Site Reliability Engineer", "Active", "Admin"),
        ("David Kim", "david.k@company.com", "Finance", "Financial Analyst", "Active", "Confidential")
    ]
    cursor.executemany("INSERT INTO employees (name, email, department, role, status, clearance_level) VALUES (?, ?, ?, ?, ?, ?)", employees)

    # Seed Devices
    devices = [
        ("alex.chen@company.com", "CORP-ENG-ACHEN", "macOS Sonoma 14.4", "192.168.1.105", "3C:22:FB:4A:11:02", "Certificate Expired", "SN-ENG-9041"),
        ("sarah.j@company.com", "CORP-MKT-SJENK", "Windows 11 Pro 23H2", "192.168.1.140", "00:1A:2B:3C:4D:5E", "Connected", "SN-MKT-3310"),
        ("michael.r@company.com", "CORP-SLS-MROSS", "Windows 11 Pro 23H2", "192.168.1.188", "14:2D:27:B1:5C:88", "Disconnected", "SN-SLS-4421"),
        ("elena.r@company.com", "CORP-OPS-EROST", "Ubuntu 22.04 LTS", "192.168.1.99", "70:85:C2:55:1A:30", "Connected", "SN-OPS-1109"),
        ("david.k@company.com", "CORP-FIN-DKIM", "Windows 11 Pro 23H2", "192.168.1.112", "58:94:6B:01:23:45", "Disconnected", "SN-FIN-8812")
    ]
    cursor.executemany("INSERT INTO devices (employee_email, hostname, os_version, ip_address, mac_address, vpn_status, serial_number) VALUES (?, ?, ?, ?, ?, ?, ?)", devices)

    # Seed Knowledge Base
    kb_articles = [
        (
            "Network / VPN",
            "Cisco AnyConnect / GlobalProtect VPN Connection Failure",
            "VPN not connecting, Error 806, Authentication failed, Tunnel timeout",
            "1. Verify internet connection.\n2. In VPN client settings, select gateway: vpn.corp.internal.\n3. Verify multi-factor authentication prompt on Authenticator app.\n4. If certificate error, renew user certificate from https://cert.corp.internal/renew.\n5. Flush DNS cache via `ipconfig /flushdns`.",
            "Self-Service"
        ),
        (
            "Software & Access",
            "Jira / Confluence Access Request & Permissions",
            "Access denied to project board, 403 Forbidden on Confluence space",
            "1. Check if user is assigned to the 'Dev-Core' or 'Product-Org' Okta group.\n2. Submit an automated manager approval token.\n3. Once approved, session refreshes automatically in 15 minutes.",
            "Self-Service"
        ),
        (
            "Hardware / System",
            "Laptop Screen Flickering or BSOD (Blue Screen)",
            "System crashes, blue screen error CRITICAL_PROCESS_DIED, display artifacts",
            "1. Disconnect external monitors and docks.\n2. Reboot in Safe Mode and inspect dump logs in C:\\Windows\\Minidump.\n3. Reinstall GPU display driver.\n4. If hardware component failure, schedule Tier-2 hardware swap.",
            "Requires Escalation"
        ),
        (
            "Security / Identity",
            "Password Reset & Okta MFA Token Resync",
            "Locked account, phone changed, MFA push notifications not arriving",
            "1. Navigate to self-service reset portal https://auth.corp.internal/reset.\n2. Provide recovery security code sent to backup mobile number.\n3. Reset password meeting corporate 14-character complexity requirements.",
            "Self-Service"
        )
    ]
    cursor.executemany("INSERT INTO knowledge_base (category, title, symptoms, troubleshooting_steps, solution_type) VALUES (?, ?, ?, ?, ?)", kb_articles)
    
    conn.commit()

# Run init on import
init_db()
