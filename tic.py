#! /usr/bin/env python
# -*- coding: utf-8 -*-

START_BIT = 83
START_BIT_EXTENSION = 15
STROBE_LENGTH = 84
STROBE_SPACE = 40


class Tic(object):
    u""" конструктор класса """
    def __init__(self, number, header, data):
        self.number = number
        self.header = header
        self.data = data
        self.extension = None

    def __str__(self):
        u""" перезагрузка символьного представления класса """
        res = u'Header: ' + self.header + u'\n'
        for item in self.data.keys():
            res = res + item + u' ' + u' '.join(self.data[item]) + u'\n'
        return res

    def get_strobes(self):
        u""" формирование стробов """
        # преобразование в длинную строку основного такта
        longdata = []
        for key in self.data.keys():
            longdata.extend(self.data[key])
        longdata = longdata[START_BIT:]

        # преобразование в длинную строку дополнительного такта
        if self.extension:
            longdataextension = []
            for key in self.extension.keys():
                longdataextension.extend(self.extension[key])
            longdataextension = longdataextension[START_BIT_EXTENSION:]
            longdata.extend(longdataextension)
        res = []
        while len(longdata) >= STROBE_LENGTH:
            res.append(longdata[0:STROBE_LENGTH])
            longdata = longdata[STROBE_LENGTH + STROBE_SPACE:]
        return res

    def setextention(self, extend_data):
        u""" присоединение дополнения тика при соответствующем условии """
        bytes_tic = u'0x' + self.data[u'0x0010'][4] + self.data[u'0x0010'][5]
        bytes_extend = u'0x' + extend_data[u'0x0010'][4] + extend_data[u'0x0010'][5]
        if int(bytes_extend, 16) == (int(bytes_tic, 16) + 1):
            self.extension = extend_data
            return True
        return False
