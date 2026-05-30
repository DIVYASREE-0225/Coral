"""Pytest suite for GigProof.

Run with: ../.coralvenv/bin/pytest backend/tests/ -v

These tests are pure-Python and don't require the `coral` CLI to be installed —
agent tests monkeypatch `coral_sql.query` so unit tests stay fast and
deterministic.
"""
