import sys
import os

# Add sidecar to path
sys.path.append(os.path.abspath("sidecar"))

from app.main import app

print("Registered Routes:")
for route in app.routes:
    if hasattr(route, "methods"):
        print(f"{route.methods} {route.path}")
    else:
        print(f"Route: {route.path}")
