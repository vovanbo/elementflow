# -*- coding:utf-8 -*-
"""
Library for generating XML as a stream without first building a tree in memory.

Basic usage::

    import elementflow
    file = open('text.xml', 'w') # can be any  object with .write() method

    with elementflow.xml(file, 'root') as xml:
        xml.element('item', attrs={'key': 'value'}, text='text')
        with xml.container('container', attrs={'key': 'value'}):
            xml.text('text')
            xml.element('subelement', text='subelement text')

Usage with namespaces::

    with elementflow.xml(file, 'root', namespaces={'': 'urn:n', 'n1': 'urn:n1'}) as xml:
        xml.element('item')
        with xml.container('container', namespaces={'n2': 'urn:n2'):
            xml.element('n1:subelement')
            xml.element('n2:subelement')

Pretty-printing::

    with elementflow.xml(file, 'root', indent=2):
        # ...

"""
import itertools
import textwrap
import codecs
from typing import Callable, Dict, IO, List, Optional, Sequence, Set, Tuple, TypeVar, Union

MapType = TypeVar('MapType')


def escape(value: str) -> str:
    if '&' not in value and '<' not in value:
        return value
    return value.replace('&', '&amp;').replace('<', '&lt;')


def quote_value(value: str) -> str:
    if '&' in value or '<' in value or '"' in value:
        value = value.replace('&', '&amp;').replace('<', '&lt;').replace('"', '&quot;')
    return f'"{value}"'


def convert_attrs_to_string(attrs: Optional[Dict[str, str]] = None) -> str:
    if not attrs:
        return ''
    return ''.join(f' {k}={quote_value(v)}' for k, v in attrs.items())


class XMLGenerator:
    """
    Basic generator without support for namespaces or pretty-printing.

    Constructor accepts:

    - file: an object receiving XML output, anything with .write()
    - root: name of the root element
    - attrs: attributes dict

    Constructor will implicitly open a root container element, you don't need
    to call .container() for it
    """

    def __init__(self, file: IO, root: str, attrs: Optional[Dict[str, str]] = None, **kwargs) -> None:
        self.file = codecs.getwriter('utf-8')(file)
        self.file.write('<?xml version="1.0" encoding="utf-8"?>')
        self.stack: List[str] = []
        self.container(root, attrs, **kwargs)

    def __enter__(self) -> 'XMLGenerator':
        return self

    def __exit__(self, exc_type, exc_value, exc_tb) -> None:
        if exc_type:
            return
        self.file.write(f'</{self.stack.pop()}>')

    def container(self, name: str, attrs: Optional[Dict[str, str]] = None, **kwargs) -> 'XMLGenerator':
        """
        Opens a new element containing sub-elements and text nodes.
        Intends to be used under ``with`` statement.
        """
        self.file.write(f'<{name}{convert_attrs_to_string(attrs)}>')
        self.stack.append(name)
        return self

    def element(self, name: str, attrs: Optional[Dict[str, str]] = None, text: str = '') -> None:
        """
        Generates a single element, either empty or with a text contents.
        """
        if text:
            self.file.write(f'<{name}{convert_attrs_to_string(attrs)}>{escape(text)}</{name}>')
        else:
            self.file.write(f'<{name}{convert_attrs_to_string(attrs)}/>')

    def text(self, value: str) -> None:
        """
        Generates a text in currently open container.
        """
        self.file.write(escape(value))

    def comment(self, value: str) -> None:
        """
        Adds a comment to the xml
        """
        value = value.replace('--', '')
        self.file.write(f'<!--{value}-->')

    def map(
            self,
            func: Callable[[MapType], Tuple[str, Optional[Dict[str, str]], str]],
            sequence: Sequence[MapType],
    ) -> None:
        """
        Convenience function for translating a sequence of objects into xml elements.
        First parameter is a function that accepts an object from the sequence and
        return a tuple of arguments for "element" method.
        """
        for item in sequence:
            self.element(*func(item))


