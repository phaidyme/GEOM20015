import csv
import random
import time
from matplotlib import pyplot
from math import sqrt, sin, cos, atan, degrees, radians, isnan
import xmltodict
from sys import argv
from Angle import Angle
from utils import *

random.seed(time.time_ns())

with open("ControlPoints.xml", "r") as file:
    control_points = xmltodict.parse(file.read())["LandXML"]["CgPoints"][
        "CgPoint"
    ]
control_points = {point["@name"]: point["#text"] for point in control_points}
for point in control_points:
    control_points[point] = [
        float(coordinate) for coordinate in control_points[point].split()
    ]

with open(f"{argv[1]}.csv", "r") as file:
    file_content = csv.reader(file)
    file_content = [
        row for row in file_content if any([len(cell) > 0 for cell in row])
    ]

################################################################### raw results
results = dict()
for s in range(1, 7):
    results[f"setup_{s}"] = dict()
    setup = dict(
        front_left=file_content[((s - 1) * 3) + 1],
        front_right=file_content[((s - 1) * 3) + 2],
    )
    for o, orientation in setup.items():
        results[f"setup_{s}"][o] = dict()
        measurements = dict(
            back_sight=orientation[1:5], fore_sight=orientation[6:]
        )
        for m, measurement in measurements.items():
            results[f"setup_{s}"][o][m] = dict(
                angle=Angle(
                    int(measurement[0]),
                    int(measurement[1]),
                    int(measurement[2]),
                ),
                distance=float(measurement[3]),
            )
for s in results:
    if results[s]["front_left"]["back_sight"]["angle"] > Angle(180):
        results[s]["front_left"]["back_sight"]["angle"] = Angle(360) - results[s]["front_left"]["back_sight"]["angle"]
"""
# adding the last result artificially
# values derived very approximately from google earth
results["setup_6"] = dict(
    front_left=dict(
        back_sight=dict(angle=Angle(0), distance=31.98),
        fore_sight=dict(angle=Angle(332, 30), distance=97.52),
    ),
    front_right=dict(
        back_sight=dict(angle=Angle(180), distance=32.24),
        fore_sight=dict(angle=Angle((332 + 180) % 360, 30), distance=97.67),
    ),
)
"""
print('_' * 60, "raw results")
print_yaml(results)

############################################################### reduced results
reduced_results = dict()
for s, setup in results.items():
    reduced_results[s] = dict(
        angle=reduce_angles(
            setup["front_left"]["back_sight"]["angle"],
            setup["front_left"]["fore_sight"]["angle"],
            setup["front_right"]["back_sight"]["angle"],
            setup["front_right"]["fore_sight"]["angle"],
        ),
        distance_back_sight=round(
            (
                setup["front_left"]["back_sight"]["distance"]
                + setup["front_right"]["back_sight"]["distance"]
            )
            / 2,
            4,
        ),
        distance_fore_sight=round(
            (
                setup["front_left"]["fore_sight"]["distance"]
                + setup["front_right"]["fore_sight"]["distance"]
            )
            / 2,
            4,
        ),
    )
results = reduced_results

print('_' * 60, "reduced results")
print_yaml(results)

############################################# angular misclosure and adjustment

n = len(results)

print('_' * 40, "angular misclosure and adjustment")
print(
    "ideal internal angle sum is (n-2)pi radians =",
    180 * (n - 2),
    "degrees",
)
print(
    "measured internal angle sum is",
    Angle(
        sum([setup["angle"].to_decimal() for setup in results.values()]),
        0,
        0,
    ),
)
print(f'acceptable angular misclosure is 12 root n = {round(12 * sqrt(n))}"')
print(
    "measured angular misclosure is",
    Angle(
        misclosure(results),
        0,
        0,
    ),
)
adjustment = Angle(misclosure(results) / n)
adjustment_remainder = round(Angle(misclosure(results)).secondsies % n)
# since python's modulo is always positive (why can't anything be easy?)
if Angle(misclosure(results)).secondsies < 0:
    adjustment_remainder = n - adjustment_remainder
    adjustment_remainder_sign = -1
else:
    adjustment_remainder_sign = 1
print(
    f"\nadjustment per angle: "
    f"{adjustment} with an extra second for {adjustment_remainder} "
    f"random angle{'' if adjustment_remainder==1 else 's'}"
)
print(
    f"\tdouble checking: {n}x ({adjustment}) + "
    f"{adjustment_remainder}x ({adjustment_remainder_sign}\") = "
    f"{
        adjustment +
        adjustment +
        adjustment +
        adjustment +
        adjustment +
        adjustment
    } + {adjustment_remainder*adjustment_remainder_sign}\""
)

