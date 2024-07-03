from __future__ import annotations

import typing as t
import re

from restcraft.core import JSONResponse, Request, View
from restcraft.core.di import inject

from ... import exceptions, utils

if t.TYPE_CHECKING:
    from ...services.manga import MangaService
    from ...services.request import RequestService

MANGA_UPDATES_URL = 'https://manganato.com/genre-all'

MANGA_INFO_URL_PREFIX = {
    'cu': 'https://chapmanganato.to',
    'mu': 'https://manganato.com',
}


class MangaView(View):
    """
    Defines the `MangaView` class, which is a view for handling requests to the
    `/mangas` route.

    This view is responsible for fetching and returning the latest manga
    updates.
    """

    route = '/v1/mangas'
    methods = ['GET']

    @inject
    def handler(self, req: Request, service: MangaService, request: RequestService) -> JSONResponse:
        page = 1
        search = None
        
        if req.query:
            page = req.query.get('page', default=1, type=int)
            search = req.query.get('q', type=str)

        if search:
            updates = service.search(search, page)
        else:
            updates = service.updates(page)


        resp = request.get(
            MANGA_UPDATES_URL + f'{"/%s" % page if page > 1 else ""}'
        )

        select = utils.get_selector(resp.text)
        
        text = select('//div[@class="group-page"]/a[@class="page-blue page-last"]/text()').get()
        numbers = re.findall('\d+\.\d+|\d+', text)
        num_ttps = int(numbers[0])
        print(numbers[0])


        return utils.success_response(
            'Latest manga updates fetched successful.', payload=updates, ttps=num_ttps, current_page=page
        )


class MangaInfoView(View):
    """
    Defines the `MangaInfoView` class, which is a view for handling requests to
    the `/mangas/<manga>` route.

    This view is responsible for fetching and returning detailed information
    about a specific manga.
    """

    route = '/v1/mangas/<manga>'
    methods = ['GET']

    def before_handler(self, req: Request) -> None:
        prefix, _, manga = req.params['manga'].partition('-')
        req.set_params = {'prefix': prefix, 'manga': manga}

    @inject
    def handler(self, req: Request, service: MangaService) -> JSONResponse:
        manga_info = service.info(
            prefix=req.params['prefix'], manga=req.params['manga']
        )

        return utils.success_response(
            'Latest manga info fetched successful.', payload=manga_info,ttps=0,current_page=0
        )

    def on_exception(self, req: Request, exc: Exception) -> JSONResponse:
        if not isinstance(exc, exceptions.NotFound):
            raise exc

        return utils.error_response(
            status_code=404,
            message='Manga not found.',
            exception_code='MANGA_NOT_FOUND',
        )
