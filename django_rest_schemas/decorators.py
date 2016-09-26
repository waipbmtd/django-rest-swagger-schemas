#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@date: 2016-09-21

@author: Devin
"""


def render_parmeters(*fields):
    def decorator(func):
        func.render_fields = [kv.dict() for kv in fields]
        return func

    return decorator


def render_link(link):
    def decorator(func):
        func.render_link = link.dict()
        return func

    return decorator


def render_responses(*response):
    def decorator(func):
        t_dict = dict()
        map(lambda resp: t_dict.update(resp.dict()), response)
        func.render_responses = t_dict
        return func

    return decorator


def rander_tag(tag):
    def decorator(func):
        func.render_tag = tag
        return func

    return decorator


def render_serializer(serial):
    def decorator(func):
        func.render_serializer = serial
        return func

    return decorator
