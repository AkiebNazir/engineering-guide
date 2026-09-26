import hashlib
import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, String, DateTime, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

def hash_key(*args):
    """Generates an MD5 hash key for business keys."""
    combined = "|".join([str(arg) for arg in args])
    return hashlib.md5(combined.encode('utf-8')).hexdigest()

# ----------------- HUBS -----------------
class HubCustomer(Base):
    __tablename__ = 'hub_customer'
    customer_hk = Column(String(32), primary_key=True)
    customer_id = Column(String(50), nullable=False, unique=True)
    load_date = Column(DateTime, nullable=False)
    record_source = Column(String(50), nullable=False)

class HubOrder(Base):
    __tablename__ = 'hub_order'
    order_hk = Column(String(32), primary_key=True)
    order_id = Column(String(50), nullable=False, unique=True)
    load_date = Column(DateTime, nullable=False)
    record_source = Column(String(50), nullable=False)

# ----------------- LINKS -----------------
class LinkCustomerOrder(Base):
    __tablename__ = 'link_customer_order'
    link_hk = Column(String(32), primary_key=True)
    customer_hk = Column(String(32), ForeignKey('hub_customer.customer_hk'), nullable=False)
    order_hk = Column(String(32), ForeignKey('hub_order.order_hk'), nullable=False)
    load_date = Column(DateTime, nullable=False)
    record_source = Column(String(50), nullable=False)

    customer = relationship("HubCustomer")
    order = relationship("HubOrder")

# --------------- SATELLITES ---------------
class SatCustomerDetails(Base):
    __tablename__ = 'sat_customer_details'
    customer_hk = Column(String(32), ForeignKey('hub_customer.customer_hk'), nullable=False)
    load_date = Column(DateTime, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(150), nullable=False)
    record_source = Column(String(50), nullable=False)

    # Composite primary key for Satellite to track history
    __table_args__ = (
        PrimaryKeyConstraint('customer_hk', 'load_date'),
    )

    customer = relationship("HubCustomer")

def main():
    # Production Data Vaults are typically on Snowflake, Redshift, or Postgres.
    DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(DATABASE_URL, echo=False)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        ld = datetime.now()
        
        # 1. Insert Hub & Sat for Customer
        cust_id = 'C123'
        c_hk = hash_key(cust_id)
        
        hub_c = HubCustomer(customer_hk=c_hk, customer_id=cust_id, load_date=ld, record_source='CRM_SYS')
        sat_c = SatCustomerDetails(customer_hk=c_hk, load_date=ld, name='Alice Smith', email='alice@example.com', record_source='CRM_SYS')
        session.add_all([hub_c, sat_c])

        # 2. Insert Hub for Order
        ord_id = 'O999'
        o_hk = hash_key(ord_id)
        
        hub_o = HubOrder(order_hk=o_hk, order_id=ord_id, load_date=ld, record_source='ORDER_SYS')
        session.add(hub_o)

        # 3. Insert Link connecting Customer and Order
        l_hk = hash_key(c_hk, o_hk)
        link_co = LinkCustomerOrder(link_hk=l_hk, customer_hk=c_hk, order_hk=o_hk, load_date=ld, record_source='ORDER_SYS')
        session.add(link_co)

        session.commit()
        logger.info("Data Vault Architecture Initialized & Data Inserted.")

        # Reconstruct Business View
        logger.info("Querying Data Vault to reconstruct business view:")
        results = session.query(
            HubCustomer.customer_id,
            SatCustomerDetails.name,
            HubOrder.order_id
        ).select_from(LinkCustomerOrder) \
         .join(HubCustomer, LinkCustomerOrder.customer_hk == HubCustomer.customer_hk) \
         .join(HubOrder, LinkCustomerOrder.order_hk == HubOrder.order_hk) \
         .join(SatCustomerDetails, HubCustomer.customer_hk == SatCustomerDetails.customer_hk) \
         .all()

        for r in results:
            logger.info(f"Customer ID: {r.customer_id} | Name: {r.name} | Order ID: {r.order_id}")

    except Exception as e:
        session.rollback()
        logger.error(f"Error in Data Vault ETL: {e}")
    finally:
        session.close()

if __name__ == '__main__':
    main()
