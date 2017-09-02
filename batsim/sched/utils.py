"""
    batsim.sched.utils
    ~~~~~~~~~~~~~~~~~~

    Utility helpers used by other modules.

"""


class ObserveList:
    """Helper class implementing a filtered list.

    :param from_list: the initial entries of the list
    """

    def __init__(self, from_list=[]):
        self._data = list()
        self._data_set = set()
        for i in from_list:
            self.add(i)

    @property
    def data(self):
        """A copy of the content of the list."""
        return tuple(self._data)

    def _check_new_elem(self, element):
        """Checks whether a new element should be added.

        Can be overriden by sub-classes.
        """
        return True

    def _element_new(self, element):
        """Hook which is called when a new element was added.

        Can be overriden by sub-classes.

        :param element: the added element
        """
        pass

    def _element_del(self, element):
        """Hook which is called when an element was removed.

        Can be overriden by sub-classes.

        :param element: the removed element
        """
        pass

    def update_element(self, element):
        """Hook which should be called my elements to notify the list about changes.

        Can be overriden by sub-classes.

        :param element: the changed element
        """
        pass

    def __len__(self):
        """The number of elements in this collection."""
        return len(self._data)

    def __contains__(self, element):
        """Check whether or not an element is in this collection.

        :param element: the element to be checked
        """
        return element in self._data_set

    def add(self, element):
        """Adds a new element to this collection.

        :param element: the element to be added
        """
        if self._check_new_elem(element) and element not in self:
            self._data.append(element)
            self._data_set.add(element)
            self._element_new(element)

    def remove(self, element):
        """Removes an element from this collection.

        :param element: the element to be removed
        """
        self._data_set.remove(element)
        self._data.remove(element)
        self._element_del(element)

    def discard(self, element):
        """Removes an element from this collection or fail silently.

        :param element: the element to be removed
        """
        try:
            self.remove(element)
        except KeyError:
            pass

    def clear(self):
        """Remove all elements from the collection."""
        for e in self._data:
            self._element_del(e)
        self._data.clear()
        self._data_set.clear()

    def __iter__(self):
        return iter(self._data)

    def __add__(self, other):
        """Concatenate two lists.

        :param other: the list to be added after the tail of this list.
        """
        return self.create(set(self._data + other._data))

    def __str__(self):
        return str([str(entry) for entry in self._data])

    def apply(self, apply):
        """Apply a function to modify the list (e.g. sorting the list).

        :param apply: a function evaluating the result list.

        """
        return self.create(apply(self._data))

    def create(self, *args, **kwargs):
        """Create a new list of this type."""
        return self.__class__(*args, **kwargs)

    def sorted(self, field_getter=None, reverse=False):
        """Return a new list with the same elements sorted.

        :param field_getter: a function which returns the field to be sorted

        :param reverse: whether or not the sorting should be reversed
        """
        return self.create(
            sorted(
                self._data,
                key=field_getter,
                reverse=reverse))


def filter_list(
        data,
        filter=[],
        cond=None,
        max=None,
        min=None,
        num=None,
        min_or_max=False):
    """Filters a list.

    :param data: the list to be filtered.

    :param filter: a list of generators through which the entries will be piped. The generators
    should iterate through the data (first argument) and should `yield` the searched elements.

    :param cond: a function evaluating the entries and returns True or False whether or not the entry should be returned.

    :param max: the maximum number of returned entries.

    :param min: the minimum number of returned entries (if less entries are available no entries will be returned at all).

    :param num: the exact number of returned entries (overwrites `min` and `max`).

    :param min_or_max: either return the minimum or maximum number but nothing between.

    """

    # If a concrete number of entries is requested do not yield less or
    # more
    if num:
        min = num
        max = num

    def filter_condition(res):
        if cond:
            for r in res:
                if cond(r):
                    yield r
        else:
            yield from res

    def do_filter(res):
        for gen in reversed(filter):
            res = gen(res)
        yield from filter_condition(res)

    result = []
    num_elems = 0
    iterator = do_filter(data)
    while True:
        # Do not yield more entries than requested
        if max and num_elems >= max:
            break

        try:
            elem = next(iterator)
        except StopIteration:
            break
        num_elems += 1
        result.append(elem)

    # Do not yield less entries than requested (better nothing than less)
    if min and len(result) < min:
        result = []
        num_elems = 0

    # Return only min elements if flag is set and num_elems is between min and
    # max
    if min_or_max and min and max and num_elems < max and num_elems > min:
        result = result[:min]

    # Construct a new list which can be filtered again
    return result


class DictWrapper:
    """Wrapper for dictionaries.

    This wrapper allows to define new fields which do not exist in the underlying
    dictionary and should be stored in the object rather than in the dictionary
    itself (because it might be directly changed by a different actor).
    The wrapper also allows to access the dictionary values as attributes.

    :param obj: the dictionary to be wrapped inside this object.
    """

    def __init__(self, obj):
        self._obj = obj

    def __getattr__(self, name):
        return self._obj[name]

    def __getitem__(self, name):
        return self._obj[name]

    def __setitem__(self, name, value):
        self._obj[name] = value

    def __str__(self):
        return str(self._obj)


class SafeIterList(list):
    """A list which can be safely iterated over while removing current elements."""

    def __iter__(self):
        return iter(self[:])
