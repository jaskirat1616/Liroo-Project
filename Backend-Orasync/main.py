#!/usr/bin/env python3
"""
Main entry point for Google Cloud Run deployment
"""

import os
from backend import app

if __name__ == "__main__":
    # Get port from environment variable (Cloud Run sets PORT)
    port = int(os.environ.get("PORT", 8080))
    
    # Run the Flask app
    app.run(host="0.0.0.0", port=port, debug=False) 