import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
sys.path.insert(0, project_root)

# Try importing the filters
try:
    from app.filters import time_ago, datetimeformat
    print("Successfully imported filters:")
    print(f"- time_ago: {time_ago.__module__}.{time_ago.__name__}")
    print(f"- datetimeformat: {datetimeformat.__module__}.{datetimeformat.__name__}")
    print("\nFilters are working correctly!")
except ImportError as e:
    print(f"Error importing filters: {e}")
    print("\nPython path:")
    for path in sys.path:
        print(f"- {path}")
