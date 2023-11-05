# Mini-IPD

This Repository allows you to start a Mini-Internet, generate Traffic and apply the Ingress Point Detection Algorithm, which we call Mini-IPD. In the following, we explain how you can setup the Mini-IPD on your machine.

## TODOs

- [ ] test single modules using relative paths
    - [x] garbage collector!
    - [x] netflow collector
    - [ ] traffic generator
- [ ] improve pipeline implementation
- [ ] Instructions for general usage

## Requirements

- Docker (+ rights to execute it)

**TBA**

## Installation & First Startup

1. Clone this [Repository](https://git.informatik.tu-cottbus.de/bergmmax/mini-ipd.git)
2. Setup your Repository: `$ bash ./setup_repo.sh`
    - Installs [Miniconda](https://docs.conda.io/projects/miniconda/en/latest/index.html#) if you have not installed it yet
        - if installed call script like: `$ bash ./setup_repo.sh path/to/miniconda/installation`
    - creates a conda environment including required packages (`mini-ipd`)
    - git submodule setup (Mini-Internet and IPD)
    - Startup basic Mini-IPD (`$ bash ./start_mini_ipd.sh path/to/miniconda/installation`)
        - startup a Mini-Internet with 5 ASes
        - configure Mini-Internet for IPD usage
        - start Traffic Generator to get a first 24-Hour Trace within 2 hours

## Further Usage Instructions

**TBA**
