# -*- mode: ruby -*-
# vi: set ft=ruby :

unless Vagrant.has_plugin?("vagrant-vbguest")
  raise 'first do "vagrant plugin install vagrant-vbguest"'
end

Vagrant.configure(2) do |config|
  config.ssh.forward_agent = true

  # to prevent ssh port collisions with the ge-govexec vagrant vm
  config.vm.network :forwarded_port, id: "ssh", guest: 22, host: 2230, auto_correct: true

  config.vm.box = "ubuntu/trusty64"
  config.vm.provision :shell, path: "vagrant-files/bootstrap.sh"
  config.vm.synced_folder ".", "/vagrant", disabled: false
  config.vm.network "forwarded_port", guest: 8001, host: 7979  # django
  config.vm.network :forwarded_port, guest: 5432, host: 15432   # postgres
  config.vm.network :forwarded_port, guest: 8002, host: 7980   # flower
  config.vm.network :forwarded_port, guest: 6379, host: 7981   # redis
  config.vm.provider "virtualbox" do |vb|
     vb.memory = "2048"
     vb.cpus = 4
     vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
  end

end
