from rest_framework import routers
from rest_framework_nested import routers as nested_routers

from . import api_views


athena_content_metadata_router = nested_routers.SimpleRouter(trailing_slash=False)
athena_content_metadata_router.register(
    "athena-content-metadata", api_views.AthenaContentMetadataViewSet
)

user_content_history_router = nested_routers.SimpleRouter(trailing_slash=False)
user_content_history_router.register(
    "user-content-history", api_views.UserContentHistoryViewSet
)


audienceusers_router = nested_routers.SimpleRouter(trailing_slash=False)
audienceusers_router.register(r"audience-users", api_views.AudienceUserViewSet)


subscriptions_router = nested_routers.NestedSimpleRouter(
    audienceusers_router, "audience-users", lookup="audienceuser", trailing_slash=False
)
subscriptions_router.register("subscriptions", api_views.SubscriptionsViewset)


product_actions_router = nested_routers.NestedSimpleRouter(
    audienceusers_router, "audience-users", lookup="audienceuser", trailing_slash=False
)
product_actions_router.register("product-actions", api_views.ProductActionsViewset)


optouthistory_router = nested_routers.NestedSimpleRouter(
    audienceusers_router, "audience-users", lookup="audienceuser", trailing_slash=False
)
optouthistory_router.register("optout-history", api_views.OptoutHistoryViewset)


lists_router = nested_routers.SimpleRouter(trailing_slash=False)
lists_router.register(r"lists", api_views.ListViewSet)


subscription_triggers_router = nested_routers.NestedSimpleRouter(
    lists_router, "lists", lookup="list", trailing_slash=False
)
subscription_triggers_router.register(
    "subscription-triggers", api_views.SubscriptionTriggerViewset
)


products_router = nested_routers.SimpleRouter(trailing_slash=False)
products_router.register("products", api_views.ProductViewSet)


product_subtypes_router = nested_routers.SimpleRouter(trailing_slash=False)
product_subtypes_router.register("product-subtypes", api_views.ProductSubtypesViewSet)


product_topics_router = nested_routers.SimpleRouter(trailing_slash=False)
product_topics_router.register("product-topics", api_views.ProductTopicViewSet)


varkey_router = routers.SimpleRouter(trailing_slash=False)
varkey_router.register(r"vars", api_views.VarKeyViewSet)


urlpatterns = (
    athena_content_metadata_router.urls
    + user_content_history_router.urls
    + audienceusers_router.urls
    + product_actions_router.urls
    + subscriptions_router.urls
    + optouthistory_router.urls
    + lists_router.urls
    + subscription_triggers_router.urls
    + products_router.urls
    + product_subtypes_router.urls
    + product_topics_router.urls
    + varkey_router.urls
)
