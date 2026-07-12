
import requests
import base64
from nacl import encoding, public
import os
import sys

def encrypt(public_key: str, secret_value: str) -> str:
    """Encrypt a Unicode string using the public key."""
    public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")

def set_secret(owner, repo, token, secret_name, secret_value):
    # 1. Get the public key
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/public-key"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to get public key: {response.text}")
        return False
    
    key_data = response.json()
    public_key = key_data["key"]
    key_id = key_data["key_id"]
    
    # 2. Encrypt the secret
    encrypted_value = encrypt(public_key, secret_value)
    
    # 3. Create or update the secret
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/{secret_name}"
    data = {
        "encrypted_value": encrypted_value,
        "key_id": key_id,
    }
    response = requests.put(url, headers=headers, json=data)
    if response.status_code in [201, 204]:
        print(f"Successfully set secret: {secret_name}")
        return True
    else:
        print(f"Failed to set secret {secret_name}: {response.text}")
        return False

if __name__ == "__main__":
    GITHUB_TOKEN = "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"
    OWNER = "ram133"
    REPO = "cross-post-automation"
    
    secrets = {
        "TELEGRAM_BOT_TOKEN": "7464269358:AAEcUuwyX77QOAh6i_NJyPcYfNfhLreu3Lw",
        "TELEGRAM_CHAT_ID": "7372546657"
    }
    
    for name, value in secrets.items():
        set_secret(OWNER, REPO, GITHUB_TOKEN, name, value)
