import pandas as pd
import os

def load_sample_data(n_samples=5, customer_account=None):
    """
    Load sample transaction data from the CSV file.
    
    Args:
        n_samples: Number of random samples to return
        customer_account: If provided, return random transactions for this customer account
        
    Returns:
        DataFrame containing transaction data
    """
    csv_path = "final_synthetic_transactions.csv"
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Transaction data file not found: {csv_path}")
    
    # If filtering by customer account, read in chunks to handle large files
    if customer_account:
        # Convert customer_account to string to ensure proper comparison
        customer_account_str = str(customer_account)
        
        # Process the file in chunks to avoid memory issues
        chunk_size = 100000  # Adjust based on available memory
        matching_transactions = []
        
        for chunk in pd.read_csv(csv_path, chunksize=chunk_size):
            # Convert the column to string for comparison
            chunk['customer_account_number'] = chunk['customer_account_number'].astype(str)
            # Filter matching transactions
            matches = chunk[chunk['customer_account_number'] == customer_account_str]
            if not matches.empty:
                matching_transactions.append(matches)
                # If we have enough transactions, we can stop
                if sum(len(df) for df in matching_transactions) >= n_samples:
                    break
        
        if not matching_transactions:
            print(f"No transactions found for customer account {customer_account}")
            return pd.DataFrame()
        
        # Combine all matching chunks
        df = pd.concat(matching_transactions, ignore_index=True)
        
        # Take a random sample of n_samples or all if fewer
        if len(df) > n_samples:
            df = df.sample(n=n_samples)
            
        print(f"Loaded {len(df)} sample transactions for customer account {customer_account}")
        return df
    else:
        # Load random sample
        try:
            # Try to read the whole file if it's not too large
            df = pd.read_csv(csv_path)
            return df.sample(n=min(n_samples, len(df)))
        except MemoryError:
            # If file is too large, read only a sample
            return pd.read_csv(csv_path, nrows=n_samples)