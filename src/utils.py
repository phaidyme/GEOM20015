from collections import defaultdict
import re
import yaml

from decimal import *
from yaml.resolver import BaseResolver

from Angle import Angle


def coord_representer(dumper, data):
    return dumper.represent_scalar(BaseResolver.DEFAULT_SCALAR_TAG, data.__repr__())


yaml.add_representer(Angle, coord_representer)
yaml.add_representer(Decimal, coord_representer)


def avg(a, b):
    return (a + b) / 2


def reduce_angles(fl_bs, fl_fs, fr_bs, fr_fs):
    if fr_fs < fr_bs:
        fr_fs += Angle(360)
    fl = fl_fs - fl_bs
    fr = fr_fs - fr_bs
    print(f"fl: {fl_fs} - {fl_bs} = {fl}")
    print(f"fr: {fr_fs} - {fr_bs} = {fr}")
    print("avg", avg(fl, fr))
    return Angle(360) - avg(fl, fr)


def misclosure(results):
    n = len(results)
    return (180 * (n - 2)) - sum([setup["angle"] for setup in results])


def nested_dict():
    return defaultdict(nested_dict)