chosen_angles_for_adjustment_remainder = random.sample(
    range(n), adjustment_remainder
)
for i in chosen_angles_for_adjustment_remainder:
    results[list(results.keys())[i]][
        "angle"
    ].seconds += adjustment_remainder_sign
for s in results:
    results[s]["angle"] += adjustment
    print(s, "->", results[s]["angle"])
assert misclosure(results) == 0
print()

###################################################################### bearings
print('_' * 60, "bearings")
print("provided control point coordinates: (5008 is CP4 and 5009 is CP1)")
print(yaml.safe_dump(control_points))

x, y = [float("nan")] * (n+1), [float("nan")] * n  # for storing coordinates

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

for result in list(results.values())[:-1]:
    bearings.append((bearings[-1] + Angle(180) - result["angle"]).normalise())

print_yaml(bearings[1:])
# sanity checks: bearings should wrap around to where they started
assert bearings[0] == (
    bearings[-1] + Angle(180) - results["setup_6"]["angle"]
).normalise()

################################################################### traversals
print('_' * 60, "traversals")
backsight = [setup["distance_back_sight"] for setup in results.values()]
foresight = [setup["distance_fore_sight"] for setup in results.values()]

print("averaged distances between pairs of points:")
distances = []
for i in range(n):
    distances.append(round(avg(foresight[i], backsight[(i + 1) % n]), 4))
print_yaml(distances)
print(
    "^ should be",
    sqrt(((x[1] - x[4]) ** 2) + ((y[1] - y[4]) ** 2)),
    "according to provided coordinates",
)
print()

print(f"CP1 is at ({x[1]},{y[1]})")
points = [1,2,3,6,5,4]
eastings = []
northings = []
print()
print("Between subsequent CPs, ")
print(" Easting = distance x sin(bearing)")
print("Northing = distance x cos(bearing)")
print()
for i in range(n):
    src = points[i]
    dst = points[(i+1)%n]

    print(f"from CP{src} to CP{dst}:")

    bearing = bearings[(i+1)%n]
    distance = distances[i]

    print(f"\t bearing = {bearing}")
    print(f"\tdistance = {distance}m")

    easting = distance * sin(radians(bearing.to_decimal()))
    northing = distance * cos(radians(bearing.to_decimal()))
    eastings.append(easting)
    northings.append(northing)

    longitudinal_direction = "East" if easting > 0 else "West"
    latitudinal_direction = "North" if northing > 0 else "South"

    print(
        f"\t-> CP{dst} is {round(abs(easting),4)}m {longitudinal_direction} "
        f"and {round(abs(northing),4)}m {latitudinal_direction} of CP{src}"
    )

    x[(i+1)%n] = x[i] + easting
    y[(i+1)%n] = y[i] + northing


############################################## linear misclosure and adjustment
print('_' * 40, "linear misclosure and adjustment")

delta_E = sum(eastings)
delta_N = sum(northings)
linear_misclosure = sqrt(delta_E**2 + delta_N**2)
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
    dst = points[(i+1)%n]
    print(f"\nfrom CP{src} to CP{dst}:")
    print( "\tadjustment ration = side length / perimeter")
    print(f"\t                  = {distances[i]} / {sum(distances)}")
    print(f"\t                  = {distances[i] / sum(distances)}")
    print(f"\tEasting -= {delta_E} x {distances[i] / sum(distances)}")
    print(f"\t        -= {delta_E * distances[i] / sum(distances)}")
    print(f"\t{eastings[i]} -> {eastings[i] - (delta_E * distances[i] / sum(distances))}")
    print(f"\tNorthing -= {delta_N} x {distances[i] / sum(distances)}")
    print(f"\t         -= {delta_N * distances[i] / sum(distances)}")
    print(f"\t{northings[i]} -> {northings[i] - (delta_N * distances[i] / sum(distances))}")

    eastings[i] -= delta_E * distances[i] / sum(distances)
    northings[i] -= delta_N * distances[i] / sum(distances)
print()

################################################################### coordinates
print('_' * 60, "coordinates")
x = [control_points["5009"][1]]
y = [control_points["5009"][0]]
for i in range(n):
    x.append(x[-1] + eastings[i])
    y.append(y[-1] + northings[i])
pyplot.scatter(x[:-1], y[:-1])
for i in range(n+1):
    print(f"CP{points[i%n]}", '\t', round(x[i],4), '\t', round(y[i],4))
    pyplot.annotate(f"CP{points[i%n]}", (x[i], y[i]))
pyplot.gca().set_aspect('equal')
# show and savefig don't work at the same time
#pyplot.show()
pyplot.savefig("transparent.png", transparent=True)
pyplot.close("all")
