
from backend.auth import approve_worker, list_pending_workers

print("\nPending ASHA Worker Accounts:")

workers = list_pending_workers()

if not workers:
    print("No pending accounts.")
else:
    for worker in workers:
        print(f"Username: {worker['username']}")

    username = input("\nEnter username to approve: ").strip()

    try:
        approve_worker(username)
        print("Worker account approved successfully!")
    except ValueError as error:
        print("Error:", error)
