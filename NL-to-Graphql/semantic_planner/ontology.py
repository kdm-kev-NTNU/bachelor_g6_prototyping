"""
Domain Ontology - Defines the semantic model for the GraphQL schema.

This module maps natural language concepts to GraphQL operations and types.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class IntentType(Enum):
    """Types of user intents."""
    QUERY_LIST = "query_list"           # Get all items
    QUERY_SINGLE = "query_single"       # Get one item by ID
    QUERY_FILTERED = "query_filtered"   # Get items with filter
    MUTATION_CREATE = "mutation_create" # Create new item
    MUTATION_UPDATE = "mutation_update" # Update existing item
    MUTATION_DELETE = "mutation_delete" # Delete item
    UNKNOWN = "unknown"


class EntityType(Enum):
    """Domain entity types mapped to GraphQL types."""
    USER = "user"
    POST = "post"
    PRODUCT = "product"


@dataclass
class EntityField:
    """Represents a field in an entity."""
    name: str
    graphql_name: str
    field_type: str
    description: str
    is_relation: bool = False
    related_entity: Optional[str] = None


@dataclass
class Entity:
    """Represents a domain entity with its fields and operations."""
    name: str
    graphql_type: str
    description: str
    fields: List[EntityField]
    
    # Natural language synonyms for this entity
    synonyms: List[str] = field(default_factory=list)
    
    def get_field_names(self) -> List[str]:
        return [f.name for f in self.fields]
    
    def get_graphql_field_names(self) -> List[str]:
        return [f.graphql_name for f in self.fields]


@dataclass
class Operation:
    """Represents a GraphQL operation."""
    name: str
    graphql_name: str
    intent_type: IntentType
    entity: EntityType
    parameters: Dict[str, str]  # param_name -> graphql_type
    returns: str
    description: str


class DomainOntology:
    """
    Domain ontology that maps natural language concepts to GraphQL schema.
    
    This is the central knowledge base for the semantic planner.
    """
    
    def __init__(self):
        self.entities: Dict[EntityType, Entity] = {}
        self.operations: Dict[str, Operation] = {}
        self.intent_patterns: Dict[IntentType, List[str]] = {}
        
        self._initialize_entities()
        self._initialize_operations()
        self._initialize_intent_patterns()
    
    def _initialize_entities(self):
        """Define domain entities based on GraphQL schema."""
        
        # User entity
        self.entities[EntityType.USER] = Entity(
            name="user",
            graphql_type="UserType",
            description="A user in the system with name and email",
            fields=[
                EntityField("id", "id", "Int", "Unique identifier"),
                EntityField("name", "name", "String", "User's full name"),
                EntityField("email", "email", "String", "User's email address"),
            ],
            synonyms=["bruker", "person", "member", "account", "konto", "menneske"]
        )
        
        # Post entity
        self.entities[EntityType.POST] = Entity(
            name="post",
            graphql_type="PostType",
            description="A blog post with title, content and author",
            fields=[
                EntityField("id", "id", "Int", "Unique identifier"),
                EntityField("title", "title", "String", "Post title"),
                EntityField("content", "content", "String", "Post content/body"),
                EntityField("authorId", "authorId", "Int", "ID of the author"),
                EntityField("author", "author", "UserType", "The post author", 
                           is_relation=True, related_entity="user"),
            ],
            synonyms=["innlegg", "artikkel", "article", "blog", "blogg", "tekst"]
        )
        
        # Product entity
        self.entities[EntityType.PRODUCT] = Entity(
            name="product",
            graphql_type="ProductType",
            description="A product with name, price and description",
            fields=[
                EntityField("id", "id", "Int", "Unique identifier"),
                EntityField("name", "name", "String", "Product name"),
                EntityField("price", "price", "Float", "Product price"),
                EntityField("description", "description", "String", "Product description"),
            ],
            synonyms=["produkt", "vare", "item", "ting", "gjenstand"]
        )
    
    def _initialize_operations(self):
        """Define available GraphQL operations."""
        
        # Query operations
        self.operations["get_users"] = Operation(
            name="get_users",
            graphql_name="users",
            intent_type=IntentType.QUERY_LIST,
            entity=EntityType.USER,
            parameters={},
            returns="List[UserType]",
            description="Get all users"
        )
        
        self.operations["get_user"] = Operation(
            name="get_user",
            graphql_name="user",
            intent_type=IntentType.QUERY_SINGLE,
            entity=EntityType.USER,
            parameters={"id": "Int!"},
            returns="UserType",
            description="Get a specific user by ID"
        )
        
        self.operations["get_posts"] = Operation(
            name="get_posts",
            graphql_name="posts",
            intent_type=IntentType.QUERY_LIST,
            entity=EntityType.POST,
            parameters={},
            returns="List[PostType]",
            description="Get all posts"
        )
        
        self.operations["get_post"] = Operation(
            name="get_post",
            graphql_name="post",
            intent_type=IntentType.QUERY_SINGLE,
            entity=EntityType.POST,
            parameters={"id": "Int!"},
            returns="PostType",
            description="Get a specific post by ID"
        )
        
        self.operations["get_products"] = Operation(
            name="get_products",
            graphql_name="products",
            intent_type=IntentType.QUERY_LIST,
            entity=EntityType.PRODUCT,
            parameters={},
            returns="List[ProductType]",
            description="Get all products"
        )
        
        self.operations["get_product"] = Operation(
            name="get_product",
            graphql_name="product",
            intent_type=IntentType.QUERY_SINGLE,
            entity=EntityType.PRODUCT,
            parameters={"id": "Int!"},
            returns="ProductType",
            description="Get a specific product by ID"
        )
        
        # Mutation operations
        self.operations["create_user"] = Operation(
            name="create_user",
            graphql_name="createUser",
            intent_type=IntentType.MUTATION_CREATE,
            entity=EntityType.USER,
            parameters={"name": "String!", "email": "String!"},
            returns="UserType",
            description="Create a new user"
        )
        
        self.operations["create_post"] = Operation(
            name="create_post",
            graphql_name="createPost",
            intent_type=IntentType.MUTATION_CREATE,
            entity=EntityType.POST,
            parameters={"title": "String!", "content": "String!", "authorId": "Int!"},
            returns="PostType",
            description="Create a new post"
        )
    
    def _initialize_intent_patterns(self):
        """Define natural language patterns for each intent type."""
        
        self.intent_patterns[IntentType.QUERY_LIST] = [
            "get all", "show all", "list all", "find all", "fetch all",
            "hent alle", "vis alle", "list opp", "finn alle",
            "what are", "show me", "give me all",
            "hva er", "vis meg", "gi meg alle"
        ]
        
        self.intent_patterns[IntentType.QUERY_SINGLE] = [
            "get the", "find the", "show the", "fetch the",
            "get user", "get post", "get product",
            "with id", "by id", "number",
            "hent", "finn", "vis", "med id", "nummer"
        ]
        
        self.intent_patterns[IntentType.MUTATION_CREATE] = [
            "create", "add", "new", "make", "insert",
            "opprett", "lag", "ny", "legg til", "sett inn"
        ]
        
        self.intent_patterns[IntentType.MUTATION_UPDATE] = [
            "update", "change", "modify", "edit",
            "oppdater", "endre", "modifiser", "rediger"
        ]
        
        self.intent_patterns[IntentType.MUTATION_DELETE] = [
            "delete", "remove", "drop",
            "slett", "fjern", "ta bort"
        ]
    
    def get_entity(self, entity_type: EntityType) -> Optional[Entity]:
        """Get entity definition by type."""
        return self.entities.get(entity_type)
    
    def get_operation(self, operation_name: str) -> Optional[Operation]:
        """Get operation definition by name."""
        return self.operations.get(operation_name)
    
    def find_entity_by_text(self, text: str) -> Optional[EntityType]:
        """Find entity type from natural language text."""
        text_lower = text.lower()
        
        for entity_type, entity in self.entities.items():
            # Check entity name
            if entity.name in text_lower:
                return entity_type
            # Check synonyms
            for synonym in entity.synonyms:
                if synonym in text_lower:
                    return entity_type
        
        return None
    
    def find_operation(self, intent: IntentType, entity: EntityType) -> Optional[Operation]:
        """Find the matching operation for an intent and entity."""
        for op in self.operations.values():
            if op.intent_type == intent and op.entity == entity:
                return op
        return None
    
    def get_all_entity_synonyms(self) -> Dict[str, EntityType]:
        """Get a mapping of all synonyms to entity types."""
        synonyms = {}
        for entity_type, entity in self.entities.items():
            synonyms[entity.name] = entity_type
            for syn in entity.synonyms:
                synonyms[syn] = entity_type
        return synonyms
    
    def to_dict(self) -> Dict[str, Any]:
        """Export ontology as dictionary for LLM context."""
        return {
            "entities": {
                et.value: {
                    "name": e.name,
                    "type": e.graphql_type,
                    "fields": [f.graphql_name for f in e.fields],
                    "synonyms": e.synonyms
                }
                for et, e in self.entities.items()
            },
            "operations": {
                name: {
                    "graphql": op.graphql_name,
                    "intent": op.intent_type.value,
                    "entity": op.entity.value,
                    "params": op.parameters
                }
                for name, op in self.operations.items()
            }
        }
