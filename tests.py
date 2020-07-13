# -*- coding:utf-8 -*-
from __future__ import with_statement

import unittest
from io import BytesIO
import xml.etree.cElementTree as ET

import pytest

import elementflow


def _bytes(value: str) -> bytes:
    return bytes(value, encoding='utf-8')


def test_xml():
    buffer = BytesIO()
    with elementflow.xml(buffer, 'root') as xml:
        with xml.container('container', {'key': '"значение"'}):
            xml.text('<Текст> контейнера')
            xml.element('item')
        xml.element('item', text='Текст')
    buffer.seek(0)
    tree = ET.parse(buffer)
    buffer = BytesIO()
    tree.write(buffer, encoding='utf-8')
    assert buffer.getvalue() == _bytes(
        '<root>'
        '<container key="&quot;значение&quot;">'
        '&lt;Текст&gt; контейнера'
        '<item />'
        '</container>'
        '<item>Текст</item>'
        '</root>',
    )


def test_non_well_formed_on_exception():
    buffer = BytesIO()
    try:
        with elementflow.xml(buffer, 'root') as xml:
            xml.text('Text')
            raise Exception()
    except Exception:
        pass
    buffer.seek(0)
    # Parsing this buffer should cause a parsing error due to unclosed
    # root element
    with pytest.raises(SyntaxError):
        ET.parse(buffer)


def test_comment():
    buffer = BytesIO()
    with elementflow.xml(buffer, 'root') as xml:
        xml.comment('comment')
    buffer.seek(0)
    assert buffer.getvalue() == _bytes('<?xml version="1.0" encoding="utf-8"?><root><!--comment--></root>')


def test_comment_with_double_hyphen():
    buffer = BytesIO()
    with elementflow.xml(buffer, 'root') as xml:
        xml.comment('--comm-->ent--')
    buffer.seek(0)
    assert buffer.getvalue() == _bytes('<?xml version="1.0" encoding="utf-8"?><root><!--comm>ent--></root>')


def test_namespaces():
    buffer = BytesIO()
    with elementflow.xml(buffer, 'root', namespaces={'': 'urn:n', 'n1': 'urn:n1'}) as xml:
        xml.element('item')
        with xml.container('n2:item', namespaces={'n2': 'urn:n2'}):
            xml.element('item')
            xml.element('n1:item')
    buffer.seek(0)
    tree = ET.parse(buffer)
    root = tree.getroot()
    assert root.tag == '{urn:n}root'
    assert root.find('{urn:n}item') is not None
    assert root.find('{urn:n2}item/{urn:n}item') is not None
    assert root.find('{urn:n2}item/{urn:n1}item') is not None


@pytest.mark.parametrize('args', [
    dict(root='n1:root', namespaces={'n': 'urn:n'}),
    dict(root='n:root', attrs={'n1:k': 'v'}, namespaces={'n': 'urn:n'}),
])
def test_bad_namespace(args):
    buffer = BytesIO()

    def g():
        with elementflow.xml(buffer, **args):
            pass

    with pytest.raises(ValueError):
        g()


def test_map():
    data = [(1, 'One'), (2, 'Two'), (3, 'Three')]
    buffer = BytesIO()
    with elementflow.xml(buffer, 'root') as xml:
        xml.map(lambda item: (
            'item',
            {'key': str(item[0])},
            item[1],
        ), data)
        xml.map(lambda item: (item[1],), data)
    buffer.seek(0)
    tree = ET.parse(buffer)
    buffer = BytesIO()
    tree.write(buffer, encoding='utf-8')
    assert buffer.getvalue() == _bytes(
        '<root>'
        '<item key="1">One</item>'
        '<item key="2">Two</item>'
        '<item key="3">Three</item>'
        '<One /><Two /><Three />'
        '</root>'
    )


def test_indent():
    buffer = BytesIO()
    with elementflow.xml(buffer, 'root', indent=2) as xml:
        with xml.container('a'):
            xml.element('b', text=''.join(['blah '] * 20))
            xml.comment(' '.join(['comment'] * 20))
    buffer.seek(0)
    assert buffer.getvalue() == _bytes(
"""<?xml version="1.0" encoding="utf-8"?>
<root>
  <a>
    <b>
      blah blah blah blah blah blah blah blah blah blah blah
      blah blah blah blah blah blah blah blah blah
    </b>
    <!--
      comment comment comment comment comment comment comment
      comment comment comment comment comment comment comment
      comment comment comment comment comment comment
    -->
  </a>
</root>
""")


def test_indent_nowrap():
    buffer = BytesIO()
    with elementflow.xml(buffer, 'root', indent=2, text_wrap=False) as xml:
        with xml.container('a'):
            xml.element('b', text=''.join(['blah '] * 20))
            xml.comment(' '.join(['comment'] * 20))
    buffer.seek(0)
    assert buffer.getvalue() == _bytes(
"""<?xml version="1.0" encoding="utf-8"?>
<root>
  <a>
    <b>blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah </b>
    <!--comment comment comment comment comment comment comment comment comment comment comment comment comment comment comment comment comment comment comment comment-->
  </a>
</root>
""")
