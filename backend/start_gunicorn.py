#!/usr/bin/env python3
import os
import sys

# Get PORT from environment, default to 8080
port = os.environ.get('PORT', '8080')

# Build gunicorn command
cmd = f"gunicorn -w 4 -b 0.0.0.0:{port} app:app"

# Execute gunicorn
os.execvp('gunicorn', ['gunicorn', '-w', '4', '-b', f'0.0.0.0:{port}', 'app:app'])