class NamespacedGenerator(XMLGenerator):
    """
    XML generator with support for namespaces.
    """

    def __init__(
            self,
            file: IO,
            root: str,
            attrs: Optional[Dict[str, str]] = None,
            namespaces: Optional[Dict[str, str]] = None,
    ) -> None:
        self.namespaces: List[Set[str]] = [{'xml'}]
        super().__init__(file, root, attrs=attrs, namespaces=namespaces)

    def _process_namespaces(
            self,
            name: str,
            attrs: Optional[Dict[str, str]] = None,
            namespaces: Optional[Dict[str, str]] = None,
    ) -> Tuple[Dict[str, str], Set[str]]:
        prefixes: Set[str] = self.namespaces[-1]
        if namespaces:
            prefixes |= set(namespaces)
        attributes = attrs or {}
        names = [n for n in itertools.chain((name,), attributes) if ':' in n]
        for name in names:
            prefix = name.split(':')[0]
            if prefix not in prefixes:
                raise ValueError(f'Unknown namespace prefix: {prefix}')
        if namespaces:
            namespaces = {
                f'xmlns:{key}' if key else 'xmlns': value
                for key, value in namespaces.items()
            }
            attributes.update(namespaces)
        return attributes, prefixes

    def __exit__(self, exc_type, exc_value, exc_tb) -> None:
        super().__exit__(exc_type, exc_value, exc_tb)
        self.namespaces.pop()

    def container(
            self,
            name: str,
            attrs: Optional[Dict[str, str]] = None,
            namespaces: Optional[Dict[str, str]] = None,
    ) -> XMLGenerator:
        attrs, prefixes = self._process_namespaces(name, attrs, namespaces)
        self.namespaces.append(prefixes)
        return super().container(name, attrs)

    def element(
            self,
            name: str,
            attrs: Optional[Dict[str, str]] = None,
            namespaces: Optional[Dict[str, str]] = None,
            text: str = '',
    ) -> None:
        attributes, _ = self._process_namespaces(name, attrs, namespaces)
        super().element(name, attributes, text)


class IndentingGenerator(NamespacedGenerator):
    """
    XML generator with pretty-printing.
    """

    def __init__(self, *args, **kwargs) -> None:
        self._text_wrap: bool = kwargs.pop('text_wrap', True)
        self._indent: str = ' ' * kwargs.pop('indent', 2)
        self._width: int = kwargs.pop('width', 70)
        self._min_width: int = kwargs.pop('min_width', 20)
        super().__init__(*args, **kwargs)

    def _format_value(self, value: str) -> str:
        indent = self._indent * len(self.stack)
        self.file.write(f'\n{indent}')
        if len(value) > self._width and self._text_wrap:
            fill = self._fill(value, indent + self._indent)
            value = f'{fill}\n{indent}'
        return value

    def _fill(self, value: str, indent: Optional[str] = None) -> str:
        if indent is None:
            indent = self._indent * len(self.stack)
        width = max(self._min_width, self._width - len(indent))
        tw = textwrap.TextWrapper(width=width, initial_indent=indent, subsequent_indent=indent)
        return f'\n{tw.fill(value)}'

    def __exit__(self, *args, **kwargs) -> None:
        fill = self._indent * (len(self.stack) - 1)
        self.file.write(f'\n{fill}')
        super().__exit__(*args, **kwargs)
        if not self.stack:
            self.file.write('\n')

    def container(self, *args, **kwargs) -> XMLGenerator:
        fill = self._indent * len(self.stack)
        self.file.write(f'\n{fill}')
        return super().container(*args, **kwargs)

    def element(
            self,
            name: str,
            attrs: Optional[Dict[str, str]] = None,
            namespaces: Optional[Dict[str, str]] = None,
            text: str = '',
    ) -> None:
        text = self._format_value(text)
        return super().element(name, attrs, namespaces, text)

    def text(self, value: str) -> None:
        super().text(self._fill(value))

    def comment(self, value: str) -> None:
        value = self._format_value(value)
        return super().comment(value)


class Queue:
    """
    In-memory queue for using as a temporary buffer in xml generator.
    """

    def __init__(self) -> None:
        self.data = bytearray()

    def __len__(self) -> int:
        return len(self.data)

    def write(self, value: Union[bytes, bytearray]) -> None:
        self.data.extend(value)

    def pop(self) -> str:
        result = str(self.data)
        self.data = bytearray()
        return result


def xml(
        file: IO,
        root: str,
        attrs: Optional[Dict[str, str]] = None,
        namespaces: Optional[Dict[str, str]] = None,
        indent: Optional[int] = None,
        text_wrap: bool = True,
        **kwargs,
) -> XMLGenerator:
    """
    Creates a streaming XML generator.

    Parameters:

    - file: an object receiving XML output, anything with .write()
    - root: name of the root element
    - attrs: attributes dict
    - namespaces: namespaces dict {prefix: uri}, default namespace has prefix ''
    - indent: indent size to pretty-print XML. When None then pretty-print is disabled.
    """
    if indent is not None:
        return IndentingGenerator(file, root, attrs, namespaces, text_wrap=text_wrap, indent=indent, **kwargs)
    elif namespaces:
        return NamespacedGenerator(file, root, attrs, namespaces)
    else:
        return XMLGenerator(file, root, attrs)
