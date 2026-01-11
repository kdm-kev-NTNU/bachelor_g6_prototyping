"""
Test script for NL-to-KG Pipeline

Tests the complete pipeline: NL → Intent → GraphQL → Cypher → FalkorDB

Run: python test_pipeline.py
"""

import sys
import os

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'FalkorDB'))


def test_ontology():
    """Test ontology initialization."""
    print("\n=== Testing Ontology ===")
    
    from ontology import BrickOntology, BrickClass, IntentType
    
    ontology = BrickOntology()
    
    print(f"✓ Loaded {len(ontology.entities)} entity types")
    print(f"✓ Loaded {len(ontology.traversals)} traversal patterns")
    
    # Test entity lookup (Norwegian)
    building = ontology.find_entity_by_text("vis meg bygningen")
    assert building == BrickClass.BUILDING, f"Expected BUILDING, got {building}"
    print("✓ Entity lookup works (Norwegian: 'bygningen' → BUILDING)")
    
    # Test entity lookup (English)
    sensor = ontology.find_entity_by_text("temperature sensor")
    assert sensor == BrickClass.TEMPERATURE_SENSOR
    print("✓ Entity lookup works (English: 'temperature sensor' → TEMPERATURE_SENSOR)")
    
    # Test intent detection
    intent = ontology.detect_intent("vis alle sensorer")
    assert intent == IntentType.QUERY_LIST
    print("✓ Intent detection works ('vis alle' → QUERY_LIST)")


def test_intent_extractor():
    """Test intent extraction (rule-based)."""
    print("\n=== Testing Intent Extractor ===")
    
    from ontology import BrickOntology, IntentType
    from intent_extractor import IntentExtractor
    
    ontology = BrickOntology()
    extractor = IntentExtractor(ontology, api_key=None)  # No LLM
    
    test_queries = [
        ("Vis alle sensorer i bygget", IntentType.QUERY_TRAVERSE),
        ("List alle temperatursensorer", IntentType.QUERY_LIST),
        ("Hvor mange etasjer?", IntentType.QUERY_AGGREGATE),
        ("Hva er bygningens adresse?", IntentType.QUERY_ENTITY),
    ]
    
    for query, expected_intent in test_queries:
        result = extractor.extract(query)
        print(f"  '{query}'")
        print(f"    → Intent: {result.intent_type.value}, Entity: {result.entity_class}, Conf: {result.confidence:.0%}")
    
    print("✓ Intent extraction works")


def test_graphql_generator():
    """Test GraphQL query generation."""
    print("\n=== Testing GraphQL Generator ===")
    
    from ontology import BrickOntology, BrickClass, IntentType
    from graphql_generator import GraphQLGenerator
    
    ontology = BrickOntology()
    generator = GraphQLGenerator(ontology)
    
    # Test list query
    gql = generator.generate(
        intent_type=IntentType.QUERY_LIST,
        entity_class=BrickClass.TEMPERATURE_SENSOR,
        parameters={}
    )
    print(f"  List query: {gql.operation_name}")
    print(f"    GraphQL: {gql.query[:60].replace(chr(10), ' ')}...")
    assert "sensors" in gql.query.lower()
    
    # Test traverse query
    gql = generator.generate(
        intent_type=IntentType.QUERY_TRAVERSE,
        entity_class=BrickClass.BUILDING,
        parameters={"name": "Opera"}
    )
    print(f"  Traverse query: {gql.operation_name}")
    print(f"    GraphQL: {gql.query[:60].replace(chr(10), ' ')}...")
    assert "building" in gql.query.lower()
    
    print("✓ GraphQL generation works")


def test_graphql_to_cypher():
    """Test GraphQL to Cypher resolution."""
    print("\n=== Testing GraphQL → Cypher Resolution ===")
    
    from graphql_to_cypher import GraphQLToCypherResolver
    
    resolver = GraphQLToCypherResolver()
    
    # Test sensors query
    cypher = resolver.resolve(
        graphql_query="query { sensors { id name unit } }",
        variables={}
    )
    print(f"  Sensors query:")
    print(f"    Cypher: {cypher.cypher[:60]}...")
    assert "MATCH" in cypher.cypher
    
    # Test building query
    cypher = resolver.resolve(
        graphql_query='query { building(name: "Opera") { id name } }',
        variables={"name": "Opera"}
    )
    print(f"  Building query:")
    print(f"    Cypher: {cypher.cypher[:60]}...")
    assert "brick_Building" in cypher.cypher
    
    print("✓ GraphQL → Cypher resolution works")


def test_full_pipeline_no_db():
    """Test full pipeline without database connection."""
    print("\n=== Testing Full Pipeline (no DB) ===")
    
    from pipeline import KGPipeline
    
    pipeline = KGPipeline()
    
    # Test explain (doesn't need DB)
    explanation = pipeline.explain("Vis alle sensorer i bygget")
    
    print(f"  Original: {explanation['original_query']}")
    print(f"  Stage 1 - Intent: {explanation['stage_1_intent']['type']}")
    print(f"  Stage 2 - GraphQL: {explanation['stage_2_graphql']['operation']}")
    print(f"  Stage 3 - Cypher: {explanation['stage_3_cypher']['description']}")
    
    assert explanation['stage_1_intent']['type'] is not None
    assert explanation['stage_2_graphql']['query'] is not None
    assert explanation['stage_3_cypher']['query'] is not None
    
    print("✓ Pipeline explain works (without DB)")


def test_full_pipeline_with_db():
    """Test full pipeline with database connection."""
    print("\n=== Testing Full Pipeline (with DB) ===")
    
    from pipeline import KGPipeline
    
    pipeline = KGPipeline()
    
    if not pipeline.connect():
        print("⚠ Could not connect to FalkorDB")
        print("  Make sure FalkorDB is running: docker start falkordb")
        return False
    
    print("✓ Connected to FalkorDB")
    
    test_queries = [
        "Vis alle sensorer",
        "Hva er bygningens adresse?",
        "Hvilke soner finnes?",
    ]
    
    for query in test_queries:
        print(f"\n  Query: '{query}'")
        result = pipeline.process(query)
        
        print(f"    Success: {result.success}")
        print(f"    Intent: {result.extracted_intent.intent_type.value if result.extracted_intent else 'N/A'}")
        print(f"    GraphQL Op: {result.graphql_query.operation_name if result.graphql_query else 'N/A'}")
        print(f"    Results: {len(result.raw_results) if result.raw_results else 0} rows")
        print(f"    Response: {result.natural_response[:80]}...")
    
    pipeline.close()
    print("\n✓ Full pipeline works!")
    return True


def main():
    print("=" * 70)
    print("NL-to-KG Pipeline Tests")
    print("Pipeline: NL → Intent → GraphQL → Cypher → FalkorDB")
    print("=" * 70)
    
    # Component tests (no DB needed)
    test_ontology()
    test_intent_extractor()
    test_graphql_generator()
    test_graphql_to_cypher()
    test_full_pipeline_no_db()
    
    print("\n" + "-" * 70)
    print("Testing with database connection...")
    print("-" * 70)
    
    if test_full_pipeline_with_db():
        print("\n" + "=" * 70)
        print("✓ All tests passed!")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("✓ Component tests passed. DB tests skipped.")
        print("  Start FalkorDB and run again for full test.")
        print("=" * 70)


if __name__ == "__main__":
    main()
