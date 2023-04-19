import copy

from django.http import Http404
from rest_framework import status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from . import api_serializers
from . import models as m


class BigPaginator(PageNumberPagination):
    page_size = 100


class AthenaContentMetadataViewSet(viewsets.ModelViewSet):
    model = m.AthenaContentMetadata
    pagination_class = BigPaginator
    queryset = m.AthenaContentMetadata.objects.all()
    serializer_class = api_serializers.AthenaContentMetadataSerializer

    @staticmethod
    def _get_existing_metadata(data):
        try:
            return m.AthenaContentMetadata.objects.get(
                athena_content_id=data.get("athena_content_id")
            )
        except (m.AthenaContentMetadata.DoesNotExist, ValueError):
            return None

    def get_queryset(self):
        queryset = m.AthenaContentMetadata.objects.all()
        slug = self.request.query_params.get("slug", None)
        if slug:
            queryset = queryset.filter(slug=slug)
        return queryset

    def create(self, request):
        # handles creates _and_ updates via POST
        existing_metadata = self._get_existing_metadata(request.data)
        serializer = api_serializers.AthenaContentMetadataSerializer(
            data=request.data, instance=existing_metadata
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return_status = (
            status.HTTP_200_OK if existing_metadata else status.HTTP_201_CREATED
        )
        return Response(serializer.data, status=return_status)

    def destroy(self, request):
        # metadata entries do not need to be delete-able via the REST API
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class UserContentHistoryViewSet(viewsets.ModelViewSet):
    model = m.UserContentHistory
    pagination_class = BigPaginator
    queryset = m.UserContentHistory.objects.all()
    serializer_class = api_serializers.UserContentHistorySerializer

    def get_queryset(self):
        queryset = m.UserContentHistory.objects.all()
        email = self.request.query_params.get("email", None)
        if email:
            queryset = queryset.filter(email=email)
        return queryset

    def update(self, request):
        # content history entries do not need to be update-able via the REST API
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def destroy(self, request):
        # content history entries do not need to be delete-able via the REST API
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class AudienceUserViewSet(viewsets.ModelViewSet):
    model = m.AudienceUser
    serializer_class = api_serializers.AudienceUserSerializer
    queryset = m.AudienceUser.objects.all()

    def get_queryset(self):
        prefetch_fields = (
            "product_actions",
            "source_signups",
            "vars_history",
            "subscriptions",
            "subscriptions__list",
        )
        queryset = m.AudienceUser.objects.all().prefetch_related(*prefetch_fields)
        email = self.request.query_params.get("email", None)
        if email:
            queryset = queryset.filter(email=email)
        return queryset

    def destroy(self, request, pk):
        # disabled because for now we only want to handle user deletes via the admin,
        # where we have some special stuff to do the delete-at-Sailthru procedure
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class ListViewSet(viewsets.ModelViewSet):
    model = m.List
    pagination_class = BigPaginator
    queryset = m.List.objects.all()
    serializer_class = api_serializers.ListSerializer

    def get_queryset(self):
        queryset = m.List.objects.all().prefetch_related(
            "subscription_triggers__related_list"
        )

        list_type = self.request.query_params.get("type", None)
        if list_type:
            queryset = queryset.filter(type=list_type)
        slug = self.request.query_params.get("slug", None)
        if slug:
            queryset = queryset.filter(slug=slug)

        return queryset


class SubscriptionTriggerViewset(viewsets.ModelViewSet):
    model = m.SubscriptionTrigger
    queryset = m.SubscriptionTrigger.objects.all()
    serializer_class = api_serializers.SubscriptionTriggerSerializer

    def list(self, request, list_pk):
        try:
            queryset = (
                m.List.objects.get(pk=list_pk)
                .subscription_triggers.select_related("primary_list", "related_list")
                .prefetch_related(
                    "primary_list__subscription_triggers",
                    "primary_list__subscription_triggers__related_list",
                    "related_list__subscription_triggers__related_list",
                )
                .all()
            )
        except m.List.DoesNotExist:
            raise Http404
        serializer = api_serializers.SubscriptionTriggerSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk, list_pk):
        try:
            st = (
                m.List.objects.get(pk=list_pk)
                .subscription_triggers.select_related("primary_list", "related_list")
                .prefetch_related(
                    "primary_list__subscription_triggers",
                    "primary_list__subscription_triggers__related_list",
                    "related_list__subscription_triggers__related_list",
                )
                .get(pk=pk)
            )
        except (m.List.DoesNotExist, m.SubscriptionTrigger.DoesNotExist):
            raise Http404
        serializer = api_serializers.SubscriptionTriggerSerializer(st, many=False)
        return Response(serializer.data)

    def create(self, request, list_pk):
        payload = {}
        payload["primary_list_slug"] = m.List.objects.get(pk=list_pk).slug
        payload["related_list_slug"] = request.data.get("related_list_slug", None)
        payload["override_previous_unsubscribes"] = request.data.get(
            "override_previous_unsubscribes", None
        )
        serializer = api_serializers.SubscriptionTriggerSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, pk, list_pk):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class SubscriptionsViewset(viewsets.ModelViewSet):
    model = m.Subscription
    queryset = m.Subscription.objects.all()
    serializer_class = api_serializers.SubscriptionSerializer

    @staticmethod
    def _get_existing_subscription(data):
        try:
            audience_user = m.AudienceUser.objects.get(pk=data.get("audienceuser_pk"))
            list_ = m.List.objects.get(slug=data.get("list"))
            return m.Subscription.objects.get(audience_user=audience_user, list=list_)
        except (
            m.AudienceUser.DoesNotExist,
            m.List.DoesNotExist,
            m.Subscription.DoesNotExist,
            ValueError,
        ):
            return None

    def list(self, request, audienceuser_pk):
        try:
            queryset = (
                m.AudienceUser.objects.get(pk=audienceuser_pk)
                .subscriptions.select_related("list")
                .all()
            )
        except m.AudienceUser.DoesNotExist:
            raise Http404
        serializer = api_serializers.SubscriptionSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk, audienceuser_pk):
        try:
            s = (
                m.AudienceUser.objects.get(pk=audienceuser_pk)
                .subscriptions.select_related("list")
                .get(pk=pk)
            )
        except (m.AudienceUser.DoesNotExist, m.Subscription.DoesNotExist, ValueError):
            raise Http404
        serializer = api_serializers.SubscriptionSerializer(s, many=False)
        return Response(serializer.data)

    def create(self, request, audienceuser_pk):
        # handles creates _and_ updates via POST
        data = copy.deepcopy(request.data)
        if "active" not in data:
            data["active"] = True
        data["audienceuser_pk"] = audienceuser_pk
        existing_subscription = self._get_existing_subscription(data)
        serializer = api_serializers.SubscriptionSerializer(
            data=data, instance=existing_subscription
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return_status = (
            status.HTTP_200_OK if existing_subscription else status.HTTP_201_CREATED
        )
        return Response(serializer.data, status=return_status)

    def update(self, request, pk, audienceuser_pk):
        # updates happen via POST/create() -- see above; there is no good reason
        # to provide a separate mode of updating list subscriptions at this time,
        # and it is easier to do everything through POST
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def destroy(self, request, pk, audienceuser_pk):
        # right now we do not have a reason to be able to delete subscriptions
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def partial_update(self, request, pk, audienceuser_pk):
        # no need to implement PATCH
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class OptoutHistoryViewset(viewsets.ModelViewSet):
    model = m.OptoutHistory
    queryset = m.OptoutHistory.objects.all()
    serializer_class = api_serializers.OptoutHistorySerializer

    def list(self, request, audienceuser_pk):
        try:
            audience_user = m.AudienceUser.objects.get(pk=audienceuser_pk)
            optout_history_qs = audience_user.optout_history.all()
        except m.AudienceUser.DoesNotExist:
            raise Http404
        serializer = api_serializers.OptoutHistorySerializer(
            optout_history_qs, many=True
        )
        return Response(serializer.data)

    def retrieve(self, request, pk, audienceuser_pk):
        try:
            audience_user = m.AudienceUser.objects.get(pk=audienceuser_pk)
            single_optout_history = audience_user.optout_history.get(pk=pk)
        except (m.AudienceUser.DoesNotExist, m.OptoutHistory.DoesNotExist, ValueError):
            raise Http404
        serializer = api_serializers.OptoutHistorySerializer(
            single_optout_history, many=False
        )
        return Response(serializer.data)

    def create(self, request, audienceuser_pk):
        # handles creates _and_ updates via POST
        data = copy.deepcopy(request.data)
        data["audience_user"] = audienceuser_pk
        # existing_optout_history = self._get_existing_subscription(data)
        existing_optout_history = None
        serializer = api_serializers.OptoutHistorySerializer(
            data=data, instance=existing_optout_history
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return_status = (
            status.HTTP_200_OK if existing_optout_history else status.HTTP_201_CREATED
        )
        return Response(serializer.data, status=return_status)

    def update(self, request, pk, audienceuser_pk):
        """
        Updates happen via POST/create() -- see above
        Following the lead of SubscriptionsViewset
        """
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def destroy(self, request, pk, audienceuser_pk):
        # Following the lead of SubscriptionsViewset
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def partial_update(self, request, pk, audienceuser_pk):
        # Following the lead of SubscriptionsViewset
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class ProductViewSet(viewsets.ModelViewSet):
    model = m.Product
    pagination_class = BigPaginator
    queryset = m.Product.objects.all()
    serializer_class = api_serializers.ProductSerializer

    def get_queryset(self):
        queryset = m.Product.objects.all().prefetch_related("subtypes", "topics")
        slug = self.request.query_params.get("slug", None)
        if slug:
            queryset = queryset.filter(slug=slug)
        return queryset

    def update(self, request, pk):
        # products are not currently update-able via the REST API
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def destroy(self, request, pk):
        # products do not need to be delete-able via the REST API
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class ProductSubtypesViewSet(viewsets.ModelViewSet):
    model = m.ProductSubtype
    queryset = m.ProductSubtype.objects.all()
    serializer_class = api_serializers.ProductSubtypeSerializer

    def update(self, request, pk):
        # product subtypes are not currently update-able
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class ProductTopicViewSet(viewsets.ModelViewSet):
    model = m.ProductTopic
    queryset = m.ProductTopic.objects.all()
    serializer_class = api_serializers.ProductTopicSerializer

    def update(self, request, pk):
        # product topics are not currently update-able
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class ProductActionsViewset(viewsets.ModelViewSet):
    model = m.ProductAction
    queryset = m.ProductAction.objects.all()
    serializer_class = api_serializers.ProductActionSerializer

    @staticmethod
    def _get_existing_product_action(data):
        try:
            audience_user = m.AudienceUser.objects.get(pk=data.get("audienceuser_pk"))
            product = m.Product.objects.get(slug=data.get("product"))
            action_type = data.get("type")
            return m.ProductAction.objects.get(
                audience_user=audience_user, product=product, type=action_type
            )
        except (
            m.AudienceUser.DoesNotExist,
            m.Product.DoesNotExist,
            m.ProductAction.DoesNotExist,
            ValueError,
        ):
            return None

    def list(self, request, audienceuser_pk):
        try:
            queryset = (
                m.AudienceUser.objects.get(pk=audienceuser_pk)
                .product_actions.select_related("product")
                .prefetch_related("details", "product__subtypes", "product__topics")
                .all()
            )
        except m.AudienceUser.DoesNotExist:
            raise Http404
        serializer = api_serializers.ProductActionSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk, audienceuser_pk):
        try:
            pa = (
                m.AudienceUser.objects.get(pk=audienceuser_pk)
                .product_actions.select_related("product")
                .prefetch_related("details", "product__subtypes", "product__topics")
                .get(pk=pk)
            )
        except (m.AudienceUser.DoesNotExist, m.ProductAction.DoesNotExist, ValueError):
            raise Http404
        serializer = api_serializers.ProductActionSerializer(pa, many=False)
        return Response(serializer.data)

    def create(self, request, audienceuser_pk):
        # handles creates _and_ updates via POST
        data = copy.deepcopy(request.data)
        data["audienceuser_pk"] = audienceuser_pk
        existing_action = self._get_existing_product_action(data)
        serializer = api_serializers.ProductActionSerializer(
            data=data, instance=existing_action
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return_status = (
            status.HTTP_200_OK if existing_action else status.HTTP_201_CREATED
        )
        return Response(serializer.data, status=return_status)

    def update(self, request, pk, audienceuser_pk):
        # updates happen via POST/create() -- see above; there is no good reason
        # to provide a separate mode of updating product actions at this time,
        # and it is easier to do everything through POST
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def destroy(self, request, pk, audienceuser_pk):
        # right now we do not have a reason to be able to delete product actions
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def partial_update(self, request, pk, audienceuser_pk):
        # no need to implement PATCH for now
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class VarKeyViewSet(viewsets.ModelViewSet):
    model = m.VarKey
    pagination_class = BigPaginator
    queryset = m.VarKey.objects.all()
    serializer_class = api_serializers.VarKeySerializer
