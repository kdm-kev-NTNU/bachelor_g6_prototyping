"""
Load Brick Ontology Knowledge Graph into FalkorDB

Creates a connected graph with brick_Building as root.
All nodes have valid semantic paths to the Building.

Usage:
    python load_graph.py [--clear]
"""

import argparse
import sys
from falkor_client import FalkorDBClient, FalkorConfig
from seed_data import generate_cypher_statements, get_seed_summary


def create_indexes(client: FalkorDBClient) -> None:
    """Create indexes for common queries."""
    indexes = [
        "CREATE INDEX ON :brick_Building(id)",
        "CREATE INDEX ON :brick_Building(name)",
        "CREATE INDEX ON :brick_Floor(id)",
        "CREATE INDEX ON :brick_HVAC_Zone(id)",
        "CREATE INDEX ON :brick_Air_Handling_Unit(id)",
        "CREATE INDEX ON :brick_Electrical_Meter(id)",
        "CREATE INDEX ON :brick_Temperature_Sensor(id)",
        "CREATE INDEX ON :brick_Timeseries(id)",
        "CREATE INDEX ON :brick_Timeseries(external_id)",
    ]
    
    for index in indexes:
        try:
            client.execute(index)
        except Exception:
            pass  # Index may already exist


def load_graph(client: FalkorDBClient, clear_first: bool = True) -> None:
    """Load the Brick ontology graph into FalkorDB."""
    
    print("\n" + "=" * 50)
    print("LOADING BRICK ONTOLOGY GRAPH")
    print("=" * 50)
    
    if clear_first:
        print("\n[*] Clearing existing graph...")
        client.delete_all()
    
    print("[*] Creating indexes...")
    create_indexes(client)
    
    print("[*] Generating Cypher statements...")
    statements = generate_cypher_statements()
    print(f"    Generated {len(statements)} statements")
    
    print("[*] Executing statements...")
    success = 0
    errors = 0
    
    for i, stmt in enumerate(statements):
        try:
            client.execute(stmt)
            success += 1
        except Exception as e:
            errors += 1
            print(f"    [ERROR] Statement {i+1}: {e}")
    
    print(f"\n[OK] Executed {success} statements")
    if errors > 0:
        print(f"[WARN] {errors} errors")
    
    # Verify connectivity
    print("\n[*] Verifying graph connectivity...")
    verify_graph(client)
    
    # Print summary
    print("\n" + "=" * 50)
    print("LOAD COMPLETE")
    print("=" * 50)
    
    summary = get_seed_summary()
    print(f"\nRoot: {summary['root']}")
    print(f"Expected nodes: ~{sum([summary['floors'], summary['zones'], summary['systems'], summary['equipment'], summary['meters'], summary['sensors'], summary['timeseries']]) + 1}")
    
    # Count actual nodes
    result = client.query("MATCH (n) RETURN count(n) as count")
    if result:
        print(f"Actual nodes: {result[0]['count']}")
    
    result = client.query("MATCH ()-[r]->() RETURN count(r) as count")
    if result:
        print(f"Relationships: {result[0]['count']}")


def verify_graph(client: FalkorDBClient) -> None:
    """Verify the graph is properly connected."""
    
    # Check Building exists
    result = client.query("MATCH (b:brick_Building) RETURN b.name as name")
    if result:
        print(f"    Root Building: {result[0]['name']}")
    else:
        print("    [ERROR] No Building found!")
        return
    
    # Check all nodes are reachable from Building
    result = client.query("""
        MATCH (b:brick_Building {id: 'building_opera'})
        MATCH (b)-[*1..5]-(connected)
        RETURN count(DISTINCT connected) as reachable
    """)
    if result:
        print(f"    Nodes reachable from Building: {result[0]['reachable']}")
    
    # Check traversal path exists
    result = client.query("""
        MATCH path = (b:brick_Building)-[:brick_hasPart]->
                     (:brick_HVAC_System)-[:brick_hasMember]->
                     (:brick_Air_Handling_Unit)-[:brick_hasPoint]->
                     (:brick_Temperature_Sensor)-[:brick_hasTimeseries]->
                     (:brick_Timeseries)
        RETURN count(path) as paths
    """)
    if result and result[0]['paths'] > 0:
        print(f"    Valid traversal paths: {result[0]['paths']}")
    else:
        print("    [WARN] No complete traversal path found")


def main():
    parser = argparse.ArgumentParser(description="Load Brick ontology graph into FalkorDB")
    parser.add_argument("--clear", action="store_true", help="Clear existing graph")
    parser.add_argument("--host", default="localhost", help="FalkorDB host")
    parser.add_argument("--port", type=int, default=6379, help="FalkorDB port")
    parser.add_argument("--graph", default="energy_graph", help="Graph name")
    
    args = parser.parse_args()
    
    config = FalkorConfig(
        host=args.host,
        port=args.port,
        graph_name=args.graph
    )
    
    client = FalkorDBClient(config)
    
    try:
        client.connect()
        load_graph(client, clear_first=args.clear)
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        print("\nMake sure FalkorDB is running:")
        print("  docker start falkordb")
        sys.exit(1)
    
    finally:
        client.close()


if __name__ == "__main__":
    main()
