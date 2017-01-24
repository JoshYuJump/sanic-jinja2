#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import partial
from sanic.response import html
from jinja2 import Environment, PackageLoader


class SanicJinja2:
    def __init__(self, app=None, jinja_loader=None, **kwargs):
        self.env = Environment(**kwargs)
        if app:
            self.init_app(app, jinja_loader)

    def init_app(self, app, loader=None):
        if not hasattr(app, 'extensions'):
            app.extensions = {}

        app.extensions['jinja2'] = self
        if not loader:
            loader = PackageLoader(app.name, 'templates')

        self.env.loader = loader
        self.env.globals['app'] = app

        @app.middleware('request')
        async def hook_request_to_jinja2(request):
            self.flash = partial(self._flash, request)
            self.env.globals['request'] = request
            self.env.globals['get_flashed_messages'] = \
                partial(self._get_flashed_messages, request)

    def render_string(self, template, **context):
        return self.env.get_template(template).render(**context)

    def render(self, template, **context):
        return html(self.render_string(template, **context))

    def _flash(self, request, message, category='message'):
        '''need sanic_session extension'''
        if 'session' in request:
            flashes = request['session'].get('_flashes', [])
            flashes.append((category, message))
            request['session']['_flashes'] = flashes

    def _get_flashed_messages(self, request, with_categories=False,
                              category_filter=[]):
        if 'session' not in request:
            return []

        flashes = request['session'].pop('_flashes') \
            if '_flashes' in request['session'] else []

        if category_filter:
            flashes = list(filter(lambda f: f[0] in category_filter, flashes))

        if not with_categories:
            return [x[1] for x in flashes]

        return flashes