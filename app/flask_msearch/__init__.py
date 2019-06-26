#!/usr/bin/env python
# -*- coding: utf-8 -*-
# **************************************************************************
# Copyright © 2017-2019 jianglin
# File Name: __init__.py
# Author: jianglin
# Email: mail@honmaple.com
# Created: 2017-04-15 20:03:18 (CST)
# Last Update: Monday 2018-12-17 10:27:44 (CST)
#          By:
# Description:
# **************************************************************************
from .whoosh_backend import WhooshSearch


class Search(object):
    def __init__(self, app=None, db=None, analyzer=None):
        """
        You can custom analyzer by::

            from jieba.analyse import ChineseAnalyzer
            search = Search(analyzer = ChineseAnalyzer)
        """
        self.db = db
        self.analyzer = analyzer
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.config.setdefault('MSEARCH_BACKEND', 'simple')
        self._backend = WhooshSearch(app, self.db, self.analyzer)

    def __getattr__(self, name):
        return getattr(self._backend, name)
