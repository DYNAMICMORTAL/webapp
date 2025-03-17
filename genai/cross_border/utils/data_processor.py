import pandas as pd
import random
import os

def load_transactions(n_samples=3, customer_acc_number=None, file_path=None):
    """
    Load transactions for a specific customer account number from the synthetic data CSV file.
    
    Args:
        n_samples (int): Number of random transactions to load
        customer_acc_number (str): Customer account number to filter transactions
        file_path (str, optional): Path to the CSV file
        
    Returns:
        pd.DataFrame: DataFrame containing the filtered transactions
    """
    if file_path is None:
        file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                "synthetic_data_with_risk.csv")
    
    try:
        df = pd.read_csv(file_path)
        print(f"Loaded {len(df)} transactions from CSV file")
        
        # Print column names to debug
        print(f"Available columns: {df.columns.tolist()}")
        
        # Filter by customer account number if provided
        if customer_acc_number is not None:
            df = df[df['customer_acc_number'] == customer_acc_number]
            print(f"Filtered to {len(df)} transactions for account {customer_acc_number}")
        
        # Filter for cross-border transactions
        if 'is_cross_border' in df.columns:
            df = df[df['is_cross_border'] == True]
            print(f"Filtered to {len(df)} cross-border transactions")
        elif 'source_country' in df.columns and 'destination_country' in df.columns:
            df = df[df['source_country'] != df['destination_country']]
            print(f"Filtered to {len(df)} cross-border transactions")
        
        # Sample random transactions
        if len(df) > n_samples:
            sampled_df = df.sample(n=n_samples, random_state=42)
            print(f"Sampled {len(sampled_df)} transactions")
        else:
            sampled_df = df
            print(f"Using all {len(sampled_df)} transactions (less than requested sample size)")
            
        # Debug: print a sample transaction
        if not sampled_df.empty:
            print("\nSample transaction data:")
            print(sampled_df.iloc[0].to_dict())
            
        return sampled_df
        
    except Exception as e:
        print(f"Error loading transaction data: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error