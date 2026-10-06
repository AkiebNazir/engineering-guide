# BASIC EXAMPLE: Python Inbuilt urllib + xml.etree
# Demonstrates raw XML Envelope construction and HTTP POST
import urllib.request
import xml.etree.ElementTree as ET

url = "http://www.dataaccess.com/webservicesserver/numberconversion.wso"

# Construct the raw XML SOAP Envelope
soap_body = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <NumberToWords xmlns="http://www.dataaccess.com/webservicesserver/">
      <ubiNum>500</ubiNum>
    </NumberToWords>
  </soap:Body>
</soap:Envelope>"""

req = urllib.request.Request(url, data=soap_body.encode("utf-8"), headers={
    "Content-Type": "text/xml; charset=utf-8"
})

response = urllib.request.urlopen(req)
root = ET.fromstring(response.read())

# Parse XML namespaces
ns = {'m': 'http://www.dataaccess.com/webservicesserver/'}
result = root.find('.//m:NumberToWordsResult', ns).text

print(f"Result from SOAP service: {result}")
