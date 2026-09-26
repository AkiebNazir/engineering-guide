import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Numeric, Date, ForeignKey, select
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

Base = declarative_base()

# ==========================================
# Schema Definitions (Star Schema)
# ==========================================

class DimDate(Base):
    __tablename__ = 'dim_date'
    
    date_id = Column(Integer, primary_key=True, autoincrement=True)
    full_date = Column(Date, nullable=False, unique=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    day = Column(Integer, nullable=False)

class DimProduct(Base):
    __tablename__ = 'dim_product'
    
    product_id = Column(Integer, primary_key=True)
    product_name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)

class FactSales(Base):
    __tablename__ = 'fact_sales'
    
    sale_id = Column(Integer, primary_key=True, autoincrement=True)
    date_id = Column(Integer, ForeignKey('dim_date.date_id'), nullable=False)
    product_id = Column(Integer, ForeignKey('dim_product.product_id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)

    # Relationships for easier ORM traversal
    date = relationship("DimDate")
    product = relationship("DimProduct")

# ==========================================
# Operations
# ==========================================

def build_and_populate_warehouse(engine):
    """Creates tables and populates them with initial dimensions and facts."""
    logger.info("Creating database schema...")
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    
    with Session() as session:
        try:
            logger.info("Inserting dimension data...")
            # Insert Dimensions
            dt = datetime(2023, 10, 1).date()
            d_date = DimDate(full_date=dt, year=dt.year, month=dt.month, day=dt.day)
            
            d_prod = DimProduct(product_id=101, product_name='Enterprise Database Server', category='Hardware', price=15000.00)
            
            session.add_all([d_date, d_prod])
            session.flush() # Flush to get the auto-generated date_id
            
            logger.info("Inserting fact data...")
            # Insert Facts
            f_sales = FactSales(
                date_id=d_date.date_id, 
                product_id=d_prod.product_id, 
                quantity=3, 
                total_amount=d_prod.price * 3
            )
            session.add(f_sales)
            
            session.commit()
            logger.info("Data committed successfully.")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error populating data warehouse: {e}")
            raise

def analyze_sales(engine):
    """Demonstrates querying the star schema."""
    logger.info("Running analytical query on Star Schema...")
    Session = sessionmaker(bind=engine)
    
    with Session() as session:
        # Constructing the JOIN query using SQLAlchemy 2.0 select syntax
        stmt = (
            select(
                DimDate.full_date,
                DimProduct.product_name,
                FactSales.quantity,
                FactSales.total_amount
            )
            .select_from(FactSales)
            .join(DimDate, FactSales.date_id == DimDate.date_id)
            .join(DimProduct, FactSales.product_id == DimProduct.product_id)
        )
        
        results = session.execute(stmt).fetchall()
        
        print("\n--- Sales Analysis Report ---")
        print(f"{'Date':<15} | {'Product Name':<30} | {'Qty':<5} | {'Total Amount'}")
        print("-" * 75)
        for row in results:
            print(f"{str(row.full_date):<15} | {row.product_name:<30} | {row.quantity:<5} | ${row.total_amount:,.2f}")
        print("-" * 75)

if __name__ == "__main__":
    # In production, this would be a Postgres/Snowflake/Redshift URI
    # e.g. "postgresql://user:pass@host:5432/warehouse"
    db_uri = "sqlite:///:memory:"
    
    # Create SQLAlchemy engine
    engine = create_engine(db_uri, echo=False)
    
    build_and_populate_warehouse(engine)
    analyze_sales(engine)
