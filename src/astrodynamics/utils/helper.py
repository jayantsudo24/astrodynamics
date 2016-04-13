# coding: utf-8
from __future__ import absolute_import, division, print_function

import errno
from contextlib import contextmanager

import numpy as np
from astropy import units as u
from astropy.units import Unit, UnitBase
from boltons.typeutils import make_sentinel

from ..compat.contextlib import suppress
from ..compat.math import isclose
from .compat import PY33

__all__ = (
    'format_size',
    'prefix',
    'qisclose',
    'read_only_property',
    'suppress_file_exists_error',
    'verify_unit',
)

_size_suffixes = {
    'decimal': ('kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'),
    'binary': ('KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'),
    'gnu': "KMGTPEZY",
}


def read_only_property(name, docstring=None):
    """Return property for accessing attribute with name `name`

    Parameters:
        name: Attribute name
        docstring: Optional docstring for getter.

    Example:
        .. code-block:: python

            class Circle:
                def __init__(self, radius):
                    self._radius = radius

                radius = read_only_property('_radius')
    """
    def fget(self):
        return getattr(self, name)

    fget.__doc__ = docstring
    return property(fget)


def verify_unit(quantity, unit):
    """Verify unit of passed quantity and return it.

    Parameters:
        quantity: :py:class:`~astropy.units.Quantity` to be verified. Bare
                  numbers are valid if the unit is dimensionless.
        unit: Equivalent unit, or string parsable by
              :py:class:`astropy.units.Unit`

    Raises:
        ValueError: Units are not equivalent.

    Returns:
        ``quantity`` unchanged. Bare numbers will be converted to a dimensionless
        :py:class:`~astropy.units.Quantity`.

    Example:
        .. code-block:: python

            def __init__(self, a):
                self.a = verify_unit(a, astropy.units.m)

    """
    if not isinstance(unit, UnitBase):
        unit = Unit(unit)

    q = quantity * u.one
    if unit.is_equivalent(q.unit):
        return q
    else:
        raise ValueError(
            "Unit '{}' not equivalent to quantity '{}'.".format(unit, quantity))


def qisclose(a, b, rel_tol=1e-9, abs_tol=0.0):
    """Helper function for using :py:func:`math.isclose` with
    :py:class:`~astropy.units.Quantity` objects.
    """
    return isclose(a.si.value, b.si.value, rel_tol=rel_tol, abs_tol=abs_tol)


def format_size(value, binary=False, gnu=False, format='%.1f'):
    """Format a number of bytes like a human readable file size (e.g. 10 kB). By
    default, decimal suffixes (kB, MB) are used.  Passing binary=true will use
    binary suffixes (KiB, MiB) are used and the base will be 2**10 instead of
    10**3.  If ``gnu`` is True, the binary argument is ignored and GNU-style
    (ls -sh style) prefixes are used (K, M) with the 2**10 definition.
    Non-gnu modes are compatible with jinja2's ``filesizeformat`` filter.

    Copyright (c) 2010 Jason Moiron and Contributors.
    """
    if gnu:
        suffix = _size_suffixes['gnu']
    elif binary:
        suffix = _size_suffixes['binary']
    else:
        suffix = _size_suffixes['decimal']

    base = 1024 if (gnu or binary) else 1000
    bytes = float(value)

    if bytes == 1 and not gnu:
        return '1 Byte'
    elif bytes < base and not gnu:
        return '%d Bytes' % bytes
    elif bytes < base and gnu:
        return '%dB' % bytes

    for i, s in enumerate(suffix):
        unit = base ** (i + 2)
        if bytes < unit and not gnu:
            return (format + ' %s') % ((base * bytes / unit), s)
        elif bytes < unit and gnu:
            return (format + '%s') % ((base * bytes / unit), s)
    if gnu:
        return (format + '%s') % ((base * bytes / unit), s)
    return (format + ' %s') % ((base * bytes / unit), s)


@contextmanager
def suppress_file_exists_error():
    """Compatibility function for catching FileExistsError on Python 2"""
    if PY33:
        with suppress(FileExistsError):  # noqa
            yield
    else:
        try:
            yield
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise


def prefix(prefix, iterable):
    """Prepend items from `iterable` with `prefix` string."""
    for x in iterable:
        yield '{prefix}{x}'.format(prefix=prefix, x=x)


inherit_doc_sentinel = make_sentinel(var_name='inherit_doc_sentinel')


class _InheritDoc(object):
    @staticmethod
    def mark(fn):
        if fn.__doc__ is not None:
            raise TypeError(
                'docstring for {} is not None, inherit_doc would overwrite.'
                .format(fn))

        fn.__doc__ = inherit_doc_sentinel
        return fn

    @staticmethod
    def resolve(cls):
        sentinel_found = False
        for name, func in vars(cls).items():

            # Only inherit docstrings for functions explicitly marked
            if func.__doc__ is inherit_doc_sentinel:
                # We will raise exceptions so that when nothing happens, it
                # doesn't do so silently.
                sentinel_found = True
                parfunc_found = False

                for parent in cls.__bases__:
                    parfunc = getattr(parent, name, None)
                    parfunc_found = bool(parfunc)

                    if parfunc and getattr(parfunc, '__doc__', None):
                        func.__doc__ = parfunc.__doc__
                        break
                else:
                    # If we don't break, then replace inherit_doc_sentinel with
                    # None
                    func.__doc__ = None
                    pass

                if not parfunc_found:
                    raise TypeError(
                        "Cannot inherit docstring, '{}' not found in any parent"
                        " classes.".format(name))

        if not sentinel_found:
            raise TypeError(
                'Could not resolve docstring inheritance for {}, you must use'
                ' the inherit_doc decorator.'.format(cls))

        return cls

inherit_doc = _InheritDoc()


def find_nearest_index(array, value):
    idx_sorted = np.argsort(array)
    sorted_array = np.array(array[idx_sorted])
    idx = np.searchsorted(sorted_array, value, side='left')
    if idx >= len(array):
        idx_nearest = idx_sorted[len(array) - 1]
        return idx_nearest
    elif idx == 0:
        idx_nearest = idx_sorted[0]
        return idx_nearest
    else:
        if (abs(value - sorted_array[idx - 1]) <
                abs(value - sorted_array[idx])):
            idx_nearest = idx_sorted[idx - 1]
            return idx_nearest
        else:
            idx_nearest = idx_sorted[idx]
            return idx_nearest


def get_neighbors_index(array, central, num_neighbors):
    idx = find_nearest_index(array, central)

    start = max(0, idx - (num_neighbors - 1) // 2)
    end = min(len(array), start + num_neighbors)
    start = end - num_neighbors

    return slice(start, end)
