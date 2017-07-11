#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Matteo'

import datetime
import cPickle as pickle

def save_file(data, filename = './out/data.p'):
    with open(filename, 'wb') as fp:
        pickle.dump(data, fp)

def load_file(filename = './out/data.p'):
    with open(filename, 'rb') as fp:
        data = pickle.load(fp)
    return data

def set_to_midnight(dt):
    midnight = datetime.time(0)
    return datetime.datetime.combine(dt.date(), midnight)