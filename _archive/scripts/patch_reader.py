import re

path = '/Users/njasm/Njasm/AI/DSA-Practice/webapp/static/reader.js'
with open(path, 'r') as f:
    content = f.read()

api_module = """  api: {
    hash: 'apis', nav: 'navApis', name: 'API Technologies', noun: 'technologies', motif: 'api',
    list: '/api/apis', doc: '/api/apis-doc',
    tagline: 'Deep dives, architectures, and masterclasses on REST, GraphQL, gRPC, WebSockets, and Protocol Buffers.',
    group: it => it.id.split('_')[0],
    label: it => it.id.split('_')[0],
    kicker: it => `API Technology · ${it.id.split('_')[0]}`,
  },
"""

content = content.replace('const MODULES = {\n', 'const MODULES = {\n' + api_module)

with open(path, 'w') as f:
    f.write(content)
