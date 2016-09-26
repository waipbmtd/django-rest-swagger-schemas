#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@date: 2016-09-22

@author: Devin
"""


class DocBase(object):
    def __init__(self):
        self._dict = dict()

    def dict(self):
        return self._dict

    def __getattr__(self, name):
        return self._dict.get(name, "")


class Field(DocBase):
    def __init__(self, name, required=False, location='query', description="",
                 ftype="string", **kwargs):
        super(Field, self).__init__()
        self._dict.update(name=name,
                          required=required,
                          location=location,
                          description=description,
                          type=ftype)
        self._dict.update(kwargs)


class Link(DocBase):
    def __init__(self, description="", summary="", **kwargs):
        super(Link, self).__init__()
        self._dict.update(summary=summary,
                          description=description
                          )
        self._dict.update(kwargs)


class ScResponse(DocBase):
    def __init__(self, code=200, description="", ftype="string", serial=None,
                 **kwargs):
        super(ScResponse, self).__init__()
        if ftype == "schema":
            self._dict.update({code: dict(description=description,
                                          schema=serial)})
        elif ftype == "string":
            self._dict.update({code: dict(description=description,
                                          type=ftype)})
        self._dict.get(code).update(kwargs)


class Tag(DocBase):
    def __init__(self, name="", description="", **kwargs):
        super(Tag, self).__init__()
        self._dict.update(name=name,
                          description=description)
