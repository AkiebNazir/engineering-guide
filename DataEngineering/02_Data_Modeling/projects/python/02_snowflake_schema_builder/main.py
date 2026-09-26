import logging
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

class DimCountry(Base):
    __tablename__ = 'dim_country'
    country_id = Column(Integer, primary_key=True, autoincrement=True)
    country_name = Column(String, nullable=False)

class DimState(Base):
    __tablename__ = 'dim_state'
    state_id = Column(Integer, primary_key=True, autoincrement=True)
    state_name = Column(String, nullable=False)
    country_id = Column(Integer, ForeignKey('dim_country.country_id'), nullable=False)
    
    country = relationship("DimCountry")

class DimCity(Base):
    __tablename__ = 'dim_city'
    city_id = Column(Integer, primary_key=True, autoincrement=True)
    city_name = Column(String, nullable=False)
    state_id = Column(Integer, ForeignKey('dim_state.state_id'), nullable=False)

    state = relationship("DimState")

class DimStore(Base):
    __tablename__ = 'dim_store'
    store_id = Column(Integer, primary_key=True, autoincrement=True)
    store_name = Column(String, nullable=False)
    city_id = Column(Integer, ForeignKey('dim_city.city_id'), nullable=False)

    city = relationship("DimCity")

class FactSales(Base):
    __tablename__ = 'fact_sales'
    sale_id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(Integer, ForeignKey('dim_store.store_id'), nullable=False)
    amount = Column(Float, nullable=False)

    store = relationship("DimStore")

def main():
    # Production configurations would use a robust RDBMS like PostgreSQL or Snowflake via SQLAlchemy dialects.
    DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(DATABASE_URL, echo=False)
    
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Hierarchical insertion for Snowflake Schema
        country = DimCountry(country_name="USA")
        session.add(country)
        session.flush()

        state = DimState(state_name="New York", country_id=country.country_id)
        session.add(state)
        session.flush()

        city = DimCity(city_name="NYC", state_id=state.state_id)
        session.add(city)
        session.flush()

        store = DimStore(store_name="NYC Flagship", city_id=city.city_id)
        session.add(store)
        session.flush()

        sale = FactSales(store_id=store.store_id, amount=500.0)
        session.add(sale)
        
        session.commit()
        logger.info("Snowflake Schema Data Generated.")

        # Query across snowflake relationships
        logger.info("Querying across the snowflake relationships:")
        results = session.query(
            FactSales.sale_id,
            DimStore.store_name,
            DimCity.city_name,
            DimState.state_name,
            DimCountry.country_name,
            FactSales.amount
        ).join(DimStore).join(DimCity).join(DimState).join(DimCountry).all()

        for r in results:
            logger.info(f"Sale: {r.sale_id} | Store: {r.store_name} | Location: {r.city_name}, {r.state_name}, {r.country_name} | Amt: ${r.amount}")

    except Exception as e:
        session.rollback()
        logger.error(f"Transaction failed: {e}")
    finally:
        session.close()

if __name__ == '__main__':
    main()
