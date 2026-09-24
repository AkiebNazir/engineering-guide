# REAL-WORLD EXAMPLE: suds-community (External 2)
# Demonstrates: Factory pattern for creating complex XML objects
from suds.client import Client

url = 'http://www.dataaccess.com/webservicesserver/numberconversion.wso?WSDL'
client = Client(url)

# In real world SOAP, you often need to create complex nested objects.
# Suds provides a factory for this:
# complex_obj = client.factory.create('ns0:ComplexTypeParams')
# complex_obj.Field1 = "Value"
# result = client.service.SomeMethod(complex_obj)

result = client.service.NumberToWords(500)
print(f"Suds parsed response: {result}")
