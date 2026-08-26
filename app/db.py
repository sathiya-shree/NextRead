import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", SUPABASE_ANON_KEY)

# Public client (respects RLS, used for anonymous reads)
public_client: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def client_for_user(access_token: str | None = None) -> Client:
    """
    Returns a Supabase client. If an access_token is provided (from the
    logged-in user's session), requests are made *as that user*, so
    Postgres Row Level Security policies apply correctly.
    """
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    if access_token:
        client.postgrest.auth(access_token)
    return client
