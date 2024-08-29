import csv
import random
import time
from collections import defaultdict
from math import sqrt, sin, cos, atan, degrees, radians

import xmltodict
import pandas
from decimal import *
from matplotlib import pyplot

from Angle import Angle
from utils import *

random.seed(time.time_ns())

with open("input/ControlPoints.xml", "r") as file:
    control_points = xmltodict.parse(file.read())
    control_points = control_points["LandXML"]["CgPoints"]["CgPoint"]
    control_points = {point["@name"]: point["#text"] for point in control_points}
    for point in control_points:
        control_points[point] = [
            Decimal(coordinate) for coordinate in control_points[point].split()
        ]

################################################################### raw results
print("_" * 60, "raw results")
booking_sheet = pandas.read_csv("input/booking_sheet.csv", dtype=str)
results = list()
names = list()
for index, row in booking_sheet.iterrows():
    results.append(nested_dict())
    names.append(list(row.values)[:3])
    items = list(row.items())
    for column, value in items[3:]:
        subkey = column.split()
        results[-1][subkey[0]][subkey[1]][subkey[2]] = Decimal(value)
n = len(results)
# convert DMS to custom Angle class
for s in range(n):
    for orientation in results[s]:
        for sight in results[s][orientation]:
            results[s][orientation][sight]["angle"] = Angle(
                results[s][orientation][sight]["degrees"],
                results[s][orientation][sight]["minutes"],
                results[s][orientation][sight]["seconds"],
            )
            results[s][orientation][sight].pop("degrees")
            results[s][orientation][sight].pop("minutes")
            results[s][orientation][sight].pop("seconds")
            results[s][orientation][sight] = dict(results[s][orientation][sight])
        results[s][orientation] = dict(results[s][orientation])
    results[s] = dict(results[s])

# make front-left backsight negative if it's like 359 or something
for s in range(n):
    if results[s]["front-left"]["backsight"]["angle"] > Angle(180):
        results[s]["front-left"]["backsight"]["angle"] = (
            Angle(360) - results[s]["front-left"]["backsight"]["angle"]
        )

for s in range(n):
    print(names[s])
    print(yaml.dump(results[s]))

############################################################### reduced results
print("_" * 60, "reduced results")
reduced_results = list()
for setup in results:
    reduced_results.append(
        dict(
            angle=reduce_angles(
                setup["front-left"]["backsight"]["angle"],
                setup["front-left"]["foresight"]["angle"],
                setup["front-right"]["backsight"]["angle"],
                setup["front-right"]["foresight"]["angle"],
            ),
            distance_backsight=round(
                (
                    setup["front-left"]["backsight"]["distance"]
                    + setup["front-right"]["backsight"]["distance"]
                )
                / 2,
                4,
            ),
            distance_foresight=round(
                (
                    setup["front-left"]["foresight"]["distance"]
                    + setup["front-right"]["foresight"]["distance"]
                )
                / 2,
                4,
            ),
        )
    )
results = reduced_results

for i in range(n):
    print(names[i])
    print(yaml.dump(results[i]))

############################################# angular misclosure and adjustment
print("_" * 40, "angular misclosure and adjustment")

print(
    "ideal internal angle sum is (n-2)pi radians =",
    180 * (n - 2),
    "degrees",
)
print(
    "measured internal angle sum is",
    Angle(
        sum([setup["angle"].to_decimal() for setup in results]),
        0,
        0,
    ),
)
print(f'acceptable angular misclosure is 12 root n = {12 * sqrt(n)}"')
print("measured angular misclosure is", misclosure(results))
# assert misclosure(results) < Angle(0, 0, 12 * sqrt(n))

adjustment = misclosure(results).seconds / n
adjustment_main = int(adjustment)
adjustment_remainder = round(n * (adjustment - adjustment_main))
print(
    f"\nadjustment per angle is "
    f'{adjustment_main}" with an extra second for {adjustment_remainder} '
    f"random angle{'' if adjustment_remainder==1 else 's'}"
)
print(
    f"\tdouble checking: {n}x ({adjustment_main}) + "
    f'{adjustment_remainder}") = '
    f'{6 * adjustment_main} + {adjustment_remainder}"'
)

chosen_angles_for_adjustment_remainder = random.sample(
    range(n), abs(adjustment_remainder)
)
chosen_angles_for_adjustment_remainder = [0, 1, 4]
for i in chosen_angles_for_adjustment_remainder:
    results[i]["angle"].secondsies += 1 if adjustment_remainder > 0 else -1
for s in range(n):
    results[s]["angle"].secondsies += adjustment_main
    results[s]["angle"] = Angle(
        results[s]["angle"].degrees,
        results[s]["angle"].minutes,
        results[s]["angle"].secondsies,
    )
    print(names[s], "->", results[s]["angle"])
print(misclosure(results))
assert misclosure(results) == Angle(0) and misclosure(results).secondsies == 0
print()

###################################################################### bearings
print("_" * 60, "bearings")
print("provided control point coordinates: (5008 is CP4 and 5009 is CP1)")
print(yaml.dump(control_points))

x, y = [float("nan")] * (n + 1), [float("nan")] * n  # for storing coordinates

# using 0 instead of 1 and 5 instead of 4 to
# preserve order of measurement and 0-based indexing
x[0], y[0] = control_points["5009"][1], control_points["5009"][0]
x[5], y[5] = control_points["5008"][1], control_points["5008"][0]

