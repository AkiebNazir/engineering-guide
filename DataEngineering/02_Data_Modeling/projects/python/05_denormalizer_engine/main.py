import pandas as pd

def main():
    # 1. Simulate Normalized Tables (Dimensions & Facts)
    dim_product = pd.DataFrame({
        'product_id': [1, 2],
        'product_name': ['Widget A', 'Widget B'],
        'category': ['Widgets', 'Widgets']
    })
    
    dim_store = pd.DataFrame({
        'store_id': [10, 20],
        'store_name': ['North Branch', 'South Branch'],
        'city': ['Chicago', 'Houston']
    })
    
    fact_sales = pd.DataFrame({
        'sale_id': [100, 101, 102],
        'product_id': [1, 2, 1],
        'store_id': [10, 10, 20],
        'amount': [50.0, 75.0, 50.0]
    })
    
    print("--- Normalized Fact Table ---")
    print(fact_sales)
    print("\n")
    
    # 2. Denormalizer Engine: Join everything into one wide table
    denormalized_df = fact_sales.merge(dim_product, on='product_id', how='left') \
                                .merge(dim_store, on='store_id', how='left')
                                
    print("--- Denormalized Wide Table ---")
    print(denormalized_df)

if __name__ == '__main__':
    main()
