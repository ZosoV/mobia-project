# Requirements

## Install Docker
* Please, refer to [Get Docker | Docker Documentation](https://docs.docker.com/get-docker/).
* If applicable, follow the [Post-installation steps for Linux| Docker Documentation](https://docs.docker.com/engine/install/linux-postinstall/).
* Set permissions to Docker.
```
sudo chmod 666 /var/run/docker.sock
```
* Log in to the Docker Registry using the CLI.
    * Username: `$oauthtoken`
    * Password: Generate it from [NVIDIA NGC](https://catalog.ngc.nvidia.com/).
    * API Key: Follow the instructions for [Generating your NGC API Key](https://docs.nvidia.com/ngc/ngc-overview/index.html#generating-api-key).
```
docker login nvcr.io
```

## Install Anaconda
* Please, refer to [Installation — Anaconda documentation](https://docs.anaconda.com/anaconda/install/).
* When Anaconda is installed, create a new environment for this model and install Jupyter Lab, Pip and Python 3.7.13 inside it.
```
conda create -n mobia_lpd jupyterlab pip python=3.7.13
conda activate mobia_lpd
```

## Create IPyKernel
* In order to run the correct Python kernel version, create a new IPyKernel.
```
python -m ipykernel install --user --name=mobia_lpd
```

## Activate Jupyter Lab
* Open Jupyter Lab with tunneling configuration.
```
jupyter lab --no-browser --port <port-number>
```
* In local machine, open CLI and run the following command with the correct values to connect with remote Jupyter Lab.
```
ssh -N -L localhost:<local-port>:localhost:<remote-port> <remote-user>@<remote-host>
```
* Open Jupyter Lab in local browser.
```
http://localhost:<local-port>/
```
* Activate mobia_lpd kernel.

## Follow the Notebook
* Open the [lpdnet_train.ipynb](lpdnet_train.ipynb) and follow the instructions.
