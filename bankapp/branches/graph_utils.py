import pandas as pd
import networkx as nx
from pyvis.network import Network
import os
import json
import random

def generate_transaction_graph(customer_id=20917, output_path='bankapp/branches/static/graph'):
    """
    Generate a transaction graph visualization for a specific customer
    
    Args:
        customer_id: The customer account number to focus on
        output_path: Directory to save the generated HTML file
    
    Returns:
        dict: Graph statistics and path to the generated HTML file
    """
    # Path to the CSV file
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                           'data', 'final_synthetic_transactions.csv')
    
    # Read the CSV file
    try:
        df = pd.read_csv(csv_path)
        
        # Filter transactions for the specified customer account number
        customer_transactions = df[df['customer_account_number'] == customer_id]
        
        # Create a directed graph
        G = nx.DiGraph()
        
        # Add the central customer node
        G.add_node(str(customer_id), 
                  title=f"Customer {customer_id}",
                  size=40,
                  label=f"Customer {customer_id}")
        
        # Count fraud transactions
        fraud_count = customer_transactions[customer_transactions['label_for_fraud'] == 1].shape[0]
        
        # Set node color based on fraud count
        if fraud_count >= 5:
            G.nodes[str(customer_id)]['color'] = 'red'
        else:
            G.nodes[str(customer_id)]['color'] = 'green'
        
        # Generate unique account numbers if missing
        # This ensures we have multiple nodes in the visualization
        account_mapping = {}
        
        # Add transaction nodes and edges
        for idx, row in customer_transactions.iterrows():
            # Determine if this is an incoming or outgoing transaction
            is_outgoing = row['transaction_amount'] < 0
            
            # Get or generate the other party in the transaction
            other_party = row.get('counterparty_account_number', None)
            
            # If counterparty is missing or NaN, generate a consistent ID based on transaction properties
            if pd.isna(other_party) or other_party is None:
                # Use transaction properties to create a consistent ID
                transaction_key = f"{row['transaction_id']}_{row['method_of_transaction']}_{row['location_data']}"
                
                if transaction_key in account_mapping:
                    other_party = account_mapping[transaction_key]
                else:
                    # Generate a random account number that's not the customer ID
                    while True:
                        random_account = random.randint(10000, 99999)
                        if random_account != customer_id:
                            break
                    
                    other_party = random_account
                    account_mapping[transaction_key] = other_party
            
            # Add the other party node if it doesn't exist
            if not G.has_node(str(other_party)):
                # Use different node colors based on transaction method
                method_colors = {
                    'RTGS': '#4299e1',  # blue
                    'NEFT': '#f6e05e',  # yellow
                    'UPI': '#9f7aea',   # purple
                    'IMPS': '#4fd1c5',  # teal
                    'DIRECT_TRANSFER': '#fc8181'  # pink
                }
                
                node_color = method_colors.get(row['method_of_transaction'], '#a0aec0')  # default gray
                
                G.add_node(str(other_party), 
                          title=f"Account {other_party}",
                          size=20,
                          label=f"Account {other_party}",
                          color=node_color)
            
            # Determine edge direction and color
            if is_outgoing:
                source, target = str(customer_id), str(other_party)
            else:
                source, target = str(other_party), str(customer_id)
            
            # Set edge color based on fraud label
            edge_color = 'red' if row['label_for_fraud'] == 1 else 'gray'
            
            # Calculate edge width based on transaction amount (normalized)
            amount_abs = abs(float(row['transaction_amount']))
            edge_width = 1 + min(5, amount_abs / 5000)  # Cap at width 6
            
            # Add the edge with transaction details
            G.add_edge(source, target, 
                      title=f"Transaction {row['transaction_id']}: {row['transaction_amount']} {row['transaction_currency']}",
                      color=edge_color,
                      value=amount_abs,
                      width=edge_width,
                      label=f"{amount_abs:.2f}")
        
        # Create a pyvis network from the networkx graph
        net = Network(height="600px", width="100%", directed=True, notebook=False)
        
        # Set physics options for better visualization
        net.set_options("""
        {
          "physics": {
            "forceAtlas2Based": {
              "gravitationalConstant": -100,
              "centralGravity": 0.15,
              "springLength": 150,
              "springConstant": 0.05,
              "avoidOverlap": 0.8
            },
            "maxVelocity": 50,
            "solver": "forceAtlas2Based",
            "timestep": 0.35,
            "stabilization": {
              "enabled": true,
              "iterations": 1000
            }
          },
          "edges": {
            "smooth": {
              "type": "continuous",
              "forceDirection": "none"
            },
            "arrows": {
              "to": {
                "enabled": true,
                "scaleFactor": 0.5
              }
            }
          },
          "interaction": {
            "hover": true,
            "navigationButtons": true,
            "keyboard": {
              "enabled": true
            }
          }
        }
        """)
        
        # Add the networkx graph to the pyvis network
        net.from_nx(G)
        
        # Ensure the output directory exists
        os.makedirs(output_path, exist_ok=True)
        
        # Save the graph as an HTML file
        output_file = f"{output_path}/transaction_graph_{customer_id}.html"
        net.save_graph(output_file)
        
        # Return statistics and file path
        return {
            'total_transactions': len(customer_transactions),
            'fraud_transactions': fraud_count,
            'normal_transactions': len(customer_transactions) - fraud_count,
            'graph_file': f"graph/transaction_graph_{customer_id}.html",
            'node_count': len(G.nodes),
            'edge_count': len(G.edges)
        }
    
    except Exception as e:
        print(f"Error generating graph: {str(e)}")
        return {
            'error': str(e)
        }

def get_transaction_statistics(customer_id=20917):
    """
    Get transaction statistics for a specific customer
    
    Args:
        customer_id: The customer account number
    
    Returns:
        dict: Transaction statistics
    """
    # Path to the CSV file
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                           'data', 'final_synthetic_transactions.csv')
    
    try:
        df = pd.read_csv(csv_path)
        
        # Filter transactions for the specified customer account number
        customer_transactions = df[df['customer_account_number'] == customer_id]
        
        # Calculate statistics
        total = len(customer_transactions)
        fraud = customer_transactions[customer_transactions['label_for_fraud'] == 1].shape[0]
        normal = total - fraud
        
        # Calculate amounts by currency
        currency_amounts = customer_transactions.groupby('transaction_currency')['transaction_amount'].sum().to_dict()
        
        # Calculate methods distribution
        methods = customer_transactions['method_of_transaction'].value_counts().to_dict()
        
        return {
            'total_transactions': total,
            'fraud_transactions': fraud,
            'normal_transactions': normal,
            'fraud_percentage': (fraud / total * 100) if total > 0 else 0,
            'currency_amounts': currency_amounts,
            'transaction_methods': methods
        }
    
    except Exception as e:
        print(f"Error getting statistics: {str(e)}")
        return {
            'error': str(e)
        } 