# mobia-project

* The present repository contains all information about data preparation and training for **Mobia Project License Plate Detection**.

* Please, take into account that each model needs a **different virtual environment and kernel**.

* The three root directories refers to the main work flow modules in execution order: **preparation, training, and deployment**.

* For now, we can find each model in [training](https://github.com/ZosoV/mobia-project/tree/master/training) folder.

## Script formatting

In order to follow the [PEP8](pep8.org), we use the [pre-commit](pre-commit.com) hook scripts. Next, we present the steps to run them.

* Create or activate a conda environment.
```
conda create -n <name>
conda activate <name>
```

* Ensure to have pip and upgraded
```
conda install pip
conda config --add channels conda-forge 
conda update pip
```

* Install pre-commit.

```
pip install pre-commit
```

* Use pre-commit command.
```
pre-commit run --files <path/to/script.py>
```

* The configuration file is [`.pre-commit-config.yaml`](.pre-commit-config.yaml).