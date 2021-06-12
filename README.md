# ruta
Simple irrigation controller software for running on a single-board computer with GPIO pins (such as a raspberry pi)


# Requirements

- Single-board computer with GPIO pins running Ubuntu 21.04. Personally, I used a raspberry pi 3.
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

You can configure the webserver to run properly using something like systemd. 

# Scheduler configuration

TODO

# Sprinkler run configuration

TODO