bearings = []

print("bearing from CP4 to CP1 is:")
print("                 ", x[0], "-", x[5])
print("  180 + arctan ( ------------------------- )")
print("                ", y[0], "-", y[5])
print(f"= 180 + arctan({x[0] - x[5]} / {y[0] - y[5]})")
bearings.append(Angle(180 + degrees(atan((x[0] - x[5]) / (y[0] - y[5])))))
print("=", bearings[-1])
print()

print("subsequent bearings are previous bearing + 180 - internal angle")

for setup in results[:-1]:
    bearings.append((bearings[-1] + Angle(180) - setup["angle"]).normalise())

print(yaml.dump(bearings[1:]))
# sanity checks: bearings should wrap around to where they started
assert bearings[0] == (bearings[-1] + Angle(180) - results[5]["angle"]).normalise()

################################################################### traversals
print("_" * 60, "traversals")
backsight = [setup["distance_backsight"] for setup in results]
foresight = [setup["distance_foresight"] for setup in results]

print("averaged distances between pairs of points:")
distances = []
for i in range(n):
    distances.append(round(avg(foresight[i], backsight[(i + 1) % n]), 4))
print(yaml.dump(distances))
print(
    "^ should be",
    sqrt(((x[1] - x[4]) ** 2) + ((y[1] - y[4]) ** 2)),
    "according to provided coordinates",
)
print()

print(f"CP1 is at ({x[1]},{y[1]})")
points = [1, 2, 3, 6, 5, 4]
eastings = []
northings = []
print()
print("Between subsequent CPs, ")
print(" Easting = distance x sin(bearing)")
print("Northing = distance x cos(bearing)")
print()
for i in range(n):
    src = points[i]
    dst = points[(i + 1) % n]

    print(f"from CP{src} to CP{dst}:")

    bearing = bearings[(i + 1) % n]
    distance = distances[i]

    print(f"\t bearing = {bearing}")
    print(f"\tdistance = {distance}m")

    easting = distance * Decimal(sin(radians(bearing.to_decimal())))
    northing = distance * Decimal(cos(radians(bearing.to_decimal())))
    eastings.append(easting)
    northings.append(northing)

    longitudinal_direction = "East" if easting > 0 else "West"
    latitudinal_direction = "North" if northing > 0 else "South"

    print(
        f"\t-> CP{dst} is {round(abs(easting),4)}m {longitudinal_direction} "
        f"and {round(abs(northing),4)}m {latitudinal_direction} of CP{src}"
    )

    x[(i + 1) % n] = x[i] + easting
    y[(i + 1) % n] = y[i] + northing


############################################## linear misclosure and adjustment
print("_" * 40, "linear misclosure and adjustment")

delta_E = sum(eastings)
delta_N = sum(northings)
linear_misclosure = Decimal(sqrt(delta_E**2 + delta_N**2))
print()
print(f"ΔE = {delta_E}")
print(f"ΔN = {delta_N}")

print(
    "Linear misclosure = sqrt( ΔE^2 + ΔN^2 )"
    f"\n                  = sqrt({delta_E}^2 + {delta_N}^2)"
    f"\n                  = sqrt({delta_E**2} + {delta_N**2})"
    f"\n                  = sqrt({delta_E**2 + delta_N**2})"
    f"\n                  = {linear_misclosure}m"
)

print(
    "accuracy = perimiter / linear misclosure"
    f"\n         = {sum(distances)} / {linear_misclosure}"
    f"\n         = {sum(distances) / linear_misclosure}"
)
print(f"minimum acceptable accuracy is 8000")
print()
print("adjusted northings and eastings are:")
for i in range(n):
    src = points[i]
    dst = points[(i + 1) % n]
    print(f"\nfrom CP{src} to CP{dst}:")

    print("\tadjustment ration = side length / perimeter")
    print(f"\t                  = {distances[i]} / {sum(distances)}")
    ration = distances[i] / sum(distances)
    print(f"\t                  = {ration}")

    print(f"\tEasting -= {delta_E} x {ration}")
    delta_e = delta_E * ration
    print(f"\t        -= {delta_e}")
    print(f"\t{eastings[i]} -> {eastings[i] - delta_e}")

    print(f"\tNorthing -= {delta_N} x {ration}")
    delta_n = delta_N * ration
    print(f"\t         -= {delta_n}")
    print(f"\t{northings[i]} -> {northings[i] - delta_n}")

    eastings[i] -= delta_e
    northings[i] -= delta_n
print()
print("ΔE after adjustment:", sum(eastings))
print("ΔN after adjustment:", sum(northings))

################################################################### coordinates
print("_" * 60, "coordinates")
x = [control_points["5009"][1]]
y = [control_points["5009"][0]]
for i in range(n):
    x.append(x[-1] + eastings[i])
    y.append(y[-1] + northings[i])
pyplot.scatter(x[:-1], y[:-1])
for i in range(n + 1):
    print(f"CP{points[i%n]}", "\t", round(x[i], 4), "\t", round(y[i], 4))
    pyplot.annotate(f"CP{points[i%n]}", (x[i], y[i]))
pyplot.gca().set_aspect("equal")
pyplot.savefig("output/opaque.png")
pyplot.savefig("output/transparent.png", transparent=True)
pyplot.close("all")
