# TRMNL Weather Plot

Generate images for TRMNL to show weather forecast plots.

Stacked plot of temperature and rainfall density.
Optimized for small grayscale screen, viewable from across the room.

## In Python

1. Take arguments:
  * webhook URL, string. required
  * user-agent, string. required
  * duration, hours. default 48.
  * axes limits. default: 0-100 F. 0-20 mm/hour
  * image dimensions, pixels. default 800x600
  * dry run, boolean. default False.
1. grab hourly weather forecast from api.met.no for temperature and rainfall over the duration
  * Use user-agent to identify self to api.met.no
1. Generate a stacked grayscale plot
  * x axis is duration. with hours in 24-hour format (0-23)
  * y axis limits are fixed by config input, not scaled to data
  * Top plot is temperature (deg F).
  * Bottom plot is rainfall density (mm/hour). 
  * Above the top plot, day of week and date number are shown. Centered on noon of that day, if there is enough space.
  * Vertical dashed line at midnight
  * Linear interpolation between measurements (lines not bar graphs)
  * Shading underneath values (gray for temp, black for rain)
  * In small text in the corner, include generation time.
1. Export image as png with requested size. Save to disk in current working directory.
1. If not dry run, POST image to the webhook URL

## In Github actions

* Schedule: Every 30 minutes, run plot.py.
* Set user agent to URL of this repository (don't hard code because people may fork)
* Save webhook URL in a secrets database of some kind (however github actions offers?)
* Stretch goal: let people override more arguments without changing the code.
