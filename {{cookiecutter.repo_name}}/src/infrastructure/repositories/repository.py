import logging
from abc import ABC
from typing import Callable

from src.infrastructure import (
    DEFAULT_PAGE_VALUE,
    DEFAULT_PER_PAGE_VALUE,
    ITEMIZE,
    ITEMIZED,
    PAGE,
    PER_PAGE,
    ApiException,
)

logger = logging.getLogger(__name__)


class Repository(ABC):
    base_class: Callable
    DEFAULT_NOT_FOUND_MESSAGE = "The requested resource was not found"
    DEFAULT_PER_PAGE = DEFAULT_PER_PAGE_VALUE
    DEFAULT_PAGE = DEFAULT_PAGE_VALUE
    session = None

    def __init__(self, session):
        self.session = session

    def save(self, entity):
        self.session.add(entity)
        self.session.flush()
        return entity

    def create(self, data):
        created_object = self.base_class(**data)
        self.session.add(created_object)
        self.session.flush()
        return created_object

    def update(self, object_id, data):
        update_object = self.get(object_id)
        for attr, value in data.items():
            setattr(update_object, attr, value)

        self.session.add(update_object)
        self.session.flush()
        return update_object

    def delete(self, object_id):
        delete_object = self.get(object_id)
        self.session.delete(delete_object)
        self.session.flush()
        return delete_object

    def delete_all(self, query_params):
        if query_params is None:
            raise ApiException("No parameters are required")

        query_set = self.session.query(self.base_class)
        query_set = self.apply_query_params(query_set, query_params)
        query_set.delete()
        self.session.flush()
        return query_set

    def get_all(self, query_params=None):
        query_set = self.session.query(self.base_class)
        query_set = self.apply_query_params(query_set, query_params)

        if self.is_itemized(query_params):
            return self.create_itemization(query_set)

        return self.create_pagination(query_params, query_set)

    def get(self, object_id):
        return self.session.query(self.base_class).filter_by(id=object_id).one()

    def _apply_query_params(self, query, query_params):
        return query

    def apply_query_params(self, query, query_params):
        if query_params is not None:
            query = self._apply_query_params(query, query_params)

        return query

    def exists(self, query_params):
        query = self.session.query(self.base_class)
        query = self.apply_query_params(query, query_params)
        return query.first() is not None

    def find(self, query_params):
        query = self.session.query(self.base_class)
        query = self.apply_query_params(query, query_params)
        return query.one()

    def count(self, query_params=None):
        query = self.session.query(self.base_class)
        query = self.apply_query_params(query, query_params)
        return query.count()

    def normalize_query_param(self, value):
        """
        Given a non-flattened query parameter value,
        and if the value is a list only containing 1 item,
        then the value is flattened.

        :param value: a value from a query parameter
        :return: a normalized query parameter value
        """

        if len(value) == 1 and value[0].lower() in ["true", "false"]:
            return value[0].lower() == "true"
        return value if len(value) > 1 else value[0]

    def is_query_param_present(self, key, params, throw_exception=False):
        query_params = self.normalize_query(params)

        if key in query_params:
            return True
        if not throw_exception:
            return False

        raise ApiException(f"{key} is not specified")

    def normalize_query(self, params):
        """
        Converts query parameters from only containing one value for
        each parameter, to include parameters with multiple values as lists.

        :param params: a flask query parameters data structure
        :return: a dict of normalized query parameters
        """

        if not isinstance(params, dict):
            params = params.to_dict(flat=False)

        return {k: self.normalize_query_param(v) for k, v in params.items()}

    def get_query_param(self, key, params, default=None, many=False):
        boolean_array = ["true", "false"]

        if params is None:
            return default

        if not isinstance(params, dict):
            params = self.normalize_query(params)

        selection = params.get(key, default)

        if not isinstance(selection, list):
            selection = [] if selection is None else [selection]
        new_selection = []

        for selected in selection:
            if isinstance(selected, str) and selected.lower() in boolean_array:
                new_selection.append(selected.lower() == "true")
            else:
                new_selection.append(selected)

        if not many:
            return None if not new_selection else new_selection[0]
        return new_selection

    def is_itemized(self, query_params):
        if query_params is None:
            return False

        itemized = self.get_query_param(ITEMIZED, query_params, False)
        itemize = self.get_query_param(ITEMIZE, query_params, False)
        return itemized or itemize

    def create_pagination(self, query_params, query_set):
        page = self.get_query_param(PAGE, query_params, self.DEFAULT_PAGE)
        per_page = self.get_query_param(PER_PAGE, query_params, self.DEFAULT_PER_PAGE)

        try:
            page = int(page)
        except ValueError:
            page = self.DEFAULT_PAGE

        try:
            per_page = int(per_page)
        except ValueError:
            per_page = self.DEFAULT_PER_PAGE

        paginated = query_set.paginate(page=int(page), per_page=int(per_page))
        return {
            "total": paginated.total,
            "page": paginated.page,
            "per_page": paginated.per_page,
            "items": paginated.items,
        }

    def create_itemization(self, query_set):
        return {"items": query_set.all()}
