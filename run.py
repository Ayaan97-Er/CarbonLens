#!/usr/bin/env python3
"""
CarbonLens — Single Command Application Launcher
Starts the FastAPI Backend and serves the complete frontend application at http://127.0.0.1:8000
"""

import sys
import os
import io

# Configure UTF-8 stdout if needed on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Ensure backend directory is on Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

import uvicorn

if __name__ == "__main__":
    print("=" * 70)
    print("CARBONLENS -- Sustainability Intelligence & Carbon Footprint Platform")
    print("=" * 70)
    print("Web Application: http://127.0.0.1:8000")
    print("API Documentation: http://127.0.0.1:8000/docs")
    print("Default Demo User: demo@carbonlens.dev / CarbonLens2026!")
    print("Default Admin:     admin@carbonlens.dev / AdminCarbonLens2026!")
    print("=" * 70)
    
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    print(f"Server binding on http://{host}:{port}")
    uvicorn.run("app.main:app", host=host, port=port, reload=False, app_dir="backend")
