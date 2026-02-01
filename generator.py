import os
import base64

def generate_jwt_secret_key():
    secret_key = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8')
    return secret_key

if __name__ == "__main__":
    print("JWT Secret Key:", generate_jwt_secret_key())