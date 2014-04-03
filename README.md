# elif

### Dependencies

If you're on Ubuntu or Debian (with recent repositories), just launch ``sudo install-dependencies.sh``

Otherwise :

* Install Python 2.7

        sudo apt-get install python

* Install Python dependencies

        sudo apt-get install python-pip
        sudo pip install -r requirements.txt

* Install mongodb (may require a reboot)

        sudo apt-get install mongodb

* Install clang

        sudo apt-get install clang

### Deploying

Two different processes need to be launched in order for elif to work : the web server (``web.py``),
and ``greedy`` (our compilations' job processor)

To deploy elif with a development server, just launch ``web.py`` :

    cd src/
    python web.py

If you want to launch it with a "real" server, you can use gunicorn :

First install it with ``pip``
    sudo pip install gunicorn

Then do the following (change 5000 with the port you want to use) :

    gunicorn -b 0.0.0.0:5000 web:app

``greedy`` needs to be launched with root privileges, you simply have to do :

    sudo python greedy.py