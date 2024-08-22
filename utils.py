import re
import yaml

from Angle import Angle


def avg(a, b):
    return (a + b) / 2


def reduce_angles(fl_bs, fl_fs, fr_bs, fr_fs):
    if fr_fs < fr_bs:
        fr_fs += Angle(360)
    fl = fl_fs - fl_bs
    fr = fr_fs - fr_bs
    return Angle(360) - avg(fl, fr)


def print_yaml(whatever):
    """
    yaml is too fucking dumb to use my Angle.__repr__() ugh I hate this so much
    """
    whatever = yaml.dump(whatever)
    whatever = re.sub(r" !!python/object:Angle.Angle", "", whatever)
    whatever = re.sub(r"\n\s*degrees:", "", whatever)
    whatever = re.sub(r"\n\s*minutes:", "°", whatever)
    whatever = re.sub(r"\n\s*seconds:", "'", whatever)
    whatever = re.sub(r"\n\s*secondsies: .*", '"', whatever)
    print(whatever)


def misclosure(results):
    n = len(results)
    return (180 * (n - 2)) - sum(
        [setup["angle"].to_decimal() for setup in results.values()]
    )
