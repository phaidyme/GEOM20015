from functools import total_ordering


@total_ordering
class Angle:
    def __init__(self, degrees, minutes=0, seconds=0):
        # normalise minutes and seconds between -60 and 60 exclusive
        sign = -1 if seconds < 0 else 1
        while abs(seconds) >= 60:
            seconds -= 60 * sign
            minutes += 1 * sign
        sign = -1 if minutes < 0 else 1
        while abs(minutes) >= 60:
            minutes -= 60 * sign
            degrees += 1 * sign
        # make all signs the same
        if degrees >= 1:
            if minutes < 0:
                minutes += 60
                degrees -= 1
        elif degrees <= -1:
            if minutes > 0:
                minutes -= 60
                degrees += 1
        if minutes >= 1:
            if seconds < 0:
                seconds += 60
                minutes -= 1
        elif minutes <= -1:
            if seconds > 0:
                seconds -= 60
                minutes += 1
        # convert decimal degrees into D+M+S
        sign = -1 if degrees < 0 else 1
        mnt, sec = divmod(abs(degrees) * 3600, 60)
        deg, mnt = divmod(mnt, 60)
        deg *= sign
        mnt *= sign
        sec *= sign
        # convert  decimal minutes into M+S
        sign = -1 if minutes < 0 else 1
        mnt_2, sec_2 = divmod(abs(minutes) * 60, 60)
        mnt_2 *= sign
        sec_2 *= sign
        # finalise
        self.degrees = deg

        assert self.degrees % 1 == 0
        self.degrees = int(self.degrees)

        self.minutes = mnt + mnt_2
        assert self.minutes % 1 == 0
        self.minutes = int(self.minutes)

        self.secondsies = sec + sec_2 + seconds
        self.seconds = int(round(self.secondsies))

    def __repr__(self):
        return f"{self.degrees} {self.minutes}' {self.seconds}\" ({self.secondsies})"

    def __add__(self, other):
        return Angle(
            self.degrees + other.degrees,
            self.minutes + other.minutes,
            self.seconds + other.seconds,
        )

    def __radd__(self, other):
        return Angle(other) + self

    def __rsub__(self, other):
        return Angle(other) - self

    def __sub__(self, other):
        return Angle(
            self.degrees - other.degrees,
            self.minutes - other.minutes,
            self.seconds - other.seconds,
        )

    def __truediv__(self, other):
        return Angle(
            self.degrees / other,
            self.minutes / other,
            self.secondsies / other,
        )

    def __lt__(self, other):
        if self.degrees < other.degrees:
            return True
        elif self.degrees == other.degrees:
            if self.minutes < other.minutes:
                return True
            elif self.minutes == other.minutes:
                return self.seconds < other.seconds
            else:
                return False
        else:
            return False

    def __eq__(self, other):
        return (
            self.degrees == other.degrees
            and self.minutes == other.minutes
            and self.seconds == other.seconds
        )

    def to_decimal(self):
        return self.degrees + (self.minutes / 60) + (self.seconds / (60 * 60))

    def normalise(self):
        return Angle(self.degrees % 360, self.minutes, self.secondsies)
