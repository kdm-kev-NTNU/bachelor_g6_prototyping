"""
Load Knowledge Graph into FalkorDB

This script loads the Brick-based energy knowledge graph into FalkorDB.
It creates nodes for buildings, equipment, meters, sensors, and zones,
along with their relationships.

Usage:
    python load_graph.py [--clear] [--host HOST] [--port PORT]
    
Options:
    --clear     Clear existing graph before loading
    --host      FalkorDB host (default: localhost)
    --port      FalkorDB port (default: 6379)
"""

import argparse
import sys
from typing import List

from falkor_client import FalkorDBClient, FalkorConfig
from schema import BrickEntity, BrickRelationship, create_index_queries
from seed_data import get_all_seed_data


def create_node_cypher(entity: BrickEntity) -> str:
    """Generate Cypher CREATE statement for an entity."""
    label = entity.brick_class.value
    props = entity.to_cypher_properties()
    return f"CREATE (:{label} {props})"


def create_relationship_cypher(rel: BrickRelationship) -> str:
    """Generate Cypher statement to create a relationship."""
    props = ""
    if rel.properties:
        prop_strings = []
        for k, v in rel.properties.items():
            if isinstance(v, str):
                prop_strings.append(f'{k}: "{v}"')
            else:
                prop_strings.append(f'{k}: {v}')
        props = " {" + ", ".join(prop_strings) + "}"
    
    return f"""
    MATCH (a {{id: "{rel.from_id}"}}), (b {{id: "{rel.to_id}"}})
    CREATE (a)-[:{rel.relation_type.value}{props}]->(b)
    """


def load_graph(
    client: FalkorDBClient,
    entities: List[BrickEntity],
    relationships: List[BrickRelationship],
    clear_first: bool = True
) -> None:
    """
    Load all entities and relationships into FalkorDB.
    
    Args:
        client: Connected FalkorDB client
        entities: List of Brick entities to create
        relationships: List of relationships to create
        clear_first: Whether to clear existing data first
    """
    print("\n" + "=" * 60)
    print("LOADING KNOWLEDGE GRAPH")
    print("=" * 60)
    
    if clear_first:
        print("\n[*] Clearing existing graph...")
        client.delete_all()
    
    # Create indexes
    print("\n[*] Creating indexes...")
    for index_query in create_index_queries():
        try:
            client.execute(index_query)
        except Exception as e:
            # Index might already exist
            pass
    print("  [OK] Indexes created")
    
    # Create nodes
    print(f"\n[*] Creating {len(entities)} nodes...")
    node_count = 0
    for entity in entities:
        try:
            cypher = create_node_cypher(entity)
            client.execute(cypher)
            node_count += 1
        except Exception as e:
            print(f"  [WARN] Failed to create {entity.id}: {e}")
    
    print(f"  [OK] Created {node_count} nodes")
    
    # Create relationships
    print(f"\n[*] Creating {len(relationships)} relationships...")
    rel_count = 0
    for rel in relationships:
        try:
            cypher = create_relationship_cypher(rel)
            client.execute(cypher)
            rel_count += 1
        except Exception as e:
            print(f"  [WARN] Failed to create relationship {rel.from_id} -> {rel.to_id}: {e}")
    
    print(f"  [OK] Created {rel_count} relationships")
    
    # Print summary
    print("\n" + "=" * 60)
    print("LOADING COMPLETE")
    print("=" * 60)
    
    try:
        stats = client.get_statistics()
        print(f"\n[STATS] Graph Statistics:")
        print(f"   Total nodes: {stats['total_nodes']}")
        print(f"   Total edges: {stats['total_edges']}")
        
        if stats['nodes_by_label']:
            print(f"\n   Nodes by type:")
            for label, count in stats['nodes_by_label'].items():
                print(f"     {label}: {count}")
    except Exception as e:
        print(f"\n[WARN] Could not retrieve statistics: {e}")
        print(f"   Graph loaded successfully with {node_count} nodes and {rel_count} relationships.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Load Brick-based knowledge graph into FalkorDB"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing graph before loading"
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="FalkorDB host (default: localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=6379,
        help="FalkorDB port (default: 6379)"
    )
    parser.add_argument(
        "--graph",
        default="energy_graph",
        help="Graph name (default: energy_graph)"
    )
    
    args = parser.parse_args()
    
    # Create client
    config = FalkorConfig(
        host=args.host,
        port=args.port,
        graph_name=args.graph
    )
    
    client = FalkorDBClient(config)
    
    try:
        client.connect()
        
        # Get seed data
        print("\n[*] Generating seed data...")
        entities, relationships = get_all_seed_data()
        print(f"   Generated {len(entities)} entities")
        print(f"   Generated {len(relationships)} relationships")
        
        # Load into FalkorDB
        load_graph(client, entities, relationships, clear_first=args.clear)
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        print("\nMake sure FalkorDB is running:")
        print("  docker run -p 6379:6379 -it --rm falkordb/falkordb")
        sys.exit(1)
    
    finally:
        client.close()


if __name__ == "__main__":
    main()
