"""
NL-to-KG: Natural Language to Knowledge Graph Pipeline

Converts natural language queries to GraphQL, then to Cypher queries 
for FalkorDB using Brick Ontology schema for building/energy domain.

Pipeline:
    NL → Intent → GraphQL → Cypher → FalkorDB → Response
"""

from pipeline import KGPipeline
from ontology import BrickOntology, BrickClass, IntentType
from intent_extractor import IntentExtractor, ExtractedIntent
from graphql_generator import GraphQLGenerator, GeneratedGraphQL
from graphql_to_cypher import GraphQLToCypherResolver, CypherQuery

__version__ = "0.1.0"
__all__ = [
    "KGPipeline",
    "BrickOntology",
    "BrickClass",
    "IntentType",
    "IntentExtractor", 
    "ExtractedIntent",
    "GraphQLGenerator",
    "GeneratedGraphQL",
    "GraphQLToCypherResolver",
    "CypherQuery"
]
