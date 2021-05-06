# -*- mode: ruby -*-
# vi: set ft=ruby :


Vagrant.configure("2") do |config|

    config.vm.box = "hashicorp/bionic64"
  
    # config.vm.box_check_update = false
    config.vm.network "forwarded_port", guest: 8888, host: 8888
    config.vm.network "forwarded_port", guest: 6006, host: 6006 # tensorboard
    
    # config.vm.network "forwarded_port", guest: 8000, host: 8000
  
    # config.vm.network "private_network", ip: "192.168.33.10"
  
    # config.vm.network "public_network", ip: "192.168.50.200"
  
    config.vm.synced_folder ".", "/home/vagrant/project", id: "project"
    config.vm.synced_folder "../bert", "/home/vagrant/bert", id: "bert"
  
    
    # Provider Settings
    config.vm.provider "virtualbox" do |vb|
      # Display the VirtualBox GUI when booting the machine
      vb.gui = false
    
      # Customize the amount of memory on the VM:
      vb.memory = "8192"
      vb.cpus = 4
    end
  
    # config.vm.provision "shell", inline: <<-SHELL
    #   apt-get update
    #   apt-get install -y apache2
    # SHELL
  
    config.vm.provision "shell", path: "bootstrap.sh"
  
  end
  