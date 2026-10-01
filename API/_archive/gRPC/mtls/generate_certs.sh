#!/bin/bash
# Generate Certificate Authority (CA)
openssl req -x509 -newkey rsa:4096 -days 365 -nodes -keyout ca-key.pem -out ca-cert.pem -subj "/C=US/ST=CA/L=SF/O=MyOrg/CN=MyCA"

# Generate Server Certificate
openssl req -newkey rsa:4096 -nodes -keyout server-key.pem -out server-req.pem -subj "/C=US/ST=CA/L=SF/O=MyOrg/CN=localhost"
openssl x509 -req -in server-req.pem -days 60 -CA ca-cert.pem -CAkey ca-key.pem -CAcreateserial -out server-cert.pem -extfile <(echo "subjectAltName=DNS:localhost,IP:127.0.0.1")

# Generate Client Certificate
openssl req -newkey rsa:4096 -nodes -keyout client-key.pem -out client-req.pem -subj "/C=US/ST=CA/L=SF/O=MyOrg/CN=MyClient"
openssl x509 -req -in client-req.pem -days 60 -CA ca-cert.pem -CAkey ca-key.pem -CAcreateserial -out client-cert.pem
