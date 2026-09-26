with open("webapp/static/toolkit-practice.js", "r") as f:
    content = f.read()

content = content.replace("let html = '<div class=\"tk-examples-container\">';", "let html = '<h2>Examples &amp; Exercises</h2><div class=\"tk-examples-container\">';")

with open("webapp/static/toolkit-practice.js", "w") as f:
    f.write(content)
