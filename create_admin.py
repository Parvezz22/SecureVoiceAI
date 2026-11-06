import re
import getpass

from pwdlib import PasswordHash
from database import initialize_database, create_admin_user


password_hash = PasswordHash.recommended()


def main():
    print("\n===== SecureVoiceAI Admin Setup =====\n")

    initialize_database()

    username = input("Enter admin username: ").strip()

    if not re.fullmatch(r"[a-zA-Z0-9_-]{3,30}", username):
        print("Invalid username. Use 3–30 letters, numbers, underscores or hyphens.")
        return

    password = getpass.getpass("Enter admin password: ")

    if len(password) < 12:
        print("Password must contain at least 12 characters.")
        return

    confirm_password = getpass.getpass("Confirm admin password: ")

    if password != confirm_password:
        print("Passwords do not match.")
        return

    hashed_password = password_hash.hash(password)

    try:
        create_admin_user(username, hashed_password)
        print("\nAdmin account created successfully!")

    except ValueError:
        print("\nAn admin account with this username already exists.")


if __name__ == "__main__":
    main()