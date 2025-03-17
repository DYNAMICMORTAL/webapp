from neo4j import GraphDatabase
import os

def initialize_neo4j():
    """
    Initialize Neo4j database with necessary constraints and indexes
    """
    # Get Neo4j connection details from environment variables or use defaults
    uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    user = os.environ.get('NEO4J_USER', 'neo4j')
    password = os.environ.get('NEO4J_PASSWORD', 'admin123')
    
    try:
        # Connect to Neo4j
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session() as session:
            # Create constraints
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Customer) REQUIRE c.account_number IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (a:Account) REQUIRE a.account_number IS UNIQUE")
            
            # Create indexes
            session.run("CREATE INDEX IF NOT EXISTS FOR (c:Customer) ON (c.risk_level)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (a:Account) ON (a.transaction_method)")
            session.run("CREATE INDEX IF NOT EXISTS FOR ()-[t:TRANSACTION]-() ON (t.is_fraud)")
            
            print("Neo4j database initialized successfully!")
        
        driver.close()
        return True
    
    except Exception as e:
        print(f"Error initializing Neo4j database: {str(e)}")
        return False

if __name__ == "__main__":
    initialize_neo4j() 