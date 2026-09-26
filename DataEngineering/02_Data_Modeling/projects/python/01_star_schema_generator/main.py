import random
import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

class DimProduct(Base):
    __tablename__ = 'dim_product'
    product_id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String, nullable=False)
    category = Column(String, nullable=False)

class DimStore(Base):
    __tablename__ = 'dim_store'
    store_id = Column(Integer, primary_key=True, autoincrement=True)
    store_name = Column(String, nullable=False)
    city = Column(String, nullable=False)

class FactSales(Base):
    __tablename__ = 'fact_sales'
    sale_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('dim_product.product_id'), nullable=False)
    store_id = Column(Integer, ForeignKey('dim_store.store_id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)

    product = relationship("DimProduct")
    store = relationship("DimStore")

def main():
    # Use PostgreSQL in a real-world scenario.
    # We use an in-memory SQLite here for runnable demonstration, 
    # but the SQLAlchemy ORM code is production-ready.
    DATABASE_URL = "sqlite:///:memory:" 
    # e.g., "postgresql+psycopg2://user:password@localhost/data_warehouse"
    
    engine = create_engine(DATABASE_URL, echo=False)
    
    # Create tables
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Insert Dimensions
        p1 = DimProduct(product_name="Laptop", category="Electronics")
        p2 = DimProduct(product_name="Desk", category="Furniture")
        
        s1 = DimStore(store_name="Downtown Tech", city="New York")
        s2 = DimStore(store_name="Suburban Goods", city="Boston")
        
        session.add_all([p1, p2, s1, s2])
        session.flush() # flush to get generated IDs

        # Generate Synthetic Fact Data
        sales = []
        for _ in range(10):
            prod = random.choice([p1, p2])
            store = random.choice([s1, s2])
            qty = random.randint(1, 5)
            amt = qty * (1000.0 if prod.product_id == p1.product_id else 150.0)
            
            sales.append(FactSales(product_id=prod.product_id, store_id=store.store_id, quantity=qty, amount=amt))
        
        session.add_all(sales)
        session.commit()
        logger.info("Star Schema data successfully generated and committed.")

        # Analytical Query Joining Fact and Dimensions
        logger.info("Sample query joining Fact and Dimensions:")
        results = session.query(
            FactSales.sale_id,
            DimProduct.product_name,
            DimStore.store_name,
            FactSales.quantity,
            FactSales.amount
        ).join(DimProduct).join(DimStore).limit(5).all()

        for r in results:
            logger.info(f"Sale ID: {r.sale_id} | Product: {r.product_name} | Store: {r.store_name} | Qty: {r.quantity} | Amt: ${r.amount}")

    except Exception as e:
        session.rollback()
        logger.error(f"Error during database operations: {e}")
    finally:
        session.close()

if __name__ == '__main__':
    main()
