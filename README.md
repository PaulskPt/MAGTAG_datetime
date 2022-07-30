# MAGTAG_datetime
 Receive, fliter and use the Adafruit IO Time service response to set and use the built-in RTC of the MAGTAG

Software:
See 'src'

Used hardware:

a) Adafruit MAGTAG - 2.0 inch Grayscale E-ink WiFi Display (Product ID: 4800) https://www.adafruit.com/product/4800).
  
```Notes about the script:```

This script used https://learn.adafruit.com/adafruit-magtag/getting-the-date-time as source.

This version of the latter script has various modifications:
1) Use the response of the Adafruit IO Time Service HTTTP request to filter the needed datetime items to set the built-in RTC of the MAGTAG.
2) After an initial setting the built-in RTC with the response data of the Adafruit IO Time Service request, the built-in RTC will be polled every minute;
3) Next, at the change of the hour of the built-in RTC, the buil-tin RTC will be synchronized with fresh Adafruit IO Time Service data

Note about the strftime 'day of the week' value:
I discovered that, while the Adafruit IO Time Service response contains a 'day-of-the-week' value that uses 0 as base (Monday = 0),
while the built-in RTC datetime() function returns a 'day-of-the-week' value taht uses 1 as base (Monday = 1)

```Example:```

Adafruit IO Time Service ```response.text="2022-07-29 23:53:23.081 210 5 +0100 WEST"```
In this response text the 'day-of-the-week' value is '5'. Which indicates that the date 2202-07-29 was a 'Friday'
After setting the MAGTAG's built-in RTC, the result of 'r.datetime()' was: 
```struct_time(tm_year=2022, tm_mon=7, tm_mday=29, tm_hour=23, tm_min=54, tm_sec=0, tm_wday=4, tm_yday=210, tm_isdst=-1)```
In this RTC datetime result the 'day-of-the-week' value is 4 for the same date: 2022-07-29.

```Conclusion:```
The built-in RTC datetime function uses base 0 for the 'day-of-the-week' value. Resulting in: weekday 4 = Friday.

I am in contact with the maintainers of Circuitpython about this.

In the ``doc``` folder an example of a REPL output of the script.

Note the script uses a class ```my_dat``` to hold various values. One of them is ```_debug```. This is in various functions used to set a local flag ```my_debug```, used for debugging of informative REPL output printing.

In the ```images``` folder an image of the datetime presentation on the MAGTAG.


License: MIT (see LICENSE file)