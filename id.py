import requests
import json
import argparse
import sys


def get_id_token(email: str, password: str, api_key: str) -> str:
    """
    Authenticate with Firebase and return the ID token.

    Args:
        email: User's email address
        password: User's password
        api_key: Your Firebase Web API key

    Returns:
        ID token string

    Raises:
        Exception: If authentication fails
    """
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"

    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }

    response = requests.post(url, json=payload)
    data = response.json()

    if not response.ok:
        error_message = data.get("error", {}).get("message", "Unknown error")
        raise Exception(f"Authentication failed: {error_message}")

    return data["idToken"]


def main():
    parser = argparse.ArgumentParser(description="Get Firebase ID token")
    parser.add_argument("--email", required=True, help="Firebase user email")
    parser.add_argument("--password", required=True, help="Firebase user password")
    parser.add_argument("--api-key", required=True, help="Firebase Web API key")

    args = parser.parse_args()

    try:
        token = get_id_token(args.email, args.password, args.api_key)
        print(token)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()