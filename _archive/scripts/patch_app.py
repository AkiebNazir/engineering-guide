import re

path = '/Users/njasm/Njasm/AI/DSA-Practice/webapp/static/app.js'
with open(path, 'r') as f:
    content = f.read()

content = content.replace(
    "const SECTIONS = ['dsa', 'sd', 'swd', 'go', 'py', 'roadmap', 'library', 'agentic', 'csfund', 'behavioral'];",
    "const SECTIONS = ['dsa', 'sd', 'swd', 'go', 'py', 'roadmap', 'library', 'agentic', 'csfund', 'behavioral', 'api'];"
)

icon_patch = """  behavioral: '<circle cx="12" cy="7" r="4"/><path d="M5 22v-2a7 7 0 0114 0v2"/>',
  api: '<path d="M12 2v20M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/>',"""
content = content.replace("  behavioral: '<circle cx=\"12\" cy=\"7\" r=\"4\"/><path d=\"M5 22v-2a7 7 0 0114 0v2\"/>',", icon_patch)

name_patch = """  behavioral: 'Google Behavioral',
  api: 'API Technologies',"""
content = content.replace("  behavioral: 'Google Behavioral',", name_patch)

url_patch = """  behavioral: '#/google-behavioral',
  api: '#/apis',"""
content = content.replace("  behavioral: '#/google-behavioral',", url_patch)

with open(path, 'w') as f:
    f.write(content)
