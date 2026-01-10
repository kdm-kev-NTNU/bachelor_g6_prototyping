"""
FalkorDB Client for Brick Ontology Knowledge Graph

Simple client for connecting to FalkorDB and executing Cypher queries.
"""

import os
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class FalkorConfig:
    """FalkorDB connection configuration."""
    host: str = "localhost"
    port: int = 6379
    graph_name: str = "energy_graph"
    password: Optional[str] = None


class FalkorDBClient:
    """Client for FalkorDB operations."""
    
    def __init__(self, config: Optional[FalkorConfig] = None):
        self.config = config or FalkorConfig()
        self._db = None
        self._graph = None
    
    def connect(self) -> None:
        """Connect to FalkorDB."""
        try:
            from falkordb import FalkorDB
            
            self._db = FalkorDB(
                host=self.config.host,
                port=self.config.port,
                password=self.config.password
            )
            self._graph = self._db.select_graph(self.config.graph_name)
            print(f"[OK] Connected to FalkorDB at {self.config.host}:{self.config.port}")
            print(f"[OK] Graph: {self.config.graph_name}")
            
        except ImportError:
            raise RuntimeError("FalkorDB not installed. Run: pip install falkordb")
        except Exception as e:
            raise RuntimeError(f"Connection failed: {e}")
    
    def query(self, cypher: str) -> List[Dict]:
        """Execute a Cypher query and return results."""
        if self._graph is None:
            raise RuntimeError("Not connected")
        
        result = self._graph.query(cypher)
        
        records = []
        if result.result_set:
            headers = result.header
            for row in result.result_set:
                record = {}
                for i, value in enumerate(row):
                    header = headers[i]
                    if isinstance(header, (tuple, list)):
                        key = str(header[1]) if len(header) > 1 else str(header[0])
                    else:
                        key = str(header)
                    record[key] = self._convert(value)
                records.append(record)
        
        return records
    
    def execute(self, cypher: str) -> None:
        """Execute a Cypher command without returning results."""
        if self._graph is None:
            raise RuntimeError("Not connected")
        self._graph.query(cypher)
    
    def delete_all(self) -> None:
        """Delete all nodes and relationships."""
        self.execute("MATCH (n) DETACH DELETE n")
        print("[OK] Graph cleared")
    
    def _convert(self, value: Any) -> Any:
        """Convert FalkorDB values to Python types."""
        if hasattr(value, 'properties'):
            return {
                'labels': list(value.labels) if hasattr(value, 'labels') else [],
                'properties': dict(value.properties)
            }
        return value
    
    def close(self) -> None:
        """Close the connection."""
        self._graph = None
        self._db = None
        print("[OK] Disconnected")


if __name__ == "__main__":
    # Test connection
    client = FalkorDBClient()
    try:
        client.connect()
        
        # Test query
        result = client.query("MATCH (b:brick_Building) RETURN b.name as name")
        if result:
            print(f"\nBuilding: {result[0]['name']}")
        else:
            print("\nNo buildings found. Run: python load_graph.py --clear")
        
        client.close()
    except Exception as e:
        print(f"Error: {e}")
