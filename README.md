# ruta
Simple irrigation controller software for running on a single-board computer with GPIO pins (such as a raspberry pi)

![image](https://user-images.githubusercontent.com/5097634/121789516-9a602780-cba4-11eb-8d0d-7ca85b22de75.png)


# Requirements

- Single-board computer with GPIO pins running Ubuntu 21.04. Technically, any distro with [Linux kernel >= 5.11 should work](https://ubuntu.com/tutorials/gpio-on-raspberry-pi#1-overview), but I only tested against Ubuntu 21.04. 
- A 5V Relay Module with Optocoupler Isolation. You'll need enough channels to support all of your zones. 
- 2 female-to-female jumper wires for the ground and 5V connection to the relay
- `N` female-to-female jumper wires for connecting the irrigation zone wires, where `N` is the the total number of zones you have.
- A power supply that works with your irrigation system. Mine was 24V.
- Python >= 3.8 (I believe this is the default version on Ubuntu 21.04, so you may not need to do anything here)

For the wiring side, I followed this [hackster tutorial](https://www.hackster.io/Ryan33/raspberry-pi-web-page-based-sprinkler-controller-00d26f) mostly. Please be cautious when working with electricity. 

# Install
```
./bootstrap.sh
```

This will prompt you for your root password to install certain dependencies. Additionally, it will prompt you to create an admin user you can use to login into the django admin console.

Note that the lgpio dependency has to be installed via `apt` as of now, which makes it hard to use a proper virtual environment such as poetry. I'm looking into alternatives to this library.

# Running for development
```
make run
```

Starts a server on port 9000. The admin console is at <your_local_pi_ip_address>:9000/admin. 
The `make run` target enables Django debug mode so static assets are served locally by the development server.

The dashboard now requires a Django username and password. Use the admin account created during `./bootstrap.sh`, or create one with:

```
make createsuperuser
```

You can configure the webserver to run properly using something like systemd. 

# Scheduler configuration

TODO

# Sprinkler run configuration

TODO

# Production static files and automatic updates

Edit assets in `ruta/irrigate/static/`. `ruta/ruta/static/` is generated output
served by Nginx, and must not be committed. After updating code, run:

```sh
cd ruta
python3 manage.py collectstatic --noinput --clear
```

GitHub Actions tests pushes to `main` and promotes successful commits to
`deploy-ready`. The Pi's `ruta-update.timer` polls that branch every minute.
It tests a staged copy, checks migrations, pauses scheduler launches, defers
while a watering job runs, updates code, rebuilds static assets, reloads Gunicorn,
and checks the login page and dashboard CSS. A failed health check restores the
previous code and assets. Local source edits, dependency changes, and pending
migrations block deployment for manual maintenance; the live SQLite database
and service environment remain on the Pi.

The supplied units target the existing installation at `/home/ubuntu/src/ruta`.
Install `deploy/update.sh` as `/usr/local/lib/ruta/update.sh`, and the two units
under `/etc/systemd/system/`. The `ubuntu` user needs GitHub read access,
`freezegun` for staged tests, and passwordless permission to stop/start
`ruta_scheduler.timer` and reload `ruta.service`. Enable with:

```sh
sudo systemctl daemon-reload
sudo systemctl enable --now ruta-update.timer
journalctl -u ruta-update.service
```

Updater and unit changes require reinstalling these root-owned files separately.
