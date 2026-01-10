"""
FalkorDB Client Module

Provides connection management and utility functions for interacting
with FalkorDB graph database.

FalkorDB is a high-performance graph database that supports:
- Cypher query language
- Property graphs
- Full-text search
- Graph algorithms

Documentation: https://docs.falkordb.com/
"""

import os
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class FalkorConfig:
    """Configuration for FalkorDB connection."""
    host: str = "localhost"
    port: int = 6379
    graph_name: str = "energy_graph"
    password: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "FalkorConfig":
        """Load configuration from environment variables."""
        return cls(
            host=os.getenv("FALKORDB_HOST", "localhost"),
            port=int(os.getenv("FALKORDB_PORT", "6379")),
            graph_name=os.getenv("FALKORDB_GRAPH", "energy_graph"),
            password=os.getenv("FALKORDB_PASSWORD"),
        )


class FalkorDBClient:
    """
    Client wrapper for FalkorDB operations.
    
    Usage:
        client = FalkorDBClient()
        client.connect()
        
        # Execute query
        result = client.query("MATCH (b:Building) RETURN b")
        
        # Create node
        client.execute("CREATE (b:Building {name: 'Test'})")
        
        client.close()
    """
    
    def __init__(self, config: Optional[FalkorConfig] = None):
        self.config = config or FalkorConfig.from_env()
        self._db = None
        self._graph = None
    
    def connect(self) -> None:
        """Establish connection to FalkorDB."""
        try:
            from falkordb import FalkorDB
            
            self._db = FalkorDB(
                host=self.config.host,
                port=self.config.port,
                password=self.config.password
            )
            self._graph = self._db.select_graph(self.config.graph_name)
            print(f"[OK] Connected to FalkorDB at {self.config.host}:{self.config.port}")
            print(f"[OK] Using graph: {self.config.graph_name}")
            
        except ImportError:
            print("[ERROR] FalkorDB package not installed. Run: pip install falkordb")
            raise
        except Exception as e:
            print(f"[ERROR] Failed to connect to FalkorDB: {e}")
            raise
    
    @property
    def graph(self):
        """Get the graph object for direct operations."""
        if self._graph is None:
            raise RuntimeError("Not connected. Call connect() first.")
        return self._graph
    
    def query(self, cypher: str, params: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """
        Execute a Cypher query and return results.
        
        Args:
            cypher: Cypher query string
            params: Optional query parameters
            
        Returns:
            List of result records as dictionaries
        """
        if self._graph is None:
            raise RuntimeError("Not connected. Call connect() first.")
        
        result = self._graph.query(cypher, params)
        
        # Convert to list of dicts
        records = []
        if result.result_set:
            headers = result.header
            for row in result.result_set:
                record = {}
                for i, value in enumerate(row):
                    # Extract key from header (handles tuple, list, or string)
                    header = headers[i]
                    if isinstance(header, (tuple, list)):
                        key = str(header[1]) if len(header) > 1 else str(header[0])
                    else:
                        key = str(header)
                    record[key] = self._convert_value(value)
                records.append(record)
        
        return records
    
    def execute(self, cypher: str, params: Optional[Dict[str, Any]] = None) -> None:
        """Execute a Cypher command without returning results."""
        if self._graph is None:
            raise RuntimeError("Not connected. Call connect() first.")
        
        self._graph.query(cypher, params)
    
    def _convert_value(self, value: Any) -> Any:
        """Convert FalkorDB values to Python types."""
        if hasattr(value, 'properties'):
            # It's a Node
            return {
                'id': value.id,
                'labels': list(value.labels) if hasattr(value, 'labels') else [],
                'properties': dict(value.properties)
            }
        elif hasattr(value, 'relation'):
            # It's an Edge
            return {
                'type': value.relation,
                'src_node': value.src_node,
                'dest_node': value.dest_node,
                'properties': dict(value.properties) if hasattr(value, 'properties') else {}
            }
        return value
    
    def delete_all(self) -> None:
        """Delete all nodes and relationships in the graph."""
        self.execute("MATCH (n) DETACH DELETE n")
        print("[OK] Deleted all nodes and relationships")
    
    def get_node_count(self) -> int:
        """Get total number of nodes in the graph."""
        result = self.query("MATCH (n) RETURN count(n) as count")
        return result[0]['count'] if result else 0
    
    def get_edge_count(self) -> int:
        """Get total number of relationships in the graph."""
        result = self.query("MATCH ()-[r]->() RETURN count(r) as count")
        return result[0]['count'] if result else 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics."""
        node_count = self.get_node_count()
        edge_count = self.get_edge_count()
        
        # Get label counts using an aggregate query
        label_counts = {}
        try:
            # Use a simpler approach - query known labels directly
            known_labels = [
                "Building", "Floor", "Zone", "HVAC_System", "Electrical_System",
                "Lighting_System", "Air_Handling_Unit", "Chiller", "Pump",
                "Heat_Exchanger", "Variable_Air_Volume_Box",
                "Building_Electrical_Meter", "Building_Gas_Meter", 
                "Building_Water_Meter", "Thermal_Power_Meter",
                "Temperature_Sensor", "CO2_Sensor", "Power_Sensor",
                "Humidity_Sensor", "Energy_Sensor", "Occupancy_Sensor"
            ]
            for label in known_labels:
                try:
                    count_result = self.query(f"MATCH (n:{label}) RETURN count(n) as c")
                    count = count_result[0]['c'] if count_result else 0
                    if count > 0:
                        label_counts[label] = count
                except:
                    pass
        except Exception as e:
            print(f"[WARN] Could not get label counts: {e}")
        
        return {
            'total_nodes': node_count,
            'total_edges': edge_count,
            'nodes_by_label': label_counts
        }
    
    def close(self) -> None:
        """Close the database connection."""
        self._graph = None
        self._db = None
        print("[OK] Connection closed")


def create_client(
    host: str = "localhost",
    port: int = 6379,
    graph_name: str = "energy_graph"
) -> FalkorDBClient:
    """
    Create and connect a FalkorDB client.
    
    Args:
        host: FalkorDB host
        port: FalkorDB port
        graph_name: Name of the graph to use
        
    Returns:
        Connected FalkorDBClient instance
    """
    config = FalkorConfig(host=host, port=port, graph_name=graph_name)
    client = FalkorDBClient(config)
    client.connect()
    return client


if __name__ == "__main__":
    # Test connection
    print("Testing FalkorDB connection...")
    
    try:
        client = create_client()
        
        # Create a test node
        client.execute('CREATE (t:Test {name: "connection_test", timestamp: datetime()})')
        print("✓ Created test node")
        
        # Query it back
        result = client.query("MATCH (t:Test) RETURN t")
        print(f"✓ Query result: {result}")
        
        # Clean up
        client.execute("MATCH (t:Test {name: 'connection_test'}) DELETE t")
        print("✓ Cleaned up test node")
        
        stats = client.get_statistics()
        print(f"\nGraph statistics: {stats}")
        
        client.close()
        
    except Exception as e:
        print(f"Connection test failed: {e}")
        print("\nMake sure FalkorDB is running. You can start it with Docker:")
        print("  docker run -p 6379:6379 -it --rm falkordb/falkordb")
