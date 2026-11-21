from getpass import getpass
from backend.auth import create_worker

username = input("Enter ASHA worker username: ").strip()
password = getpass("Enter password: ")
confirm_password = getpass("Confirm password: ")

if password != confirm_password:
    print("Passwords do not match.")
else:
    try:
        create_worker(username, password)
        print("Worker account created successfully!")
    except ValueError as error:
        print("Error:", error)