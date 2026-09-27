"""
Run this file to check if your Bob API key is loading correctly.

Usage:
    python check_bob_key.py
"""

from dotenv import load_dotenv
import os

load_dotenv()

key = os.environ.get("BOB_API_KEY")

print("-" * 50)
if key is None:
    print("RESULT: Key NOT found.")
    print("This means either:")
    print("  1. The .env file is not in this same folder, OR")
    print("  2. The .env file is named wrong (e.g. .env.txt), OR")
    print("  3. The line inside it isn't exactly: BOB_API_KEY=yourkey")
else:
    print("RESULT: Key WAS found!")
    print("Value starts with:", repr(key[:10]))
    if key.startswith("\ufeff") or key[0] not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
        print("WARNING: The value has a strange character at the start.")
        print("This usually means the .env file was saved by Notepad with")
        print("a hidden 'BOM' marker. Re-save the file using VS Code")
        print("(or any code editor) instead of Notepad.")
    else:
        print("This looks clean. The key should work in the app now.")
print("-" * 50)
