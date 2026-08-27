from strawberry.fastapi import GraphQLRouter

from app.graphql.context import get_graphql_context
from app.graphql.schema import schema
from config.settings import settings

graphql_router = GraphQLRouter(
    schema,
    context_getter=get_graphql_context,
    # GraphiQL is a dev convenience, not something to expose in prod.
    graphql_ide="graphiql" if settings.debug else None,
)
