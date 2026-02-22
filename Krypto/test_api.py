from trading212_client import Trading212Client
c = Trading212Client()
print(f"ACCOUNT_INFO: {c.get_account_info()}")
