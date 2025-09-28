#!/usr/bin/env python3
"""
Debug script to check what routes are registered
"""

import sys
sys.path.append('src')

from src.main import app

def print_routes():
    """Print all registered routes"""
    print("🔍 Registered routes in FastAPI application:")
    print("=" * 50)

    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = list(route.methods)
            print(f"  {methods} {route.path}")
        elif hasattr(route, 'path'):
            print(f"  [INCLUDE] {route.path}")

    print("=" * 50)
    print(f"Total routes: {len(app.routes)}")

if __name__ == "__main__":
    print_routes()