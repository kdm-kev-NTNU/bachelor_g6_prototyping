"""
CLI Interface for NL-to-KG Pipeline

Interactive command-line interface for querying the Brick Ontology
knowledge graph with natural language.

Pipeline: NL → GraphQL → Cypher → FalkorDB
"""

import argparse
import json
import sys
import os

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline import KGPipeline


def print_banner():
    """Print welcome banner."""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║          NL-to-KG: Natural Language to Knowledge Graph           ║
║                                                                  ║
║    Pipeline: NL → Intent → GraphQL → Cypher → FalkorDB          ║
╚══════════════════════════════════════════════════════════════════╝
    """)


def print_help():
    """Print help message."""
    print("""
Eksempler på spørringer:
  • "Vis alle sensorer i bygget"
  • "Hvilke soner mater AHU-en?"
  • "List alle temperatursensorer"
  • "Hva er bygningens adresse?"
  • "Vis alle etasjer"
  • "Sensorer i Foyer"
  • "Tidsserie-ID for hovedeffektmåler"

Kommandoer:
  help      - Vis denne hjelpen
  debug     - Toggle debug-modus (vis pipeline-steg)
  graphql   - Vis siste GraphQL-spørring
  cypher    - Vis siste Cypher-spørring
  explain   - Forklar hvordan siste spørring ble behandlet
  exit/q    - Avslutt
""")


def run_interactive(
    host: str = "localhost",
    port: int = 6379,
    graph: str = "energy_graph",
    language: str = "no"
):
    """Run interactive CLI session."""
    print_banner()
    
    # Initialize pipeline
    pipeline = KGPipeline(
        falkor_host=host,
        falkor_port=port,
        graph_name=graph,
        language=language
    )
    
    # Try to connect
    print(f"Kobler til FalkorDB på {host}:{port}...")
    if not pipeline.connect():
        print("[FEIL] Kunne ikke koble til FalkorDB.")
        print("Sjekk at databasen kjører: docker start falkordb")
        return
    
    print("[OK] Koblet til!")
    print_help()
    
    debug_mode = False
    last_result = None
    last_query = None
    
    try:
        while True:
            try:
                query = input("\n🔍 Spørring> ").strip()
            except EOFError:
                break
            
            if not query:
                continue
            
            # Handle commands
            if query.lower() in ["exit", "quit", "q"]:
                print("Ha det!")
                break
            
            if query.lower() == "help":
                print_help()
                continue
            
            if query.lower() == "debug":
                debug_mode = not debug_mode
                print(f"Debug-modus: {'PÅ' if debug_mode else 'AV'}")
                continue
            
            if query.lower() == "graphql":
                if last_result and last_result.graphql_query:
                    print("\n--- GraphQL Query ---")
                    print(last_result.graphql_query.query)
                    print(f"\nVariables: {last_result.graphql_query.variables}")
                else:
                    print("Ingen tidligere spørring.")
                continue
            
            if query.lower() == "cypher":
                if last_result and last_result.cypher_query:
                    print("\n--- Cypher Query ---")
                    print(last_result.cypher_query.cypher)
                    print(f"\nParameters: {last_result.cypher_query.parameters}")
                else:
                    print("Ingen tidligere spørring.")
                continue
            
            if query.lower() == "explain":
                if last_query:
                    print("\n--- Pipeline Explanation ---")
                    explanation = pipeline.explain(last_query)
                    print(json.dumps(explanation, indent=2, ensure_ascii=False))
                else:
                    print("Ingen tidligere spørring å forklare.")
                continue
            
            # Process query
            last_query = query
            result = pipeline.process(query)
            last_result = result
            
            if debug_mode:
                print("\n┌─── Debug Info ───────────────────────────────────────────┐")
                print(f"│ Pipeline: {result.debug_info.get('pipeline', 'N/A')}")
                print(f"│ Stages: {' → '.join(result.debug_info.get('stages', []))}")
                print(f"│ Intent: {result.debug_info.get('intent_type', 'N/A')} ({result.debug_info.get('intent_confidence', 0):.0%})")
                print(f"│ Entity: {result.debug_info.get('entity_class', 'N/A')}")
                if result.graphql_query:
                    print(f"│ GraphQL Op: {result.graphql_query.operation_name}")
                if result.cypher_query:
                    print(f"│ Cypher: {result.cypher_query.description}")
                print(f"│ Results: {result.debug_info.get('result_count', 0)}")
                print("└──────────────────────────────────────────────────────────┘")
            
            print("\n" + result.natural_response)
    
    finally:
        pipeline.close()


def run_single_query(
    query: str,
    host: str = "localhost",
    port: int = 6379,
    graph: str = "energy_graph",
    language: str = "no",
    output_format: str = "text",
    show_pipeline: bool = False
):
    """Run a single query and exit."""
    pipeline = KGPipeline(
        falkor_host=host,
        falkor_port=port,
        graph_name=graph,
        language=language
    )
    
    try:
        if not pipeline.connect():
            print("Error: Could not connect to FalkorDB", file=sys.stderr)
            sys.exit(1)
        
        result = pipeline.process(query)
        
        if output_format == "json":
            print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        elif show_pipeline:
            print("=== Pipeline Execution ===")
            print(f"Query: {query}")
            print(f"\n1. Intent: {result.extracted_intent.intent_type.value if result.extracted_intent else 'N/A'}")
            if result.graphql_query:
                print(f"\n2. GraphQL:\n{result.graphql_query.query[:200]}...")
            if result.cypher_query:
                print(f"\n3. Cypher:\n{result.cypher_query.cypher[:200]}...")
            print(f"\n4. Results: {len(result.raw_results or [])} rows")
            print(f"\n5. Response:\n{result.natural_response}")
        else:
            print(result.natural_response)
        
        sys.exit(0 if result.success else 1)
    
    finally:
        pipeline.close()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="NL-to-KG: Query Brick Ontology knowledge graph with natural language",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Pipeline: NL → Intent → GraphQL → Cypher → FalkorDB

Examples:
  python cli.py                                  # Interactive mode
  python cli.py "Vis alle sensorer"              # Single query
  python cli.py -q "List sensors" --lang en      # English query
  python cli.py "Vis bygget" --pipeline          # Show full pipeline
  python cli.py --host 192.168.1.10              # Custom host
        """
    )
    
    parser.add_argument(
        "query",
        nargs="?",
        help="Query to execute (omit for interactive mode)"
    )
    
    parser.add_argument(
        "-q", "--query",
        dest="query_flag",
        help="Query to execute"
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
    
    parser.add_argument(
        "--lang",
        choices=["no", "en"],
        default="no",
        help="Response language (default: no)"
    )
    
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    
    parser.add_argument(
        "--pipeline",
        action="store_true",
        help="Show full pipeline execution details"
    )
    
    args = parser.parse_args()
    
    # Determine query
    query = args.query or args.query_flag
    
    if query:
        run_single_query(
            query=query,
            host=args.host,
            port=args.port,
            graph=args.graph,
            language=args.lang,
            output_format=args.format,
            show_pipeline=args.pipeline
        )
    else:
        run_interactive(
            host=args.host,
            port=args.port,
            graph=args.graph,
            language=args.lang
        )


if __name__ == "__main__":
    main()
