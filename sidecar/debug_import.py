import sys
import os

print("="*50)
print("DEBUG IMPORT DIAGNOSTIC")
print("="*50)

print(f"Current Working Directory: {os.getcwd()}")
print(f"Python Executable: {sys.executable}")
print("\nsys.path:")
for p in sys.path:
    print(f"  - {p}")

print("\nAttempting to import 'app'...")
try:
    import app
    print(f"✅ 'app' imported successfully.")
    if hasattr(app, '__file__'):
        print(f"   Location: {app.__file__}")
    else:
        print(f"   Location: (namespace package) {app.__path__}")
        
    print("\nAttempting to import 'app.data'...")
    import app.data
    print(f"✅ 'app.data' imported successfully.")
    if hasattr(app.data, '__file__'):
        print(f"   Location: {app.data.__file__}")
    else:
        print(f"   Location: (namespace package) {app.data.__path__}")

    print("\nAttempting to import 'app.data.database'...")
    import app.data.database
    print(f"✅ 'app.data.database' imported successfully.")
    print(f"   Location: {app.data.database.__file__}")

except ImportError as e:
    print(f"\n❌ IMPORT FAILED: {e}")
except Exception as e:
    print(f"\n❌ UNEXPECTED ERROR: {e}")

print("="*50)
