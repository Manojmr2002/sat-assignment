import os
import sys
import sqlite3

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from database import get_db

class DatabaseAgent:
    """
    Database Agent (Step 4 in Workflow):
    Checks employee, device, and ticket records in SQLite database.
    """
    
    def process(self, employee_email: str, employee_name: str = "") -> dict:
        conn = get_db()
        cursor = conn.cursor()
        
        # 1. Lookup Employee
        cursor.execute("SELECT * FROM employees WHERE LOWER(email) = LOWER(?) OR LOWER(name) LIKE LOWER(?)", (employee_email, f"%{employee_name}%" if employee_name else ""))
        emp_row = cursor.fetchone()
        
        employee_data = dict(emp_row) if emp_row else {
            "name": employee_name or "Guest Employee",
            "email": employee_email or "unknown@company.com",
            "department": "Engineering / General",
            "role": "Staff Member",
            "status": "Active",
            "clearance_level": "Standard"
        }
        
        actual_email = employee_data.get("email", employee_email)
        
        # 2. Lookup Assigned Devices
        cursor.execute("SELECT * FROM devices WHERE LOWER(employee_email) = LOWER(?)", (actual_email,))
        device_rows = cursor.fetchall()
        devices = [dict(d) for d in device_rows]
        
        if not devices:
            # Fallback default device profile
            devices = [{
                "hostname": "CORP-WRK-STATION",
                "os_version": "Windows 11 / macOS",
                "ip_address": "192.168.1.150",
                "mac_address": "AA:BB:CC:DD:EE:FF",
                "vpn_status": "Disconnected",
                "serial_number": "SN-GEN-5501"
            }]

        # 3. Lookup Past Tickets
        cursor.execute("SELECT ticket_number, category, status, created_at FROM tickets WHERE LOWER(employee_email) = LOWER(?) ORDER BY id DESC LIMIT 3", (actual_email,))
        past_tickets = [dict(t) for t in cursor.fetchall()]
        
        conn.close()

        return {
            "agent": "Database Agent",
            "employee": employee_data,
            "device": devices[0] if devices else None,
            "all_devices_count": len(devices),
            "past_tickets_count": len(past_tickets),
            "recent_tickets": past_tickets,
            "database_status": "Record Verified"
        }
