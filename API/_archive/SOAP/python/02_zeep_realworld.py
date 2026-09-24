# REAL-WORLD EXAMPLE: zeep (External 1)
# Demonstrates: WSDL parsing, WS-Security Headers, Complex Types
from zeep import Client
from zeep.wsse.username import UsernameToken
from zeep.transports import Transport
import requests

# 1. Custom transport for timeouts and SSL config in enterprise environments
session = requests.Session()
session.verify = False # Ignore self-signed certs in legacy systems
transport = Transport(session=session, timeout=10)

# 2. Load WSDL
wsdl = 'http://www.dataaccess.com/webservicesserver/numberconversion.wso?WSDL'

# 3. Add WS-Security Headers (Required by most Enterprise SOAP services)
# client = Client(wsdl=wsdl, transport=transport, wsse=UsernameToken('admin', 'password123'))
client = Client(wsdl=wsdl, transport=transport)

# 4. Call Service Method
try:
    result = client.service.NumberToWords(ubiNum=500)
    print(f"Enterprise SOAP response: {result}")
except Exception as e:
    print(f"SOAP Fault: {e}")
