from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, mixins, filters
from rest_framework import permissions, authentication, status

from recipe import serializers
from core.models import Tag, Ingredient, Recipe, User


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """
    The request is authenticated as a user, or is a read-only request.
    """

    def has_permission(self, request, view):
        if (request.method in permissions.SAFE_METHODS):
            return True
        if(request.user.is_authenticated and request.method == 'POST'):
            return True
        if (request.user and request.user.is_authenticated):
            try:
                recipe = Recipe.objects.get(id=int(view.kwargs['pk']))
            except:
                return False
            if(recipe.user == request.user):
                return True
        return False


class BaseListViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        queryset = self.queryset

        assigned_only = bool(
            int(self.request.query_params.get('assigned_only', 0))
        )
        mine = self.request.query_params.get('mine', 0)

        if assigned_only:
            queryset = queryset.filter(recipe__isnull=False)

        if self.request.user.is_authenticated and mine:
            return queryset.filter(user=self.request.user).distinct()

        return queryset.order_by('name')


class BaseCreateViewSet(viewsets.GenericViewSet,
                        mixins.CreateModelMixin):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    authentication_classes = (authentication.TokenAuthentication,)

    def perform_create(self, serializer):
        return serializer.save(user=self.request.user)


class TagViewSet(BaseListViewSet, BaseCreateViewSet):
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()
    search_fields = ['name']
    filter_backends = (filters.SearchFilter,)


class IngredientViewSet(BaseListViewSet, BaseCreateViewSet):
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()
    search_fields = ['name']
    filter_backends = (filters.SearchFilter,)


class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.RecipeSerializer
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    authentication_classes = (authentication.TokenAuthentication,)

    def retrieve(self, request, *args, **kwargs):
        fav = False
        if not self.request.user.is_anonymous:
            fav = self.queryset.filter(
                user_favourites=self.request.user, id=self.kwargs['pk']).exists()
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({**serializer.data, 'favourites': fav})

    def query_params_to_ints(self, qs):
        return [int(id) for id in qs.split(',')]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):

        if self.action == 'retrieve':
            return serializers.RecipeDetailSerializer
        elif self.action == 'upload_image':
            return serializers.RecipeImageSerializer

        return serializers.RecipeSerializer

    def get_queryset(self):

        queryset = Recipe.objects.all()
        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredients')
        mine = self.request.query_params.get('mine')

        if tags:
            tag_ids = self.query_params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)

        if ingredients:
            ingredient_ids = self.query_params_to_ints(ingredients)
            queryset = queryset.filter(ingredients__id__in=ingredient_ids)

        if self.request.user.is_authenticated and mine:
            return queryset.filter(user=self.request.user)
        return queryset.order_by('title')

    @action(methods=['GET', 'POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        recipe = self.get_object()
        serializer = self.get_serializer(
            recipe,
            data=request.data
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                data=serializer.data,
                status=status.HTTP_200_OK
            )
        return Response(
            data=serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
