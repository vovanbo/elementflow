# -*- coding:utf-8 -*-
from datetime import datetime


def ef_generator(file, count):
    import elementflow

    with elementflow.xml(file, 'contacts') as xml:
        for i in range(count):
            with xml.container('person', {'id': str(i)}):
                xml.element('name', text='John & Smith')
                xml.element('email', text='john.smith@megacorp.com')
                with xml.container('phones'):
                    xml.element('phone', {'type': 'work'}, text='123456')
                    xml.element('phone', {'type': 'home'}, text='123456')


def et_generator(file, count):
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


def lxml_generator(file, count):
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
    start = datetime.now()
    ef_generator(open('/dev/null', 'wb'), 40000)
    print(datetime.now() - start)
    et_generator(open('/dev/null', 'wb'), 40000)
    print(datetime.now() - start)
    lxml_generator(open('/dev/null', 'wb'), 40000)
    print(datetime.now() - start)
