from neo4j import GraphDatabase
import pandas as pd
import os
from typing import Dict, Any
import urllib.parse

class Neo4jConnection:
    def __init__(self, uri=None, user=None, password=None):
        """Initialize Neo4j connection with environment variables or defaults"""
        self.uri = uri or os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
        self.user = "admin"
        self.password = "admin123"
        
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        
    def close(self):
        """Close the Neo4j connection"""
        self.driver.close()
        
    def verify_connectivity(self):
        """Verify Neo4j connection"""
        try:
            self.driver.verify_connectivity()
            return True
        except Exception as e:
            print(f"Failed to connect to Neo4j: {str(e)}")
            return False

def load_transaction_data(customer_id: int, csv_path: str) -> Dict[str, Any]:
    """
    Load transaction data from CSV and prepare it for Neo4j
    
    Args:
        customer_id: The customer account number
        csv_path: Path to the CSV file containing transaction data
    
    Returns:
        dict: Transaction data and statistics
    """
    try:
        # Read the CSV file
        df = pd.read_csv(csv_path)
        
        # Filter transactions for the specified customer
        customer_transactions = df[df['customer_account_number'] == customer_id]
        
        # Calculate statistics
        total_transactions = len(customer_transactions)
        fraud_transactions = customer_transactions[customer_transactions['label_for_fraud'] == 1].shape[0]
        normal_transactions = total_transactions - fraud_transactions
        
        # Prepare nodes and relationships
        nodes = []
        relationships = []
        
        # Add customer node
        nodes.append({
            'id': str(customer_id),
            'labels': ['Customer'],
            'properties': {
                'account_number': str(customer_id),
                'fraud_count': fraud_transactions,
                'risk_level': 'High' if fraud_transactions >= 5 else 'Low'
            }
        })
        
        # Add transaction nodes and relationships
        for _, row in customer_transactions.iterrows():
            # Determine if this is an incoming or outgoing transaction
            is_outgoing = row['transaction_amount'] < 0
            
            # Get or generate counterparty account
            other_party = row.get('counterparty_account_number', None)
            if pd.isna(other_party) or other_party is None:
                other_party = f"ACC_{row['transaction_id']}"
            
            # Add counterparty node
            nodes.append({
                'id': str(other_party),
                'labels': ['Account'],
                'properties': {
                    'account_number': str(other_party),
                    'transaction_method': row['method_of_transaction']
                }
            })
            
            # Add transaction relationship
            relationships.append({
                'start_node': str(customer_id) if is_outgoing else str(other_party),
                'end_node': str(other_party) if is_outgoing else str(customer_id),
                'type': 'TRANSACTION',
                'properties': {
                    'amount': float(row['transaction_amount']),
                    'currency': row['transaction_currency'],
                    'method': row['method_of_transaction'],
                    'location': row['location_data'],
                    'is_fraud': bool(row['label_for_fraud']),
                    'timestamp': row['timestamp']
                }
            })
        
        return {
            'nodes': nodes,
            'relationships': relationships,
            'statistics': {
                'total_transactions': total_transactions,
                'fraud_transactions': fraud_transactions,
                'normal_transactions': normal_transactions,
                'fraud_percentage': (fraud_transactions / total_transactions * 100) if total_transactions > 0 else 0
            }
        }
    
    except Exception as e:
        print(f"Error loading transaction data: {str(e)}")
        return {'error': str(e)}

def create_transaction_graph(neo4j_conn: Neo4jConnection, data: Dict[str, Any]) -> bool:
    """
    Create transaction graph in Neo4j
    
    Args:
        neo4j_conn: Neo4j connection instance
        data: Dictionary containing nodes and relationships
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with neo4j_conn.driver.session() as session:
            # Clear existing data for this customer
            session.run("MATCH (n) DETACH DELETE n")
            
            # Create nodes
            for node in data['nodes']:
                labels = ':'.join(node['labels'])
                properties = ', '.join([f"{k}: ${k}" for k in node['properties'].keys()])
                query = f"CREATE (n:{labels} {{ {properties} }})"
                session.run(query, node['properties'])
            
            # Create relationships
            for rel in data['relationships']:
                query = """
                MATCH (a {account_number: $start_node})
                MATCH (b {account_number: $end_node})
                CREATE (a)-[r:TRANSACTION {
                    amount: $amount,
                    currency: $currency,
                    method: $method,
                    location: $location,
                    is_fraud: $is_fraud,
                    timestamp: $timestamp
                }]->(b)
                """
                # Create parameters dictionary with all required values
                params = {
                    'start_node': rel['start_node'],
                    'end_node': rel['end_node'],
                    **rel['properties']
                }
                session.run(query, params)
            
            return True
    
    except Exception as e:
        print(f"Error creating transaction graph: {str(e)}")
        return False

def get_neo4j_browser_url(customer_id: str, neo4j_browser_url: str = None) -> str:
    """
    Generate a Neo4j Browser URL with a Cypher query to visualize the customer's transactions
    
    Args:
        customer_id: The customer account number
        neo4j_browser_url: The base URL for Neo4j Browser (defaults to localhost)
    
    Returns:
        str: URL to open Neo4j Browser with the query
    """
    # Default Neo4j Browser URL
    base_url = neo4j_browser_url or os.environ.get('NEO4J_BROWSER_URL', 'http://localhost:7474/browser/')
    
    # Cypher query to visualize the customer's transactions
    cypher_query = f"""MATCH (c:Customer {{account_number: '{customer_id}'}})-[t:TRANSACTION]-(a:Account)
