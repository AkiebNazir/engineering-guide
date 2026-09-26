import os
import logging
from typing import List, Dict, Any
from jinja2 import Environment, FileSystemLoader, Template
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

class SQLTemplatingEngine:
    """
    A production-grade SQL templating engine that dynamically generates 
    and executes SQL queries using Jinja2 and SQLAlchemy.
    """
    def __init__(self, db_url: str):
        self.engine: Engine = create_engine(db_url, pool_pre_ping=True, pool_size=5)
        
    def generate_query(self, template_str: str, context: Dict[str, Any]) -> str:
        """Generates a SQL query from a Jinja2 template string."""
        template = Template(template_str)
        return template.render(**context)

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Executes the generated SQL query and returns results as a list of dictionaries."""
        try:
            with self.engine.connect() as connection:
                logger.info(f"Executing Query: {query.strip()}")
                result = connection.execute(text(query))
                
                if result.returns_rows:
                    return [dict(row._mapping) for row in result]
                return []
        except SQLAlchemyError as e:
            logger.error(f"Database execution failed: {e}")
            raise

if __name__ == "__main__":
    db_url = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/analytics_db")
    sql_template = """
    SELECT
        {{ columns | join(', ') }}
    FROM {{ table_name }}
    WHERE {% for condition in conditions %}
        {{ condition }}{% if not loop.last %} AND {% endif %}
    {% endfor %}
    """
    
    context = {
        "columns": ["id", "name", "amount", "transaction_date"],
        "table_name": "raw_transactions",
        "conditions": ["amount > 100", "status = 'completed'"]
    }
    
    templater = SQLTemplatingEngine(db_url)
    try:
        query = templater.generate_query(sql_template, context)
        # Using a try/except for execution to allow it to run without a real DB
        try:
            results = templater.execute_query(query)
            logger.info(f"Retrieved {len(results)} rows.")
        except SQLAlchemyError:
            logger.warning("Could not execute query. Ensure a real database is running.")
    except Exception as e:
        logger.error("Failed to run templated query pipeline.", exc_info=True)
