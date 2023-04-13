#!/usr/bin/env bash

cp /vagrant/vagrant-files/bootstrap-files/known_hosts ~/.ssh/known_hosts

sudo apt-get -y update
sudo apt-get -y autoremove
sudo apt-get -y upgrade
sudo apt-get -y install git
sudo apt-get -y install phantomjs=1.9.0-1
sudo apt-get -y install tree=1.6.0-1

source /vagrant/vagrant-files/bootstrap-files/rabbitmq
source /vagrant/vagrant-files/bootstrap-files/postgres
source /vagrant/vagrant-files/bootstrap-files/python
source /vagrant/vagrant-files/bootstrap-files/venv
source /vagrant/vagrant-files/bootstrap-files/celery
source /vagrant/vagrant-files/bootstrap-files/redis
source /vagrant/vagrant-files/bootstrap-files/supervisord

# create the Django db tables
cd /vagrant/src
python manage.py migrate

# add stuff to .bashrc
echo "source /vagrant/vagrant-files/bashrc" >> /home/vagrant/.bashrc

if [ -f /vagrant/vagrant-files/custom_bashrc ]; then
    echo "source /vagrant/vagrant-files/custom_bashrc" >> /home/vagrant/.bashrc
fi

# ptpython config
mkdir /home/vagrant/.ptpython
cp /vagrant/vagrant-files/pt-python-config.py /home/vagrant/.ptpython/config.py

# set timezone
echo "US/Eastern" | sudo tee /etc/timezone
sudo /usr/sbin/dpkg-reconfigure --frontend noninteractive tzdata
