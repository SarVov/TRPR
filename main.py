#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import with_statement
from __future__ import absolute_import
from collections import OrderedDict
import re
from tic import Tic
import json
import struct
import sys
import os
import csv
from io import open

reload(sys)
sys.setdefaultencoding('utf8')


file = None
n = 20  # шаг разбиения тиков при записи

json_dict = OrderedDict([('parsig_nom_sign', 8), ('parsig_n_fil', 8), ('parsig_n_dec', 8), ('parsig_n_dfm', 8),
            ('parsig_poly', 8), ('parsig_n_tay', 8), ('parsig_Drp', 8), ('parsig_dev', 8), ('parsig_Kpot', 8),
            ('parsig_nsdv', 8), ('nstr', 8), ('ndnstr', 8), ('dlstr', 8), ('trpr_fg1', 8), ('trpr_r_phasepoint', 8),
            ('tips', 4), ('nvk', 4), ('nhk', 4), ('prUWB', 2), ('reserve', 4), ('nfaz', 2), ('input_switch', 2),
            ('trks', 2), ('reserve_1', 2), ('kdiv_x', 2), ('kdiv_y', 2), ('trpr_npos', 2), ('trpr_mask_rec', 8),
            ('attamps', 2), ('fazkk', 2), ('fazopk', 2), ('mask_bc_ams', 2), ('mode_cont_unit', 2), ('kpg', 2),
            ('align_1', 12), ('reserve_2', 12), ('por_blank', 4), ('abs_value', 8), ('kgd', 8), ('shgd', 8),
            ('trace_ctrl', 8), ('fg2', 8), ('nfgd_fu', 8), ('n1grs', 4), ('kgrs', 4), ('shgrs', 4),
            ('magnitude_rel', 4), ('magnitude_fl', 4), ('win_size_R', 2), ('win_size_V', 2), ('thres_comb', 2),
            ('local_max', 2), ('mask_pol', 2), ('prclb', 2), ('kolimp', 2), ('namplrs', 2), ('tippc', 2),
            ('union_pol', 2), ('comm_ent_stream', 2), ('mask232_0', 2), ('mask232_1', 2), ('hardw_model_mask', 2),
            ('sign_ea', 2), ('num_ad', 2), ('align_2', 12), ('nom_imob', 4), ('pr_imit', 2), ('nom_can', 2),
            ('tip_z', 2), ('nom_bar', 2), ('align_3', 12)])

to_float = [u'parsig_n_tay', u'parsig_Drp', u'parsig_Kpot']

to_plusminus = [u'nfgd_fu', u'n1grs']


def check_bit(item):
    u""" проверка соответствия тика условиям
        в начальной задаче бит 0x0040 равен 0049 """
    try:
        bit = item[u'0x0040'][0]
        if bit == u'0049':
            return True
        else:
            return False
    except:
        return False


def main_method(fullpath=None, outputdir=None):
    u""" основной метод обработки входного файла
         outputdir - директория сохранения. Если параметр пустой - поддиректория текущей, output"""
    main_dict = OrderedDict()
    subdict = OrderedDict()
    header = u' '
    if not outputdir:
        outputdir = 'output'

    if not fullpath:
        return

    # чтение файла
    with open(fullpath) as f:
        for line in f:
            match = re.search(r'[\d]{2}\:[\d]{2}\:[\d]{2}[\.]{1}[\d]*', line)
            
            if match:
                if header != u'':
                    #main_dict[main_dict.keys()[header]]=subdict
                    main_dict.update({header: subdict})
                header = match.group(0)
                subdict = OrderedDict()
            else:
                match = re.search(r'0[Хx][0-9A-Fa-f]{4}', line)
                if match:
                    subheader = match.group(0)
                    subline = line[len(subheader)+2:]
                    data = subline.strip().split(u' ')
                    subdict.update({subheader: data})
        main_dict.update({header: subdict})

    # создание списка объектов, при удовлетворении входному условию
    # условие может быть изменено в функции check_bit()
    res = []
    count = 0  # счетчик тиков, увеличивается всегда кроме случая, когда следующий тик есть продолжение предыдущего
    # для счета по порядку следует изменить на 1
    # минимальное значение номера тика из 0x0040
    list_of_tics = []
    for item in main_dict.keys():
        if check_bit(main_dict[item]):
            # номер тика из 0x0040
            cur_number = main_dict[item][u'0x0040'][6]
            #print(cur_number)
            list_of_tics.append(int(cur_number, 16))
            #print(min(list_of_tics))
            # расчет номер тика вычитанием минимального номера и исключением '0x'
            deducted = ((int(cur_number, 16) - (min(list_of_tics))))
            res.append(Tic(deducted, item, main_dict[item]))
            count += 1
        # else:
        #     if res:
        #         res[-1].setextention(main_dict[item])
                # count += 1 # при счете по порядку следует убрать этот инкремент
    # формирование выходного файла
    # определение имени файла
    path, filename = os.path.split(fullpath)
    outputfilename = filename[:filename.index(u'.')]
    outputdirname = outputdir + '/'
    
    #outputfilename=outputfilename.decode('utf-8')
    #outputdirname = outputdirname.decode('utf-8')
    #filename = filename.decode('utf-8')

    if not os.path.exists(outputdirname):
        os.mkdir(outputdirname)
    json_result = make_json(res)  # здесь получаем длинный словарь, который можно разбивать на части
    keys = list(json_result.keys())
    to_write = [keys[i:i + n] for i in xrange(0, len(keys), n)]
    for i in xrange(0, len(to_write)):
        write_name = outputdirname + (outputfilename if i == 0 else outputfilename + '_' + str(i)) + '.json'
        with open(write_name, 'w', encoding='utf-8', errors="ignore") as f:
            temp = OrderedDict()
            for item in to_write[i]:
                temp[item] = json_result[item]
            f.write(unicode(json.dumps(final_json(temp), indent=4)))

    # формирование данных для текстового файла
    textarray = []
    for key in json_result.keys():
        count = 1
        for subitem in json_result[key]:
            # номер тика, номер строба, нужное значение
            textarray.append((key, count, subitem))
            count += 1

    rusnames = param_names()
    # запись в текстовый файл
    with open(outputdirname + outputfilename + u'.txt', u'w') as f:
        for item in textarray:
            for subitem in item[2].keys():
                s = u'Номер такта: %s' % (item[0]) + u'; '
                s += subitem + u':' + unicode(item[2][subitem]) + u'  ' + rusnames[subitem] + u'; '
                s += u'Номер строба: %d\n ' % (item[1])
                f.write(s)
    print u'Operation completed successfully'


