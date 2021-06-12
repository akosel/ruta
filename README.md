# ruta
Simple rasperry pi controller for irrigation system


# Requirements

- Raspberry pi 3 or 4 running Ubuntu 21.04
- Python >= 3.8

# Install
./bootstrap.sh

This will prompt you for your root password to install certain dependencies. Additionally, it will prompt you to create an admin user you can use to login into the django admin console.

Note that the lgpio dependency has to be installed via `apt` as of now, which makes it hard to use a proper virtual environment such as poetry. I'm looking into alternatives to this library.

# Running for development
make run

Starts a server on port 9000. The admin console is at <your_local_pi_ip_address>:9000/admin. 

You can configure the webserver to run properly using something like systemd. 

# Scheduler configuration

TODO

# Sprinkler run configuration

TODO
