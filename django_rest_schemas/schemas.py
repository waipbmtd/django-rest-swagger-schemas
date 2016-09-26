#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@date: 2016-09-21

@author: Devin
"""
import copy
import inspect
from collections import OrderedDict

from rest_framework.schemas import *


class CoreApiSchemaGenerator(SchemaGenerator):
    def __init__(self, title=None, url=None, patterns=None, urlconf=None,
                 **kwargs):
        super(CoreApiSchemaGenerator, self).__init__(title, url, patterns,
                                                     urlconf)
        self.tag_dict = OrderedDict()
        self.definitions = OrderedDict()

    def get_schema(self, request=None):
        if self.endpoints is None:
            self.endpoints = self.get_api_endpoints(self.patterns)

        links = []
        for path, method, category, action, callback in self.endpoints:
            view = callback.cls()
            for attr, val in getattr(callback, 'initkwargs', {}).items():
                setattr(view, attr, val)
            view.args = ()
            view.kwargs = {}
            view.format_kwarg = None

            if request is not None:
                view.request = clone_request(request, method)
                try:
                    view.check_permissions(view.request)
                except exceptions.APIException:
                    continue
            else:
                view.request = None

            link = self.get_link(path, method, callback, view)
            links.append((category, action, link))

        if not links:
            return None

        # Generate the schema content structure, eg:
        # {'users': {'list': Link()}}
        content = {}
        for category, action, link in links:
            if category is None:
                content[action] = link
            elif category in content:
                content[category][action] = link
            else:
                content[category] = {action: link}

        # Return the schema document.
        return coreapi.Document(title=self.title, content=content,
                                url=self.url, tags=self.tags,
                                definitions=self.definitions)

    def get_link(self, path, method, callback, view):
        """
        Return a `coreapi.Link` instance for the given endpoint.
        """
        fields = self.get_render_fields(view, method)
        if not fields:
            fields = self.get_path_fields(path, method, callback, view)
            fields += self.get_serializer_fields(path, method, callback, view)
            fields += self.get_pagination_fields(path, method, callback, view)
            fields += self.get_filter_fields(path, method, callback, view)

        if fields and any(
                [field.location in ('form', 'body') for field in fields]):
            encoding = self.get_encoding(path, method, callback, view)
        else:
            encoding = None

        if self.url and path.startswith('/'):
            path = path[1:]

        render_responses = self.get_render_response(view, method)
        render_link = self.get_render_link(view, method)
        link_kwargs = dict(
            url=urlparse.urljoin(self.url, path),
            action=method.lower(),
            encoding=encoding,
            responses=render_responses,
            fields=fields
        )
        link_kwargs.update(render_link)

        return coreapi.Link(**link_kwargs)

    def get_api_endpoints(self, patterns, prefix=''):
        """
        Return a list of all available API endpoints by inspecting the URL conf.
        """
        api_endpoints = []

        for pattern in patterns:
            path_regex = prefix + pattern.regex.pattern
            if isinstance(pattern, RegexURLPattern):
                path = self.get_path(path_regex)
                callback = pattern.callback
                if self.should_include_endpoint(path, callback):
                    for method in self.get_allowed_methods(callback):
                        action = self.get_action(path, method, callback)
                        category, desc = self.get_category(path, method,
                                                           callback.cls(),
                                                           action)
                        endpoint = (path, method, category, action, callback)
                        api_endpoints.append(endpoint)
                        self.add_tag_dict(category, desc)

            elif isinstance(pattern, RegexURLResolver):
                nested_endpoints = self.get_api_endpoints(
                    patterns=pattern.url_patterns,
                    prefix=path_regex
                )
                api_endpoints.extend(nested_endpoints)

        return api_endpoints

    def add_serializer_to_definition(self, method_serializer):
        """
        add definition to definitions
        """

        if not isinstance(method_serializer, serializers.Serializer):
            return

        serial_name = method_serializer.__class__.__name__
        if self.definitions.has_key(serial_name):
            return

        serial_dict = dict(type="object")
        properties = dict()

        for field in method_serializer.fields.values():
            field_name = field.field_name
            if isinstance(field, serializers.Serializer):
                self.add_serializer_to_definition(field)
                properties[field_name] = {"$ref": "#/definitions/"+field.__class__.__name__}
            else:
                properties[field_name] = dict(type='string',
                                               description=force_text(field.help_text) if field.help_text else '')
        serial_dict["properties"] = properties
        self.definitions[serial_name] = serial_dict

    def get_category(self, path, method, callback, action):
        """
        Return a descriptive category string for the endpoint, eg. 'users'.

        Examples of category/action pairs that should be generated for various
        endpoints:

        /users/                     [users][list], [users][create]
        /users/{pk}/                [users][read], [users][update], [users][destroy]
        /users/enabled/             [users][enabled]  (custom action)
        /users/{pk}/star/           [users][star]     (custom action)
        /users/{pk}/groups/         [groups][list], [groups][create]
        /users/{pk}/groups/{pk}/    [groups][read], [groups][update], [groups][destroy]
        """
        tag, desc = self.get_class_tag(callback, method)
        if tag:
            return tag, desc

        tag, desc = self.get_view_tag(callback, method)
        if tag:
            return tag, desc

        return self.get_default_tag(path, action)

    def get_render_fields(self, view, method):
        """
        Return a list of the valid HTTP methods for this endpoint.
        """
        lower_method = method.lower()
        if not hasattr(view, lower_method):
            return []

        origin_method = getattr(view, lower_method)
        if not inspect.ismethod(origin_method):
            return []

        if hasattr(origin_method, 'render_fields'):
            return [coreapi.Field(**kv) for kv in origin_method.render_fields]
        return []

    def get_render_link(self, view, method):
        lower_method = method.lower()
        if not hasattr(view, lower_method):
            return {}

        origin_method = getattr(view, lower_method)
        if not inspect.ismethod(origin_method):
            return {}

        if hasattr(origin_method, 'render_link'):
            return origin_method.render_link
        return {}

    def get_render_response(self, view, method):
        lower_method = method.lower()
        if not hasattr(view, lower_method):
            return {}

        origin_method = getattr(view, lower_method)
        if not inspect.ismethod(origin_method):
            return {}

        if hasattr(origin_method, 'render_responses'):
            responses = origin_method.render_responses
            copy_response = copy.deepcopy(responses)
            for resp in copy_response.values():
                if resp.has_key("schema"):
                    serial_class = resp.get("schema")
                    if not isinstance(serial_class, dict):
                        self.add_serializer_to_definition(serial_class())
                        resp["schema"] = {"$ref":"#/definitions/%s"%serial_class.__name__}

            return copy_response
        return {}

    def get_class_tag(self, action, method):
        if hasattr(action, 'render_tag'):
            return action.render_tag.name, action.render_tag.description
        return "", ""

    def get_view_tag(self, view, method):
        lower_method = method.lower()
        if not hasattr(view, lower_method):
            return "", ""

        origin_method = getattr(view, lower_method)
        if not inspect.ismethod(origin_method):
            return "", ""

        if hasattr(origin_method, 'render_tag'):
            return origin_method.render_tag.name, origin_method.render_tag.description
        return "", ""

    def get_default_tag(self, path, action):
        """
        Return a descriptive category string for the endpoint, eg. 'users'.

        Examples of category/action pairs that should be generated for various
        endpoints:

        /users/                     [users][list], [users][create]
        /users/{pk}/                [users][read], [users][update], [users][destroy]
        /users/enabled/             [users][enabled]  (custom action)
        /users/{pk}/star/           [users][star]     (custom action)
        /users/{pk}/groups/         [groups][list], [groups][create]
        /users/{pk}/groups/{pk}/    [groups][read], [groups][update], [groups][destroy]
        """
        path_components = path.strip('/').split('/')
        path_components = [
            component for component in path_components
            if '{' not in component
            ]
        if action in self.known_actions:
            # Default action, eg "/users/", "/users/{pk}/"
            idx = -1
        else:
            # Custom action, eg "/users/{pk}/activate/", "/users/active/"
            idx = -2

        try:
            return path_components[idx], ""
        except IndexError:
            return "", ""

    def add_tag_dict(self, name, value):
        exist_value = self.tag_dict.get(name, "")
        if not exist_value:
            self.tag_dict[name] = value

    @property
    def tags(self):
        return [dict(name=k, description=v) for k, v in
                self.tag_dict.iteritems()]
