from django.core.paginator import Paginator

from yatube.settings import PAGES_NUMBER


def get_paginator(request, page):
    paginator = Paginator(page, PAGES_NUMBER)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