RETURN c, t, a"""
    
    # URL encode the query
    encoded_query = urllib.parse.quote(cypher_query)
    
    # Generate the URL - use 'query' instead of 'play'
    url = f"{base_url}?cmd=query&arg={encoded_query}"
    
    return url

def generate_static_visualization(customer_id: str, output_dir: str = 'bankapp/branches/static/graph') -> str:
    """
    Generate a static HTML visualization of the Neo4j graph
    
    Args:
        customer_id: The customer account number
        output_dir: Directory to save the generated HTML file
    
    Returns:
        str: Path to the generated HTML file
    """
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Create the HTML file
    output_file = f"{output_dir}/neo4j_graph_{customer_id}.html"
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Transaction Network for Customer {customer_id}</title>
    <script src="https://unpkg.com/neovis.js@2.0.2"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
        }}
        #viz {{
            width: 100%;
            height: 100vh;
            border: none;
        }}
    </style>
</head>
<body>
    <div id="viz"></div>

    <script>
        // Initialize the visualization
        const viz = new NeoVis.default({{
            container_id: "viz",
            server_url: "bolt://localhost:7687",
            server_user: "admin",
            server_password: "admin123",
            labels: {{
                "Customer": {{
                    caption: "account_number",
                    size: "fraud_count",
                    community: "risk_level",
                    title_properties: ["account_number", "fraud_count", "risk_level"]
                }},
                "Account": {{
                    caption: "account_number",
                    size: 10,
                    community: "transaction_method",
                    title_properties: ["account_number", "transaction_method"]
                }}
            }},
            relationships: {{
                "TRANSACTION": {{
                    caption: false,
                    thickness: "amount",
                    color: {{
                        function: {{
                            field: "is_fraud",
                            mapper: function(is_fraud) {{
                                return is_fraud ? "#ff0000" : "#999999";
                            }}
                        }}
                    }},
                    title_properties: ["amount", "currency", "method", "is_fraud"]
                }}
            }},
            initial_cypher: "MATCH (c:Customer {{account_number: '{customer_id}'}})-[t:TRANSACTION]-(a:Account) RETURN c, t, a"
        }});
        
        // Render the visualization
        viz.render();
    </script>
</body>
</html>"""
    
    # Write the HTML file
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    # Return the path to the HTML file
    return f"graph/neo4j_graph_{customer_id}.html"

def generate_standalone_visualization(customer_id: str, data: Dict[str, Any], output_dir: str = 'bankapp/branches/static/graph') -> str:
    """
    Generate a standalone HTML visualization that doesn't require Neo4j
    
    Args:
        customer_id: The customer account number
        data: Dictionary containing nodes and relationships
        output_dir: Directory to save the generated HTML file
    
    Returns:
        str: Path to the generated HTML file
    """
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Create the HTML file
    output_file = f"{output_dir}/standalone_viz_{customer_id}.html"
    
    # Prepare nodes and edges for vis.js
    nodes_data = []
    edges_data = []
    
    # Process nodes
    for node in data['nodes']:
        node_type = node['labels'][0]
        node_id = node['properties']['account_number']
        
        if node_type == 'Customer':
            nodes_data.append({
                'id': node_id,
                'label': f"Customer {node_id}",
                'title': f"Customer Account: {node_id}",
                'group': 'customer',
                'value': 40,
                'risk': 'high' if node['properties'].get('risk_level') == 'High' else 'low'
            })
        else:
            # Determine the group based on transaction method
            method = node['properties'].get('transaction_method', 'UNKNOWN')
            group = method.lower() if method in ['RTGS', 'NEFT', 'UPI', 'IMPS'] else 'direct'
            
            nodes_data.append({
                'id': node_id,
                'label': node_id,
                'title': f"{method} Transaction",
                'group': group,
                'value': 20
            })
    
    # Process relationships
    for rel in data['relationships']:
        edges_data.append({
            'from': rel['start_node'],
            'to': rel['end_node'],
            'title': f"Rs. {abs(rel['properties']['amount']):.2f} - {rel['properties']['method']}",
            'width': 1 + min(5, abs(rel['properties']['amount']) / 5000),
            'color': {'color': '#f56565' if rel['properties']['is_fraud'] else '#a0aec0'}
        })
    
    # Create the HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Transaction Network for Customer {customer_id}</title>
    <script src="https://unpkg.com/vis-network@9.1.2/dist/vis-network.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
        }}
        #mynetwork {{
            width: 100%;
            height: 100vh;
            border: none;
        }}
        .legend {{
            position: absolute;
            top: 10px;
            right: 10px;
            background-color: rgba(255, 255, 255, 0.8);
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 12px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            margin-bottom: 5px;
        }}
        .legend-color {{
            width: 15px;
            height: 15px;
            margin-right: 5px;
            border-radius: 50%;
        }}
        .legend-edge {{
            width: 20px;
            height: 3px;
            margin-right: 5px;
        }}
    </style>
