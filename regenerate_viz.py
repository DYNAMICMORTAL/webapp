from bankapp.branches.neo4j_utils import generate_static_visualization, generate_standalone_visualization, load_transaction_data

def regenerate_visualization(customer_id=20917):
    """
    Regenerate the static and standalone visualizations for a specific customer
    """
    # Path to the CSV file
    import os
    csv_path = os.path.join('bankapp', 'branches', 'data', 'final_synthetic_transactions.csv')
    
    print(f"Regenerating visualizations for customer {customer_id}...")
    
    # Load transaction data
    graph_data = load_transaction_data(customer_id, csv_path)
    
    # Generate static visualization
    static_viz_path = generate_static_visualization(str(customer_id))
    print(f"Static visualization regenerated: {static_viz_path}")
    
    # Generate standalone visualization
    standalone_viz_path = generate_standalone_visualization(str(customer_id), graph_data)
    print(f"Standalone visualization regenerated: {standalone_viz_path}")
    
    return static_viz_path, standalone_viz_path

if __name__ == "__main__":
    import sys
    customer_id = int(sys.argv[1]) if len(sys.argv) > 1 else 20917
    regenerate_visualization(customer_id) 