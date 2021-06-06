from __future__ import annotations

import copy
from typing import Any, Generic, Optional, Type, TypeVar, overload

from .dict import Dict
from .immutable import Immutable
from .list import List

A = TypeVar('A')
B = TypeVar('B', covariant=True)


class Transform(Immutable, Generic[A]):
    """
    Represents transformation functions created by `Lens` instances
    """
    lens: Lens[A]
    value: Any

    def __repr__(self) -> str:
        return f'{repr(self.lens)} << {repr(self.value)}'

    def __call__(self, a: A) -> A:
        """
        Apply transformation to object `a`

        Examples:
            >>> from typing import List
            >>> (lens(List[int])[0] << 1)([0])
            [1]
        Args:
            a: Object to transform
        Return:
            Transformed object
        """
        *rest, head = self.lens
        attr_stack = [a]
        for path_element in rest:
            *attrs, last_attr = attr_stack
            next_attr = path_element.get(last_attr)
            attr_stack = attrs + [last_attr, next_attr]
        *attrs, last_attr = attr_stack
        transformed_last_attr = head.set(last_attr, self.value)
        for attr, path_element in zip(reversed(attrs), reversed(rest)):
            transformed_last_attr = path_element.set(
                attr, transformed_last_attr
            )
        return transformed_last_attr


class PathElement(Immutable):
    def get(self, x):
        raise NotImplementedError()

    def set(self, x, value):
        raise NotImplementedError()


def _is_named_tuple(x: object) -> bool:
    return (
        isinstance(x, tuple) and hasattr(x, '_fields')
        and hasattr(x, '_asdict') and hasattr(x, '_replace')
    )


class Attr(PathElement):
    attr: str

    def __repr__(self):
        return f'.{self.attr}'

    def get(self, x):
        return getattr(x, self.attr)

    def set(self, x, value):
        if _is_named_tuple(x):
            return x._replace(**{self.attr: value})
        x = copy.copy(x)
        object.__setattr__(x, self.attr, value)
        return x


class Index(PathElement):
    index: Any

    def __repr__(self):
        return f'[{repr(self.index)}]'

    def get(self, x):
        return x[self.index]

    def set(self, x, value):
        if isinstance(x, List):
            x[self.index]
            before = x[:self.index]
            after = x[self.index + 1:]
            return before + List([value]) + after
        elif isinstance(x, tuple):
            x[self.index]
            before = x[:self.index]
            after = x[self.index + 1:]
            return before + (value, ) + after
        elif isinstance(x, Dict):
            return x.set(self.index, value)
        x = copy.copy(x)
        x[self.index] = value
        return x


class RootLens(Immutable, Generic[B]):
    """
    Lens object that supports attribute access and indexing
    """
    __path: List[PathElement] = List()

    def __iter__(self):
        return iter(self.__path)

    def __repr__(self) -> str:
        result = 'lens()'
        for path_element in self:
            result += repr(path_element)
        return result

    def __getattr__(self, name: str) -> Lens[B]:
        """
        Create a new `Lens` that transform instances at path `name`

        Example:
            >>> from pfun import Immutable
            >>> class User(Immutable):
            ...     name: str
            >>> user = User('Bob')
            >>> (lens(User).name << 'Alice')(user)
            User(name='Alice')
        Args:
            name: name of attribute to transform in returned `Lens`
        Return:
            `Lens` that transform instances at path `name`
        """
        return Lens(self.__path + [Attr(name)])

    def __getitem__(self, index: Any) -> Lens[B]:
        """
        Create a `Lens` object that supports
        transformations of instances at index `index

        Example:
            >>> from typing import List
            >>> (lens(List[int])[0] << 1)([0])
            [1]
        Args:
            index: index that the `Lens` supports transformations of
        Return:
            `Lens` instance
        """
        return Lens(self.__path + [Index(index)])


class Lens(RootLens[B]):
    """
    Lens object that supports attribute access, indexing
    and can create transformations
    """
    def __repr__(self):
        return super().__repr__()

    def __lshift__(self, value: Any) -> Transform[B]:
        """
        Create a transformation function that assigns `value`
        to this path in the `Lens`

        Example:
            >>> from typing import List
            >>> (lens(List[int])[0] << 1)([0])
            [1]
        Args:
            value: Value to assign in transformation
        Return:
            Transformation function
        """
        return Transform(self, value)


T = TypeVar('T', bound=Type[Any])


@overload
def lens(t: T) -> RootLens[T]:
    pass


@overload
def lens(t: None = None) -> RootLens[Any]:
    pass


def lens(t: Optional[T] = None) -> RootLens[T]:
    """
    Create a `Lens` object that supports
    transformations of instances of type `T`

    Example:
        >>> from typing import List
        >>> (lens(List[int])[0] << 1)([0])
        [1]
    Args:
        t: Type that the `Lens` supports transformations of
    Return:
        `Lens` instance
    """
    return RootLens()


__all__ = ['lens']
