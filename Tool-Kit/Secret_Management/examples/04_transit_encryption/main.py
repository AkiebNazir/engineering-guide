import os
import hvac
import base64

def main():
    client = hvac.Client(url=os.getenv('VAULT_ADDR'), token=os.getenv('VAULT_TOKEN'))
    
    plaintext = "Confidential User Data".encode('utf-8')
    encoded_plaintext = base64.b64encode(plaintext).decode('utf-8')
    
    encrypt_res = client.secrets.transit.encrypt_data(
        name='my-app-key',
        plaintext=encoded_plaintext
    )
    ciphertext = encrypt_res['data']['ciphertext']
    print(f"Ciphertext: {ciphertext}")

    decrypt_res = client.secrets.transit.decrypt_data(
        name='my-app-key',
        ciphertext=ciphertext
    )
    decoded_plaintext = base64.b64decode(decrypt_res['data']['plaintext']).decode('utf-8')
    print(f"Decrypted Data: {decoded_plaintext}")

if __name__ == '__main__':
    main()
