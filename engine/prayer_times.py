"""
Project Zia - Islamic Prayer Time Calculation & Gentle Check-in Engine
Custom-tailored for Palakkad, Kerala (Latitude 10.7867° N, Longitude 76.6548° E)
100% offline, zero external dependencies, astronomical solar calculation (<0.1ms CPU).
"""

import math
from datetime import datetime, timezone, timedelta, date
from typing import Dict, Any, List, Optional
from engine.memory import memory_engine


class PalakkadPrayerEngine:
    """
    Astronomical solar prayer calculation engine for Palakkad, Kerala.
    Employs Shafi'i juristic convention (shadow factor = 1) and standard 18° angles.
    """

    # Regional geographic coordinates for Palakkad, Kerala
    DEFAULT_LAT = 10.7867
    DEFAULT_LNG = 76.6548
    DEFAULT_TIMEZONE_OFFSET = 5.5  # Asia/Kolkata (UTC +05:30)

    # Shafi'i juristic shadow factor
    SHADOW_FACTOR = 1.0
    FAJR_ANGLE = 18.0
    ISHA_ANGLE = 18.0

    def __init__(self, lat: float = DEFAULT_LAT, lng: float = DEFAULT_LNG, tz_offset: float = DEFAULT_TIMEZONE_OFFSET):
        self.lat = lat
        self.lng = lng
        self.tz_offset = tz_offset
        self.tz = timezone(timedelta(hours=int(tz_offset), minutes=int((tz_offset % 1) * 60)))

        # Tracking for gentle check-in prompts (prayer_name -> date_str)
        self.prompted_today: Dict[str, str] = {}
        self.last_checkin_prayer: Optional[str] = None
        self.last_checkin_time: float = 0.0

    # -------------------------------------------------------------------------
    # Solar Astronomical Core Algorithms (Jean Meeus / PrayTimes standard)
    # -------------------------------------------------------------------------
    @staticmethod
    def _dsin(d: float) -> float:
        return math.sin(math.radians(d))

    @staticmethod
    def _dcos(d: float) -> float:
        return math.cos(math.radians(d))

    @staticmethod
    def _dtan(d: float) -> float:
        return math.tan(math.radians(d))

    @staticmethod
    def _darccos(x: float) -> float:
        x = max(-1.0, min(1.0, x))
        return math.degrees(math.acos(x))

    @staticmethod
    def _darccot(x: float) -> float:
        return math.degrees(math.atan(1.0 / x))

    @staticmethod
    def _julian_day(year: int, month: int, day: int) -> float:
        if month <= 2:
            year -= 1
            month += 12
        a = math.floor(year / 100)
        b = 2 - a + math.floor(a / 4)
        return math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + b - 1524.5

    def _sun_position(self, jd: float) -> tuple[float, float]:
        """Calculates solar declination and equation of time (hours)."""
        d = jd - 2451545.0
        g = (357.529 + 0.98560028 * d) % 360
        q = (280.459 + 0.98564736 * d) % 360
        l = (q + 1.915 * self._dsin(g) + 0.020 * self._dsin(2 * g)) % 360
        e = 23.439 - 0.00000036 * d

        ra = math.degrees(math.atan2(self._dcos(e) * self._dsin(l), self._dcos(l))) / 15.0
        ra = (ra + 24) % 24

        declination = math.degrees(math.asin(self._dsin(e) * self._dsin(l)))
        eot = (q / 15.0) - ra
        if eot > 12:
            eot -= 24
        if eot < -12:
            eot += 24
        return declination, eot

    def _hour_angle(self, alpha: float, dec: float) -> float:
        """Computes hour angle for a given solar altitude angle alpha."""
        top = self._dsin(alpha) - self._dsin(self.lat) * self._dsin(dec)
        bottom = self._dcos(self.lat) * self._dcos(dec)
        if abs(bottom) < 1e-6:
            return 0.0
        val = top / bottom
        if val > 1.0 or val < -1.0:
            return 0.0
        return self._darccos(val) / 15.0

    def get_prayer_times(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Calculates today's prayer times for Palakkad, Kerala.
        Returns dictionary of prayer items with name, time string, float hour, and datetime.
        """
        now = datetime.now(self.tz)
        if target_date is None:
            t_date = now.date()
        else:
            t_date = target_date

        jd = self._julian_day(t_date.year, t_date.month, t_date.day) - (self.lng / (15.0 * 24.0))
        dec, eot = self._sun_position(jd)

        # Midday solar transit (Dhuhr)
        noon = 12.0 + self.tz_offset - (self.lng / 15.0) - eot

        # Fajr (Subhi): -18°
        fajr_ha = self._hour_angle(-self.FAJR_ANGLE, dec)
        fajr_hour = noon - fajr_ha

        # Sunrise: -0.833°
        sunrise_ha = self._hour_angle(-0.833, dec)
        sunrise_hour = noon - sunrise_ha

        # Asr (Shafi'i shadow factor = 1)
        asr_alpha = self._darccot(self.SHADOW_FACTOR + self._dtan(abs(self.lat - dec)))
        asr_ha = self._hour_angle(asr_alpha, dec)
        asr_hour = noon + asr_ha

        # Maghrib (Sunset): -0.833°
        maghrib_hour = noon + sunrise_ha

        # Isha: -18°
        isha_ha = self._hour_angle(-self.ISHA_ANGLE, dec)
        isha_hour = noon + isha_ha

        def to_datetime(hour_float: float) -> datetime:
            h = hour_float % 24
            hh = int(h)
            mm = int(round((h - hh) * 60))
            if mm == 60:
                hh += 1
                mm = 0
            base = datetime(t_date.year, t_date.month, t_date.day, tzinfo=self.tz)
            return base.replace(hour=hh % 24, minute=mm, second=0, microsecond=0)

        def to_str(dt: datetime) -> str:
            return dt.strftime("%H:%M")

        def to_12h(dt: datetime) -> str:
            return dt.strftime("%I:%M %p")

        subhi_dt = to_datetime(fajr_hour)
        sunrise_dt = to_datetime(sunrise_hour)
        dhuhr_dt = to_datetime(noon)
        asr_dt = to_datetime(asr_hour)
        maghrib_dt = to_datetime(maghrib_hour)
        isha_dt = to_datetime(isha_hour)

        return {
            "date": t_date.strftime("%Y-%m-%d"),
            "location": "Palakkad, Kerala (10.7867° N, 76.6548° E)",
            "prayers": [
                {"name": "Subhi", "canonical": "Fajr", "time": to_str(subhi_dt), "time_12h": to_12h(subhi_dt), "dt": subhi_dt, "timestamp": subhi_dt.timestamp()},
                {"name": "Sunrise", "canonical": "Shurooq", "time": to_str(sunrise_dt), "time_12h": to_12h(sunrise_dt), "dt": sunrise_dt, "timestamp": sunrise_dt.timestamp()},
                {"name": "Dhuhr", "canonical": "Dhuhr", "time": to_str(dhuhr_dt), "time_12h": to_12h(dhuhr_dt), "dt": dhuhr_dt, "timestamp": dhuhr_dt.timestamp()},
                {"name": "Asr", "canonical": "Asr", "time": to_str(asr_dt), "time_12h": to_12h(asr_dt), "dt": asr_dt, "timestamp": asr_dt.timestamp()},
                {"name": "Maghrib", "canonical": "Maghrib", "time": to_str(maghrib_dt), "time_12h": to_12h(maghrib_dt), "dt": maghrib_dt, "timestamp": maghrib_dt.timestamp()},
                {"name": "Isha", "canonical": "Isha", "time": to_str(isha_dt), "time_12h": to_12h(isha_dt), "dt": isha_dt, "timestamp": isha_dt.timestamp()},
            ]
        }

    def get_next_prayer(self) -> Dict[str, Any]:
        """
        Returns the next upcoming prayer in Palakkad and countdown.
        """
        now = datetime.now(self.tz)
        now_ts = now.timestamp()
        times_today = self.get_prayer_times(now.date())

        for p in times_today["prayers"]:
            if p["name"] == "Sunrise":
                continue  # Sunrise is astronomical reference, not prayer
            if p["timestamp"] > now_ts:
                diff_sec = int(p["timestamp"] - now_ts)
                hours = diff_sec // 3600
                minutes = (diff_sec % 3600) // 60
                countdown_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
                return {
                    "name": p["name"],
                    "canonical": p["canonical"],
                    "time": p["time"],
                    "time_12h": p["time_12h"],
                    "timestamp": p["timestamp"],
                    "seconds_remaining": diff_sec,
                    "countdown": countdown_str,
                    "is_tomorrow": False
                }

        # If all prayers today passed, return tomorrow's Subhi
        tomorrow = now.date() + timedelta(days=1)
        times_tomorrow = self.get_prayer_times(tomorrow)
        subhi = times_tomorrow["prayers"][0]
        diff_sec = int(subhi["timestamp"] - now_ts)
        hours = diff_sec // 3600
        minutes = (diff_sec % 3600) // 60
        countdown_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        return {
            "name": subhi["name"],
            "canonical": subhi["canonical"],
            "time": subhi["time"],
            "time_12h": subhi["time_12h"],
            "timestamp": subhi["timestamp"],
            "seconds_remaining": diff_sec,
            "countdown": countdown_str,
            "is_tomorrow": True
        }

    def check_prayer_prompt_needed(self) -> Optional[Dict[str, Any]]:
        """
        Checks if any prayer entered its gentle check-in window (within 0 - 20 minutes
        after prayer start time) and has not yet been prompted today.
        """
        now = datetime.now(self.tz)
        today_str = now.strftime("%Y-%m-%d")
        now_ts = now.timestamp()
        times_today = self.get_prayer_times(now.date())

        for p in times_today["prayers"]:
            if p["name"] == "Sunrise":
                continue

            # Within 0 to 20 minutes after prayer start
            p_ts = p["timestamp"]
            if 0 <= (now_ts - p_ts) <= 1200:
                p_name = p["name"]
                # Check if already prompted today
                if self.prompted_today.get(p_name) != today_str:
                    self.prompted_today[p_name] = today_str
                    self.last_checkin_prayer = p_name
                    self.last_checkin_time = now_ts
                    return {
                        "prayer": p_name,
                        "time_12h": p["time_12h"],
                        "prompt": f"Hey, {p_name} time in Palakkad has started. Did you manage to pray yet?"
                    }

        return None

    def record_prayer_status(self, prayer_name: Optional[str] = None, status: str = "completed") -> Dict[str, Any]:
        """
        Persists prayer habit status to data/memory.json.
        """
        now = datetime.now(self.tz)
        target_prayer = prayer_name or self.last_checkin_prayer or "Prayer"

        record = {
            "prayer": target_prayer,
            "status": status,
            "timestamp": now.timestamp(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%I:%M %p"),
            "location": "Palakkad, Kerala"
        }

        # Save into memory_engine persistent structure
        if "prayer_log" not in memory_engine.data:
            memory_engine.data["prayer_log"] = []

        memory_engine.data["prayer_log"].append(record)
        # Keep last 30 prayer records
        if len(memory_engine.data["prayer_log"]) > 30:
            memory_engine.data["prayer_log"] = memory_engine.data["prayer_log"][-30:]
        memory_engine.save()

        # Clear active check-in so she doesn't re-ask
        self.last_checkin_prayer = None

        return {"success": True, "prayer": target_prayer, "record": record}

    def get_prayer_log(self, limit: int = 7) -> List[Dict[str, Any]]:
        """Retrieves recent prayer logs from memory.json."""
        logs = memory_engine.data.get("prayer_log", [])
        return logs[-limit:]

    def format_schedule_table(self) -> str:
        """Formats today's Palakkad prayer times into an ANSI table."""
        now = datetime.now(self.tz)
        now_ts = now.timestamp()
        data = self.get_prayer_times(now.date())
        next_p = self.get_next_prayer()

        lines = []
        lines.append(f"\033[1mPALAKKAD, KERALA PRAYER TIMES\033[0m ({data['date']})")
        lines.append(f"\033[90mCoordinates: 10.7867 N, 76.6548 E (Asia/Kolkata IST)\033[0m\n")

        for p in data["prayers"]:
            is_passed = p["timestamp"] < now_ts
            is_next = (p["name"] == next_p["name"] and not next_p["is_tomorrow"])
            if is_next:
                bullet = "\033[92m>\033[0m"
                color = "\033[92m\033[1m"
                tag = f" (Next in {next_p['countdown']})\033[0m"
            elif is_passed:
                bullet = "\033[90m-\033[0m"
                color = "\033[90m"
                tag = " (Passed)\033[0m"
            else:
                bullet = "*"
                color = "\033[97m"
                tag = "\033[0m"

            lines.append(f" {bullet} {color}{p['name']:8s}\033[0m : {p['time_12h']:8s}{tag}")

        lines.append(f"\n\033[96mNext Prayer: {next_p['name']} at {next_p['time_12h']} ({next_p['countdown']} remaining)\033[0m")
        return "\n".join(lines)


# Global prayer times singleton
prayer_engine = PalakkadPrayerEngine()
