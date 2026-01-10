"""
CLI for testing the Semantic Planner.

Usage:
    python -m semantic_planner.cli "Show me all users"
    python -m semantic_planner.cli --interactive
"""
import asyncio
import argparse
import json
import sys

from .pipeline import SemanticPipeline


def print_result(result, verbose: bool = False):
    """Pretty print a pipeline result."""
    print("\n" + "="*60)
    print(f"Query: {result.original_query}")
    print("="*60)
    
    if verbose and result.extracted_intent:
        print(f"\n📊 Intent: {result.extracted_intent.intent_type.value}")
        print(f"   Entity: {result.extracted_intent.entity_type.value if result.extracted_intent.entity_type else 'N/A'}")
        print(f"   Confidence: {result.extracted_intent.confidence:.2%}")
        print(f"   Parameters: {result.extracted_intent.parameters}")
    
    if verbose and result.graphql_query:
        print(f"\n📝 GraphQL Query:")
        print("-"*40)
        print(result.graphql_query)
        print("-"*40)
    
    if verbose and result.graphql_result:
        print(f"\n📦 Raw Result:")
        print(json.dumps(result.graphql_result, indent=2, ensure_ascii=False)[:500])
    
    print(f"\n💬 Response:")
    print("-"*40)
    print(result.natural_response)
    print("-"*40)
    
    status = "✅ Success" if result.success else "❌ Failed"
    print(f"\nStatus: {status}")


async def interactive_mode(pipeline: SemanticPipeline, verbose: bool):
    """Run in interactive mode."""
    print("\n🤖 Semantic GraphQL Planner - Interactive Mode")
    print("="*50)
    print("Enter natural language queries (type 'quit' to exit)")
    print("Example queries:")
    print("  - Vis meg alle brukere")
    print("  - Get the product with id 1")
    print("  - Opprett en ny bruker med navn Test")
    print("="*50)
    
    while True:
        try:
            query = input("\n> ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye! 👋")
                break
            
            if not query:
                continue
            
            result = await pipeline.process(query)
            print_result(result, verbose)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


async def main():
    parser = argparse.ArgumentParser(
        description="Semantic Planner CLI - Natural Language to GraphQL"
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Natural language query to process"
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Run in interactive mode"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed output including GraphQL query and raw results"
    )
    parser.add_argument(
        "--endpoint",
        default="http://localhost:8000/graphql",
        help="GraphQL endpoint URL"
    )
    parser.add_argument(
        "--language",
        default="no",
        choices=["no", "en"],
        help="Response language (no=Norwegian, en=English)"
    )
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = SemanticPipeline(
        graphql_endpoint=args.endpoint,
        language=args.language
    )
    
    if args.interactive:
        await interactive_mode(pipeline, args.verbose)
    elif args.query:
        result = await pipeline.process(args.query)
        print_result(result, args.verbose)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
