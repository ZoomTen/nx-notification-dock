# nx-notification-dock
A vertical notification dock written in PyQt5, works in Linux / BSD.

Best used embedded in a panel/sidebar (preview uses `xfce4-panel` with `xfce4-embed-plugin`)

![Preview](https://raw.githubusercontent.com/ZoomTen/nx-notification-dock/master/preview.gif)

Requires:

* `python3` with `PyQt5`
* Working freedesktop-compliant d-bus and notifications
* "Franklin Gothic Medium" font, though you can change this *in `nx-notify.py`* at the moment.

Features:

* Simple notification viewing
* Marquee/ticker style for longer text
* Simple notification grouping (by summary/subject)
* Notification logging (to `/tmp/notifs-20180715.txt`, for example)

Execution:

`chmod +x && ./nx-notify.py` -or- `python3 nx-notify.py`