def final_json(j_dict):
    cdir = os.path.abspath(os.curdir)
    with open((cdir + '/Assets/header.json').decode('utf-8'), 'r') as f:
        header = json.load(f, object_pairs_hook=OrderedDict)
    res = []
    for item in j_dict.keys():
        temp = OrderedDict()
        for k1 in j_dict[item]:
            temp2 = OrderedDict()
            temp2['ch_Nstr'] = True
            temp2.update(k1)
            temp.update(temp2)
        res.append(OrderedDict([('tic', item), ('trpr_strobes', [temp])]))
    header.update({u'shedule': res})
    return header


def make_json(ticlist):
    u""" функция формирования JSON на основе списка тактов """
    s = 0
    write_dict = OrderedDict()
    for item in json_dict.keys():
        s += json_dict[item]
    for item in ticlist:
        strobeslst = []
        for subitem in item.get_strobes():
            stringtoparse = ''.join(subitem)
            pointer = 0
            strobedict = OrderedDict()
            for parametr in json_dict.keys():
                value = stringtoparse[pointer: pointer+json_dict[parametr]]
                # перевод параметра в другую систему счисления и запись в словарь
                if parametr in to_float:
                    # если параметр в списке float - параметров
                    strobedict.update({parametr: hex_to_float(value)})
                elif parametr in to_plusminus:
                    # если нужно анализировать положительный/отрицательный
                    valuehead = value[:int(len(value)/2)]
                    if valuehead == u'f' * len(valuehead):
                        strobedict.update({parametr: hex_to_negative(value)})
                    else:
                        strobedict.update({parametr: int(u'0x' + value, 16)})
                else:
                    strobedict.update({parametr: int(u'0x' + value, 16)})
                pointer += json_dict[parametr]
            strobeslst.append(strobedict)
        write_dict.update({item.number: strobeslst})
    return write_dict


def main():
    # чтение строки аргументов
    try:
        filename = sys.argv[1]
    except:
        print u'No source list'
        sys.exit(1)

    # чтение строк файла ресурсов
    with open(filename, u'r') as f:
        source = f.read().splitlines()
    for sourcefile in source:
        main_method(sourcefile)


def hex_to_float(hex_str):
    return round(struct.unpack('!f', bytearray.fromhex(hex_str))[0], 2)


def hex_to_negative(hex_str):
    num_int = int(u'0x' + hex_str, 16)
    num_int -= 1
    bin_str = bin(num_int)
    result_bin = u''
    if bin_str[2] != u'1':
        raise ValueError
    for ch in bin_str[3:]:
        if ch == u'0':
            result_bin += u'1'
        else:
            result_bin += u'0'
    return -int(result_bin, 2)


def param_names():
    with open(u'Assets/params.csv', encoding="utf-8", errors="ignore") as csv_table:
        return dict((row['Short name'], row['Full name']) for row in csv.DictReader(csv_table))


if __name__ == u'__main__':
    main()
