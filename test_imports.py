#!/usr/bin/env python3

print("Testing imports...")

try:
    import os
    print("✓ os imported")
except Exception as e:
    print(f"✗ os failed: {e}")

try:
    import sys
    print("✓ sys imported")
except Exception as e:
    print(f"✗ sys failed: {e}")

try:
    import flask
    print("✓ flask imported")
except Exception as e:
    print(f"✗ flask failed: {e}")

try:
    import requests
    print("✓ requests imported")
except Exception as e:
    print(f"✗ requests failed: {e}")

try:
    from dotenv import load_dotenv
    print("✓ dotenv imported")
except Exception as e:
    print(f"✗ dotenv failed: {e}")

try:
    from routes.reports import reports_bp
    print("✓ routes.reports imported")
except Exception as e:
    print(f"✗ routes.reports failed: {e}")

try:
    from services.coderabbit import generate_coderabbit_report
    print("✓ services.coderabbit imported")
except Exception as e:
    print(f"✗ services.coderabbit failed: {e}")

try:
    from database.db import init_database
    print("✓ database.db imported")
except Exception as e:
    print(f"✗ database.db failed: {e}")

print("Import test complete!")