import argparse
import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter, HourLocator
from matplotlib.ticker import MaxNLocator
from zoneinfo import ZoneInfo

import requests


def handle_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=int, default=48, help="hours")
    ap.add_argument("--rain-min", type=float, default=0.0, help="mm/hr")
    ap.add_argument("--rain-max", type=float, default=15.0, help="mm/hr")
    ap.add_argument("--img-width", type=int, default=800, help="pixels")
    ap.add_argument("--img-height", type=int, default=600, help="pixels")
    ap.add_argument("--lat", type=float, default=47.6, help="decimal degrees")
    ap.add_argument("--lon", type=float, default=-122.2, help="decimal degrees")
    ap.add_argument("--time-zone", default="America/Los_Angeles", help="ZoneInfo")
    ap.add_argument("--user-agent", help="identifying string for api.met.no")
    ap.add_argument("--post-url", help="where to send the image")
    return ap.parse_args()


SEATTLE_TEMPS = [
    (20, 70),  # jan
    (20, 70),  # feb
    (20, 70),  # mar
    (30, 80),  # apr
    (30, 80),  # may
    (40, 90),  # jun
    (40, 90),  # jul
    (50, 100),  # aug
    (40, 90),  # sep
    (30, 80),  # oct
    (20, 70),  # nov
    (20, 70),  # dec
]


@dataclass
class Weather:
    generation_time: dt.datetime
    time: list[dt.datetime]
    temp: list[float]  # F
    rain: list[float]  # mm/hour


def f_from_c(c: float) -> float:
    return 9 * c / 5 + 32.0


def parse_weather(d: dict, duration: int) -> Weather:
    props = d["properties"]
    time = []
    temp = []
    rain = []
    for p in props["timeseries"]:
        time.append(dt.datetime.fromisoformat(p["time"]))
        temp.append(f_from_c(float(p["data"]["instant"]["details"]["air_temperature"])))
        rain.append(float(p["data"]["next_1_hours"]["details"]["precipitation_amount"]))
        if len(time) > 2 and time[-1] - time[0] > dt.timedelta(hours=duration):
            break
    return Weather(
        generation_time=dt.datetime.fromisoformat(props["meta"]["updated_at"]),
        time=time,
        temp=temp,
        rain=rain,
    )


def get_weather(
    user_agent: str | None, duration: int, lat: float, lon: float
) -> Weather:
    example_path = Path("example_weather.json")
    if example_path.exists():
        with example_path.open() as f:
            return parse_weather(json.load(f), duration)
    assert user_agent is not None
    response = requests.get(
        url="https://api.met.no/weatherapi/locationforecast/2.0/compact",
        headers={
            "user-agent": user_agent,
        },
        params=[
            ("lat", str(round(lat, 2))),
            ("lon", str(round(lon, 2))),
        ],
    )
    response.raise_for_status()
    response_json = response.json()
    with example_path.open("w") as f:
        json.dump(response_json, f)
    return parse_weather(response_json, duration)


def plot(
    weather: Weather,
    temp_min: float,
    temp_max: float,
    rain_min: float,
    rain_max: float,
    width: int,
    height: int,
    tz: ZoneInfo,
) -> Path:
    dpi = 167
    fig = Figure(figsize=(width / dpi, height / dpi), dpi=dpi, layout="constrained")
    NUM_ROW = 2
    NUM_COL = 1

    def sub_plot(idx: int, color: str, data: list[float], lo: float, hi: float):
        ax = fig.add_subplot(NUM_ROW, NUM_COL, idx)
        ax.set_ylim(lo, hi)
        ax.set_xlim(weather.time[0], weather.time[-1])
        ax.fill_between(
            x=weather.time,  # ty: ignore[invalid-argument-type]
            y1=lo,
            y2=data,
            color=color,
        )

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["bottom"].set_visible(True)
        ax.spines["left"].set_visible(True)

        # vertical lines at midnights
        midnight = (
            weather.time[0]
            .astimezone(tz=tz)
            .replace(hour=0, minute=0, second=0, microsecond=0)
        )
        while midnight < weather.time[-1]:
            ax.axvline(midnight, color="black", linestyle=(0, (1, 10)), linewidth=1.0)
            midnight += dt.timedelta(hours=24)

        if idx == 1:  # on top
            # Weekdays at noons
            noon = (
                weather.time[0]
                .astimezone(tz=tz)
                .replace(hour=12, minute=0, second=0, microsecond=0)
            )
            while noon < weather.time[-1]:
                if noon > weather.time[0]:
                    ax.text(
                        x=noon,
                        y=lo - (hi - lo) * 0.12,
                        s=noon.strftime("%a"),
                        horizontalalignment="center",
                    )
                noon += dt.timedelta(hours=24)

        ax.grid(
            which="major",
            axis="y",
            visible=True,
            linestyle=":",
            linewidth=0.5,
            color="black",
        )
        ax.tick_params(axis="both", which="major", labelsize=8)

        if idx != NUM_ROW:
            # remove x axis for all but the bottom plot
            ax.tick_params(
                axis="x", which="both", bottom=False, top=False, labelbottom=False
            )
        else:
            ax.xaxis.set_major_locator(HourLocator(byhour=[0, 6, 12, 18], tz=tz))
            ax.xaxis.set_major_formatter(DateFormatter("%H", tz=tz))
            generated = weather.generation_time.astimezone(tz=tz).strftime("%a %H:%M")
            ax.set_xlabel(f"forecast {generated}", fontsize=4)

        return ax

    rain_ax = sub_plot(1, "darkgray", weather.rain, rain_min, rain_max)
    temp_ax = sub_plot(2, "lightgray", weather.temp, temp_min, temp_max)

    rain_ax.set_ylabel(
        r"$\frac{\text{mm}}{\text{hr}}$", rotation="horizontal", labelpad=8
    )
    rain_ax.yaxis.set_major_locator(MaxNLocator(nbins=3))

    temp_ax.set_ylabel("°F", rotation="horizontal", labelpad=8)
    temp_ax.yaxis.set_major_locator(MaxNLocator(nbins=5))

    out = Path("plot.png")
    fig.savefig(str(out), dpi=dpi)
    return out


def maybe_post(url: str | None, image: Path) -> None:
    if url is None:
        return
    raise NotImplementedError()


def main():
    args = handle_args()
    tz = ZoneInfo(args.time_zone)
    weather = get_weather(args.user_agent, args.duration, args.lat, args.lon)
    start = weather.time[0].astimezone(tz=tz)
    temp_min, temp_max = SEATTLE_TEMPS[start.month]
    image_path = plot(
        weather,
        temp_min,
        temp_max,
        args.rain_min,
        args.rain_max,
        args.img_width,
        args.img_height,
        tz,
    )
    maybe_post(args.post_url, image_path)


if __name__ == "__main__":
    main()