</head>
<body>
    <div id="mynetwork"></div>
    <div class="legend">
        <h3 style="margin-top: 0;">Legend</h3>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #4299e1;"></div>
            <span>RTGS Transactions</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #f6e05e;"></div>
            <span>NEFT Transactions</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #9f7aea;"></div>
            <span>UPI Transactions</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #4fd1c5;"></div>
            <span>IMPS Transactions</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #fc8181;"></div>
            <span>Direct Transfer</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #48bb78;"></div>
            <span>Customer (Low Risk)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #f56565;"></div>
            <span>Customer (High Risk)</span>
        </div>
        <hr>
        <div class="legend-item">
            <div class="legend-edge" style="background-color: #f56565;"></div>
            <span>Fraudulent Transaction</span>
        </div>
        <div class="legend-item">
            <div class="legend-edge" style="background-color: #a0aec0;"></div>
            <span>Normal Transaction</span>
        </div>
    </div>

    <script>
        // Transaction data
        const transactionData = {{
            nodes: {nodes_data},
            edges: {edges_data}
        }};

        // Create a network
        const container = document.getElementById('mynetwork');
        
        // Provide the data in the vis format
        const data = {{
            nodes: new vis.DataSet(transactionData.nodes.map(node => ({{
                id: node.id,
                label: node.label,
                title: node.title,
                value: node.value,
                color: getNodeColor(node),
                font: {{ size: 14 }}
            }}))),
            edges: new vis.DataSet(transactionData.edges.map(edge => ({{
                from: edge.from,
                to: edge.to,
                title: edge.title,
                width: edge.width,
                color: edge.color,
                arrows: 'to'
            }}))))
        }};
        
        // Options for the network
        const options = {{
            nodes: {{
                shape: 'dot',
                scaling: {{
                    min: 10,
                    max: 30,
                    label: {{
                        enabled: true,
                        min: 14,
                        max: 20
                    }}
                }}
            }},
            physics: {{
                forceAtlas2Based: {{
                    gravitationalConstant: -100,
                    centralGravity: 0.15,
                    springLength: 150,
                    springConstant: 0.05,
                    avoidOverlap: 0.8
                }},
                maxVelocity: 50,
                solver: 'forceAtlas2Based',
                timestep: 0.35,
                stabilization: {{
                    enabled: true,
                    iterations: 1000
                }}
            }},
            interaction: {{
                hover: true,
                navigationButtons: true,
                keyboard: {{
                    enabled: true
                }}
            }}
        }};
        
        // Create the network
        const network = new vis.Network(container, data, options);
        
        // Helper function to get node color based on group
        function getNodeColor(node) {{
            if (node.group === 'customer') {{
                return node.risk === 'high' ? '#f56565' : '#48bb78';
            }} else if (node.group === 'rtgs') {{
                return '#4299e1';
            }} else if (node.group === 'neft') {{
                return '#f6e05e';
            }} else if (node.group === 'upi') {{
                return '#9f7aea';
            }} else if (node.group === 'imps') {{
                return '#4fd1c5';
            }} else if (node.group === 'direct') {{
                return '#fc8181';
            }} else {{
                return '#a0aec0';
            }}
        }}
    </script>
</body>
</html>"""
    
    # Write the HTML file with UTF-8 encoding
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Return the path to the HTML file
    return f"graph/standalone_viz_{customer_id}.html" 