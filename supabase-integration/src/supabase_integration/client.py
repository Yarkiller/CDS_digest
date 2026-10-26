"""Supabase client factories — construct only from composition, never use-cases."""

from __future__ import annotations

from supabase import Client, create_client


def create_publishable_client(url: str, key: str) -> Client:
    """Browser-safe publishable/anon key client (no service_role)."""
    return create_client(url, key)


def create_service_role_client(url: str, key: str) -> Client:
    """Privileged service_role client for RLS-bypass writes (activity_events, profiles)."""
    return create_client(url, key)
