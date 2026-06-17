import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client, Client

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path)

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SECRET_KEY")
publishable_key = os.environ.get("SUPABASE_PUBLISHABLE_KEY")

if not url or not key:
    missing = [
        name
        for name, value in {
            "SUPABASE_URL": url,
            "SUPABASE_SECRET_KEY": key,
        }.items()
        if not value
    ]
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

client: Client = create_client(url, key)
auth_client: Client = create_client(url, publishable_key or key)
