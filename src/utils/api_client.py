import os
import requests

API_BASE = os.getenv("API_BASE", "http://web:8000")


def get_json(path: str, timeout: int = 30):
    """GET request to API"""
    r = requests.get(f"{API_BASE}{path}", timeout=timeout)
    r.raise_for_status()
    return r.json()


def post_json(path: str, timeout: int = 30):
    """POST request to API"""
    r = requests.post(f"{API_BASE}{path}", timeout=timeout)
    r.raise_for_status()
    return r.json()

