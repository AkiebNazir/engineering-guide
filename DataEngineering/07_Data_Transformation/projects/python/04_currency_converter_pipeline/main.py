import os
import requests
import pandas as pd
import logging
from typing import Dict
from tenacity import retry, wait_exponential, stop_after_attempt

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

class CurrencyConverterPipeline:
    """
    A robust currency converter utilizing external APIs for live exchange rates.
    """
    def __init__(self, base_currency: str = "USD"):
        self.base_currency = base_currency
        self.api_key = os.getenv("EXCHANGE_RATE_API_KEY", "demo_key")
        self.api_url = f"https://v6.exchangerate-api.com/v6/{self.api_key}/latest/{self.base_currency}"

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
    def fetch_exchange_rates(self) -> Dict[str, float]:
        logger.info(f"Fetching exchange rates for base {self.base_currency}")
        try:
            if self.api_key == "demo_key":
                logger.warning("Using demo key. Returning mocked rates.")
                return {"EUR": 0.9, "GBP": 0.75, "JPY": 110.0, "USD": 1.0}
            
            response = requests.get(self.api_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("conversion_rates", {})
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch exchange rates: {e}")
            raise

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Processing currency conversion.")
        rates = self.fetch_exchange_rates()
        
        def convert_to_base(row):
            currency = row['currency']
            amount = row['amount']
            rate = rates.get(currency)
            if rate is None or rate == 0:
                logger.warning(f"Unknown rate for currency {currency}. Returning original amount.")
                return amount
            return amount / rate

        df[f'{self.base_currency.lower()}_amount'] = df.apply(convert_to_base, axis=1)
        return df

if __name__ == "__main__":
    pipeline = CurrencyConverterPipeline(base_currency="USD")
    
    raw_data = pd.DataFrame({
        'tx_id': [1, 2, 3], 
        'amount': [100.0, 50.0, 200.0], 
        'currency': ['EUR', 'GBP', 'USD']
    })
    
    try:
        processed_df = pipeline.process(raw_data)
        logger.info(f"\nConverted Data:\n{processed_df}")
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
