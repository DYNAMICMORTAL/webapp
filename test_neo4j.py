from neo4j import GraphDatabase

def test_connection():
    try:
        # Try to connect to Neo4j
        driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'admin123'))
        driver.verify_connectivity()
        print(driver)
        print("Neo4j connection successful!")
        driver.close()
        return True
    except Exception as e:
        print(f"Neo4j connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection() 