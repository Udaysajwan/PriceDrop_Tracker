"""
CLI script to create a proper user account directly in Firebase Firestore.
Usage:
    python create_user.py [email] [password]
Or run interactively:
    python create_user.py
"""

import sys

# Ensure UTF-8 output on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from backend.app.database_firebase import get_firestore_db
from backend.app.repositories.user_repo import user_repo
from backend.app.services.auth_service import hash_password


def main():
    print("========================================")
    print("Firebase User Creator - PriceDrop Tracker")
    print("========================================")

    if len(sys.argv) >= 3:
        email = sys.argv[1].strip()
        password = sys.argv[2]
    else:
        email = input("Enter Email Address: ").strip()
        if not email:
            print("ERROR: Email cannot be empty.")
            return
        password = input("Enter Password: ").strip()
        if not password:
            print("ERROR: Password cannot be empty.")
            return

    # Check if user already exists
    existing = user_repo.get_by_email(email)
    if existing:
        print(f"\nA user with email '{email}' already exists in Firebase.")
        choice = input("Do you want to update/reset their password? (y/N): ").strip().lower()
        if choice == "y":
            hashed = hash_password(password)
            user_repo.collection.document(existing["id"]).update({
                "hashed_password": hashed
            })
            print(f"Successfully updated password for '{email}' in Firebase!")
        else:
            print("Operation cancelled.")
        return

    # Create new user in Firebase
    hashed = hash_password(password)
    new_user = user_repo.create(email, hashed)

    print("\nUser Created Successfully in Firebase!")
    print(f"- Email:      {new_user['email']}")
    print(f"- User ID:    {new_user['id']}")
    print(f"- Status:     Active")
    print(f"- Database:   Cloud Firestore ('users' collection)")
    print("\nYou can now log in on your web app with these credentials!")


if __name__ == "__main__":
    main()
