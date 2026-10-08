from rest_framework.pagination import PageNumberPagination


class ProductPagination(PageNumberPagination):
    """
    Standard pagination for product listings. 
    Allows clients to control page size via the 'size' query parameter, 
    capped at a maximum of 50 items per page to prevent database strain.
    """
    # پارامتر size اندازه صفحه را تغییر می‌دهد و سقف پاسخ پنجاه محصول است.
    page_size = 20
    page_size_query_param = "size"
    max_page_size = 50
