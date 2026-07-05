from passlib.context import CryptContext
import getpass
import secrets
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

username = input("Enter admin username: ")
password = getpass.getpass("Enter admin password: ")
confirm = getpass.getpass("Confirm password: ")

if password != confirm:
    print("Passwords don't match!")
    exit(1)

hashed = pwd_context.hash(password)
jwt_secret = secrets.token_hex(32)

env_path = os.path.join(os.path.dirname(__file__), "..", ".env")

if os.path.exists(env_path):
    with open(env_path, "r") as f:
        lines = [l for l in f.readlines()
                 if not l.startswith(("ADMIN_USERNAME=", "ADMIN_PASSWORD_HASH=", "JWT_SECRET="))]
else:
    lines = []

with open(env_path, "w") as f:
    f.writelines(lines)
    if lines and not lines[-1].endswith("\n"):
        f.write("\n")
    f.write(f"ADMIN_USERNAME={username}\n")
    f.write(f"ADMIN_PASSWORD_HASH={hashed}\n")
    f.write(f"JWT_SECRET={jwt_secret}\n")

print("Admin credentials saved to .env")
