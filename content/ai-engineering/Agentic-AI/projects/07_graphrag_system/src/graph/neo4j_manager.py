class MockNeo4jManager:
    def __init__(self):
        # Mock graph: (Entity) -[REL]-> (Entity)
        self.graph = {
            "SupplierA": [("SUPPLIES", "ComponentX")],
            "ComponentX": [("USED_IN", "ProductY")],
            "ProductY": [("MANUFACTURED_BY", "FactoryZ")]
        }

    def execute_cypher(self, query: str) -> str:
        """
        Mocks the execution of a Cypher query.
        Example query: MATCH (s:Supplier)-[:SUPPLIES]->(c:Component) WHERE s.name='SupplierA' RETURN c
        """
        print(f"[Neo4j] Executing Cypher: {query}")
        
        # Naive mock logic for demonstration
        if "SupplierA" in query:
            return "ComponentX"
        if "ComponentX" in query:
            return "ProductY"
            
        return "No results found."

neo4j_db = MockNeo4jManager()
