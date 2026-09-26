import logging
from datetime import datetime, date
from sqlalchemy import create_engine, Column, Integer, String, Date, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

class DimCustomer(Base):
    """
    SCD Type 2 Dimension Table.
    Tracks historical changes using start_date, end_date, and is_current flag.
    """
    __tablename__ = 'dim_customer'
    
    surrogate_key = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(50), nullable=False) # Natural/Business Key
    name = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    
    # SCD Type 2 tracking columns
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_current = Column(Boolean, nullable=False, default=True)

def apply_scd2_update(session, customer_id: str, new_name: str, new_city: str, effective_date: date):
    """
    Applies an SCD Type 2 update by closing out the current record
    and inserting a new current record.
    """
    # 1. Find the current active record
    current_record = session.query(DimCustomer).filter_by(
        customer_id=customer_id, 
        is_current=True
    ).first()

    if current_record:
        # Step A: Close the old record
        current_record.end_date = effective_date
        current_record.is_current = False
        session.add(current_record)

    # Step B: Insert the new active record
    new_record = DimCustomer(
        customer_id=customer_id,
        name=new_name,
        city=new_city,
        start_date=effective_date,
        end_date=date(9999, 12, 31),
        is_current=True
    )
    session.add(new_record)

def main():
    DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(DATABASE_URL, echo=False)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. Initial State: Customer lives in Chicago
        initial_date = date(2023, 1, 1)
        apply_scd2_update(session, 'C1', 'Bob Jones', 'Chicago', initial_date)
        session.commit()
        
        logger.info("--- Initial State ---")
        for rec in session.query(DimCustomer).all():
            logger.info(f"SK: {rec.surrogate_key} | ID: {rec.customer_id} | City: {rec.city} | Current: {rec.is_current} | {rec.start_date} to {rec.end_date}")
        
        # 2. Update (SCD Type 2 Event): Customer moves to Seattle
        update_date = date(2023, 6, 15)
        apply_scd2_update(session, 'C1', 'Bob Jones', 'Seattle', update_date)
        session.commit()
        
        logger.info("\n--- After SCD Type 2 Update (Moved to Seattle) ---")
        for rec in session.query(DimCustomer).all():
            logger.info(f"SK: {rec.surrogate_key} | ID: {rec.customer_id} | City: {rec.city} | Current: {rec.is_current} | {rec.start_date} to {rec.end_date}")

    except Exception as e:
        session.rollback()
        logger.error(f"Failed to process SCD2 event: {e}")
    finally:
        session.close()

if __name__ == '__main__':
    main()
