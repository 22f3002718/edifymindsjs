import sys
print("Importing magic...")
try:
    import magic
    print("✅ Magic imported successfully!")
except ImportError as e:
    print(f"❌ Failed to import magic: {e}")
except Exception as e:
    print(f"❌ Crash during import: {e}")
