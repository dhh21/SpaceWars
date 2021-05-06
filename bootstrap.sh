sudo apt-get update && sudo apt-get -y upgrade

sudo apt install -y python3-pip python3-dev

sudo apt-get -y install pandoc
sudo apt-get -y install texlive-xetex texlive-fonts-recommended

yes | sudo -H pip3 install --upgrade pip

yes | pip3 install jupyter nbconvert jupyterlab jupyter_contrib_nbextensions


jupyter contrib nbextension install --user
# https://jupyter-contrib-nbextensions.readthedocs.io/en/latest/install.html


# Interactive Reveal.js
# https://rise.readthedocs.io/en/stable/installation.html
pip3 install RISE
jupyter-nbextension install rise --py --sys-prefix
jupyter nbextension enable rise --py --sys-prefix

pip3 install tensorflow==1.15.0 sklearn seaborn
pip3 install transformers

pip3 install torch==1.7.1+cpu torchvision==0.8.2+cpu -f https://download.pytorch.org/whl/torch_stable.html


# https://owendavies.net/articles/install-jupyter-notebook-on-ubuntu/