from dataclasses import dataclass
from pathlib import Path
from matplotlib.figure import Figure
import argparse


def handle_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=int, default=48)
    ap.add_argument("--temp-min", type=float, default=0.0)
    ap.add_argument("--temp-max", type=float, default=100.0)
    ap.add_argument("--rain-min", type=float, default=0.0)
    ap.add_argument("--rain-max", type=float, default=20.0)
    ap.add_argument("--img-width", type=int, default=800)
    ap.add_argument("--img-height", type=int, default=600)
    ap.add_argument("--user-agent")
    ap.add_argument("--post-url")
    return ap.parse_args()


@dataclass
class Weather:
    time: list[float]
    temp: list[float]
    rain: list[float]


def get_weather_forecast(user_agent: str | None) -> Weather:
    if user_agent is None:
        return Weather(
            time=[0.0, 12.0, 48.0],
            temp=[60.0, 70.0, 65.0],
            rain=[4.0, 21.0, 10.0],
        )
    raise NotImplementedError()


def plot(
    weather: Weather,
    temp_min: float,
    temp_max: float,
    rain_min: float,
    rain_max: float,
    width: int,
    height: int,
) -> Path:
    dpi = 167
    fig = Figure(figsize=(width / dpi, height / dpi), dpi=dpi)

    def sub_plot(idx: int, color: str, data: list[float], lo: float, hi: float):
        ax = fig.add_subplot(2, 1, idx)
        ax.set_ylim(lo, hi)
        ax.fill_between(x=weather.time, y1=0, y2=data, color=color)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["bottom"].set_visible(False)
        ax.spines["left"].set_visible(False)

        if idx == 1:
            ax.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)


    sub_plot(1, "gray", weather.temp, temp_min, temp_max)
    sub_plot(2, "black", weather.rain, rain_min, rain_max)

    out = Path("plot.png")
    fig.savefig(str(out), dpi=dpi)
    return out


def maybe_post(url: str | None, image: Path) -> None:
    if url is None:
        return
    raise NotImplementedError()


def main():
    args = handle_args()
    weather = get_weather_forecast(args.user_agent)
    image_path = plot(
        weather,
        args.temp_min,
        args.temp_max,
        args.rain_min,
        args.rain_max,
        args.img_width,
        args.img_height,
    )
    maybe_post(args.post_url, image_path)


if __name__ == "__main__":
    main()
