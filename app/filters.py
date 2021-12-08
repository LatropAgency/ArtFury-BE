from rest_framework.filters import BaseFilterBackend


class OrderPriceFilter(BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        min_price = request.query_params.get('min_price', None)
        max_price = request.query_params.get('max_price', None)
        try:
            if min_price:
                queryset = queryset.filter(price__gte=int(min_price))
            if max_price:
                queryset = queryset.filter(price__lte=int(max_price))
        except Exception:
            return queryset.order_by('-created_at')
        return queryset.order_by('-created_at')
