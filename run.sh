#!/bin/bash
set -e
PYTHONPATH=server uvicorn request:app --reload --host 0.0.0.0 --port 8000
