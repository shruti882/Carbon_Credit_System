from web3 import Web3
from web3.middleware import geth_poa_middleware

# Example of connecting to a local Ethereum node (e.g., Ganache)
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))

# Make sure to use the PoA middleware if you're on a PoA network (like Ganache)
w3.middleware_stack.inject(geth_poa_middleware, layer=0)

# Create a new local Ethereum account
account = w3.eth.account.create()

# Access the private key and address
private_key = account.privateKey
address = account.address

# Print the private key and address (ensure you store the private key securely)
print(f"Address: {address}")
print(f"Private Key: {private_key.hex()}")
