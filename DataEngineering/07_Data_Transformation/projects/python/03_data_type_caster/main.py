import pandas as pd
import pandera as pa
from pandera.errors import SchemaErrors
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

class TransactionSchema(pa.SchemaModel):
    date_clean: pa.typing.Series[pd.DatetimeTZDtype] = pa.Field(dtype_kwargs={"unit": "ns", "tz": "UTC"})
    price_clean: pa.typing.Series[float] = pa.Field(ge=0.0)
    
    @pa.dataframe_check
    def check_date_validity(cls, df: pd.DataFrame) -> pa.typing.Series[bool]:
        return df["date_clean"] <= pd.Timestamp.utcnow()

class DataTypeCaster:
    """
    Production-grade data type caster using pandas and pandera for schema validation.
    """
    def clean_and_cast(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Starting data cleaning and type casting.")
        
        df = df.copy()
        
        # Clean currency strings and cast to float
        df['price_clean'] = (
            df['price_str']
            .replace(r'[\$,]', '', regex=True)
            .astype(float)
        )
        
        # Cast date strings to UTC datetime
        df['date_clean'] = pd.to_datetime(df['date_str'], utc=True)
        
        try:
            validated_df = TransactionSchema.validate(df)
            logger.info("Data validation and casting passed.")
            return validated_df
        except SchemaErrors as err:
            logger.error("Schema validation failed on casted data.")
            logger.error(err.failure_cases)
            raise

if __name__ == "__main__":
    raw_data = {
        'date_str': ['2023-01-01T12:00:00Z', '2023-02-01T14:30:00Z'],
        'price_str': ['$1,200.50', '$45.00']
    }
    raw_df = pd.DataFrame(raw_data)
    
    caster = DataTypeCaster()
    try:
        clean_df = caster.clean_and_cast(raw_df)
        logger.info(f"\nCleaned DataFrame:\n{clean_df[['date_clean', 'price_clean']]}")
        logger.info(f"\nData Types:\n{clean_df.dtypes}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
