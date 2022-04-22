# mobia-project

* The present repository contains all information about data preparation and training for **Mobia Project License Plate Detection**.

* Please, take into account that each model needs a **different virtual environment and kernel**.

* The three root directories refers to the main work flow modules: **prepare dataset, training, and DeepStream deployment**.

* For now, we can find each model in [training](https://github.com/ZosoV/mobia-project/tree/master/training) folder.

## Script formatting

* Activate conda environment.

* Use [pre-commit](pre-commit.com) command.
```
pre-commit run --files <path/to/script.py>
```

* The configuration file is `.pre-commit-config.yaml`.