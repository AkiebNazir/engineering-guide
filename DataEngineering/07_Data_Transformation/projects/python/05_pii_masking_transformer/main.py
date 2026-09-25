import pandas as pd
import hashlib

def mask_email(email):
    parts = email.split('@')
    return f"{parts[0][0]}***@{parts[1]}"

def hash_ssn(ssn):
    return hashlib.sha256(ssn.encode()).hexdigest()

df = pd.DataFrame({
    'user': ['Alice', 'Bob'],
    'email': ['alice@example.com', 'bob@test.com'],
    'ssn': ['123-456-7890', '987-654-3210']
})

df['email_masked'] = df['email'].apply(mask_email)
df['ssn_hashed'] = df['ssn'].apply(hash_ssn)

print("Masked PII Data:")
print(df[['user', 'email_masked', 'ssn_hashed']])
