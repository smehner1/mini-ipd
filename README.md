# Mini-IPD

This Repository allows you to start a Mini-Internet, generate Traffic and apply the Ingress Point Detection Algorithm, which we call Mini-IPD. In the following, we explain how you can setup the Mini-IPD on your machine.

## TODOs

- [ ] test single modules using relative paths
    - [x] garbage collector
    - [x] netflow collector
    - [x] traffic generator
    - [ ] IPD
- [ ] improve pipeline implementation
    - [x] add logging for traffic generation for easier understanding
    - [ ] check metrics calculation for easy application
    - [ ] start only needed nfdcap processes easy achievable?
- [ ] Instructions for general usage

## Requirements

- Docker (+ rights to execute it)
- Miniconda (will be installed when running executing the Mini-IPD setup if not already installed)

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

### Configure Your Mini-Internet

- **TBA**: Scale up our Mini-Internet
- **TBA**: Change overall topology to your very own Mini-Internet

### Generate Flow Configuration For Your Case

- to generate scapy flows run the `traffic_generator/generate_scapy_configs.py`
- for specific use cases see the following $\downarrow$

#### Static Flow Generation

- run the configuration script with flag `--static`
- define what portion of flows is generated from what AS in `traffic_generator/configs/as_traffic_distro.csv`

#### 24-Hour Flow Generation (Diurnal Pattern)

- **TBA**: how to configure 24 hours of flows

#### Offloading in Diurnal Pattern

- **TBA**: how to add overflow

#### Hypergiants in Diurnal Pattern

- **TBA**: how to add hypergiants

#### Increase Variability In Generation

- **TBA**: how to add more variability of source address spaces

### Start Netflow Collector

- start Netflow Collector by executing `netflow_collector/netflow_collector.py -conda <your_conda_env>`
- if necessary specify ipd-implementation directory (`-ipd <path>`), the netflow directory (`-nf <path>`)
- define how many minutes to wait before collecting netflow by using `-offset <value>`
- define interval of collection using `-i <value>`

- if you use the Netflow Collector to directly pipe the Netflow into the IPD do not use the verbose flag `-v`

- *optionally connect Netflow after execution to have your Netflow within one file for later usage (`ipd_implementation/tools/connect_netflow.py`)*


### Start Traffic Generator

**!!! Starting the traffic generator does not start the Netflow Collector, so you need to start it in parallel !!!**

- you have 2 ways to generate traffic:
    - static generation with continuously sending the same packages (set flag `--static`)
        - needs manual stopping
    - 24-hour trace generation
        - writes a log file into `time_yyyy_mm_dd_hh_mm.log` within the traffic generator directory that enables full tracking when what iteration started for later analyzes

#### Static Generation

- needs configured Mini-Internet
- needs configured flows for a single iteration using `generate_scapy_configs.py` $\rightarrow$ [Static Flow Generation](#static-flow-generation)
- start traffic generator by ` traffic_generator/traffic_generator.py --start --static`
    - you can add noise by using `-n <value>` (with value between 0 and 1)
    - if necessary adapt pathes to Mini-Internet using `--dir <path>`
- stop traffic generator by ` traffic_generator/traffic_generator.py --kill`

- *optionally connect Netflow after execution to have your Netflow within one file for later usage*

#### 24-Hour generation

- needs configured Mini-Internet
- **does not need configured flows $\rightarrow$ can be configured using the traffic controller**
    - configure them manually as shown in [Generate Flow Configuration For Your Case](#generate-flow-configuration-for-your-case)
- start day traffic with
    - flow generation `-g`
    - noise `-n <value>` (value between 0 and 1)
    - warp factor `-w <value>` (value represents seconds that each iteration will last)
    - given overall flows number `-f <value>`
    - for definition of overflow and hypergiants see [Generate Flow Configuration For Your Case](#generate-flow-configuration-for-your-case)
- after 24 iterations the traffic generator will automatically stop all traffic
    - setting Flag `--killcollector` also stops a running netflow collector and the Netflow is also directly connected (`ipd-implementation/tools/connect_netflow.py`)

### Apply IPD

**TBA**

### Apply Metrics

**TBA**
