import re

path = '/Users/njasm/Njasm/AI/DSA-Practice/webapp/static/index.html'
with open(path, 'r') as f:
    content = f.read()

content = content.replace('<script src="/viz-algorithms.js"></script>', '<script src="/viz-algorithms.js"></script>\n<script src="/viz-api.js"></script>')

with open(path, 'w') as f:
    f.write(content)
