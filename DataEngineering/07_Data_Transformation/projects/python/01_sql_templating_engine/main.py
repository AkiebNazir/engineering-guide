from jinja2 import Template

sql_template = """
SELECT
    {{ ', '.join(columns) }}
FROM {{ table_name }}
WHERE {% for condition in conditions %}
    {{ condition }}{% if not loop.last %} AND {% endif %}
{% endfor %}
"""

template = Template(sql_template)
query = template.render(
    columns=['id', 'name', 'amount'],
    table_name='raw_transactions',
    conditions=['amount > 100', "status = 'completed'"]
)

print("Generated SQL:")
print(query)
