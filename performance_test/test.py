# -*- coding:utf-8 -*-
from datetime import datetime
from typing import IO


def ef_generator(file: IO, count: int) -> None:
    import elementflow

    with elementflow.xml(file, 'contacts') as xml:
        for i in range(count):
            with xml.container('person', {'id': str(i)}):
                xml.element('name', text='John & Smith')
                xml.element('email', text='john.smith@megacorp.com')
                with xml.container('phones'):
                    xml.element('phone', {'type': 'work'}, text='123456')
                    xml.element('phone', {'type': 'home'}, text='123456')


def et_generator(file: IO, count: int) -> None:
    import xml.etree.cElementTree as ET

    root = ET.Element('contacts')
    for i in range(count):
        person = ET.SubElement(root, 'person', {'id': str(i)})
        ET.SubElement(person, 'name').text = 'John & Smith'
        ET.SubElement(person, 'email').text = 'john.smith@megacorp.com'
        phones = ET.SubElement(person, 'phones')
        ET.SubElement(phones, 'phone', {'type': 'work'}).text = '123456'
        ET.SubElement(phones, 'phone', {'type': 'home'}).text = '123456'
    ET.ElementTree(root).write(file, encoding='utf-8')


def lxml_generator(file: IO, count: int) -> None:
    from lxml import etree

    root = etree.Element('contacts')
    for i in range(count):
        person = etree.SubElement(root, 'person', {'id': str(i)})
        etree.SubElement(person, 'name').text = 'John & Smith'
        etree.SubElement(person, 'email').text = 'john.smith@megacorp.com'
        phones = etree.SubElement(person, 'phones')
        etree.SubElement(phones, 'phone', {'type': 'work'}).text = '123456'
        etree.SubElement(phones, 'phone', {'type': 'home'}).text = '123456'
    etree.ElementTree(root).write(file, encoding='utf-8')


if __name__ == '__main__':
    count = 100000
    for method in (ef_generator, et_generator, lxml_generator):
        start = datetime.now()
        method(open('/dev/null', 'wb'), count)
        print(datetime.now() - start)
