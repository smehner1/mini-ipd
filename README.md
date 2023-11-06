# Mini-IPD

This Repository allows you to start a Mini-Internet, generate Traffic and apply the Ingress Point Detection Algorithm, which we call Mini-IPD. In the following, we explain how you can setup the Mini-IPD on your machine.

## 1. TODOs

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

## 2. Requirements

- Docker (+ rights to execute it)
- Miniconda (will be installed when running executing the Mini-IPD setup if not already installed)

**TBA**

## 3. Installation & First Startup

1. Clone this [Repository](https://git.informatik.tu-cottbus.de/bergmmax/mini-ipd.git)
2. Setup your Repository: `$ bash ./setup_repo.sh`
    - Installs [Miniconda](https://docs.conda.io/projects/miniconda/en/latest/index.html#) if you have not installed it yet
        - if installed call script like: `$ bash ./setup_repo.sh path/to/miniconda/installation`
    - creates a conda environment including required packages (`mini-ipd`)
    - git submodule setup (Mini-Internet and IPD)
    - Startup basic Mini-IPD (`$ bash ./start_mini_ipd_example.sh path/to/miniconda/installation`)
        - startup a Mini-Internet with 5 ASes
        - configure Mini-Internet for IPD usage
        - start Traffic Generator to get a first 24-Hour Trace within 2 hours

## 4. Further Usage Instructions

### 4.1 Configure Your Mini-Internet

- **Start Mini-Internet** with given configuration with `start_mini_internet.sh <path-to-miniconda>`

- Increase the number of ASes by running `scalability/create_mini_internet_configs.py <value>` where the value is the number of ASes you want
    - The ASes will be incrementally placed arround the center AS and configured equally
    - This will only write the configurations $\rightarrow$ you need to restart your Mini-Internet after it

- If you want to build your very own Mini-Internet configure it within the `mini-internet` directory
    - For further information read configuration instructions at [Mini-Internet](https://github.com/nsg-ethz/mini_internet_project/wiki)
    - Please keep in mind that the Mini-Internet is still evelopying and the wiki can change over time
    - Please keep in mind that we do not guarantee functionality of our tools when changing the basic structure of our Mini-Internet

### 4.2 Generate Flow Configuration For Your Case

- to generate scapy flows run the `traffic_generator/generate_scapy_configs.py`
- for specific use cases see the following $\downarrow$

#### 4.2.1 Static Flow Generation

- run the configuration script with flag `--static`
- define what portion of flows is generated from what AS in `traffic_generator/configs/as_traffic_distro.csv`

#### 4.2.2 24-Hour Flow Generation (Diurnal Pattern)

- when not using the `--static` flag traffic for 24 iterations will be generated
- each iteration has a given portion of flows $\rightarrow$ diurnal pattern
- define what portion of flows is generated from what AS in `traffic_generator/configs/as_traffic_distro.csv`

#### 4.2.2.1 Offloading in Diurnal Pattern **TBD**

- to add an offloading event run **TBA**
- you need to give:
    - *prefix* to offload
    - *iteration* of offloading
    - the AS the flow originally originated
    - the AS the flows are offloaded to
- this will apply the canges directly in your configurations from th diurnal pattern

#### 4.2.2.2 Hypergiants in Diurnal Pattern

- to increase portion of flows from a given prefix for a given iteration use the `traffic_generator/configs/hypergiants.csv`
- add for each increase:
    - *network* within the number of flows shall be increased
    - *prefix* from which the flows are generated
    - *ratio* of increase
    - *iteration* to increase the flows

#### 4.2.3 Increase Variability In Generation *TBD*

- **TBA**: how to add more variability of source address spaces

### 4.3 Start Netflow Collector

- start Netflow Collector by executing `netflow_collector/netflow_collector.py -conda <your_conda_env>`
- if necessary specify ipd-implementation directory (`-ipd <path>`), the netflow directory (`-nf <path>`)
- define how many minutes to wait before collecting netflow by using `-offset <value>`
- define interval of collection using `-i <value>`

- if you use the Netflow Collector to directly pipe the Netflow into the IPD do not use the verbose flag `-v`

- *optionally connect Netflow after execution to have your Netflow within one file for later usage (`ipd_implementation/tools/connect_netflow.py`)*


### 4.4 Start Traffic Generator

**!!! Starting the traffic generator does not start the Netflow Collector, so you need to start it in parallel !!!**

- you have 2 ways to generate traffic:
    - static generation with continuously sending the same packages (set flag `--static`)
        - needs manual stopping
    - 24-hour trace generation
        - writes a log file into `time_yyyy_mm_dd_hh_mm.log` within the traffic generator directory that enables full tracking when what iteration started for later analyzes

#### 4.4.1 Static Generation

- needs configured Mini-Internet
- needs configured flows for a single iteration using `generate_scapy_configs.py` $\rightarrow$ Static Flow Generation](#421-static-flow-generation)
- start traffic generator by ` traffic_generator/traffic_generator.py --start --static`
    - you can add noise by using `-n <value>` (with value between 0 and 1)
    - if necessary adapt pathes to Mini-Internet using `--dir <path>`
- stop traffic generator by ` traffic_generator/traffic_generator.py --kill`

- *optionally connect Netflow after execution to have your Netflow within one file for later usage*

#### 4.4.2 24-Hour generation

- needs configured Mini-Internet
- **does not need configured flows $\rightarrow$ can be configured using the traffic controller**
    - configure them manually as shown in [Generate Flow Configuration For Your Case](#42-generate-flow-configuration-for-your-case)
- start day traffic with
    - flow generation `-g`
    - noise `-n <value>` (value between 0 and 1)
    - warp factor `-w <value>` (value represents seconds that each iteration will last)
    - given overall flows number `-f <value>`
    - for definition of overflow and hypergiants see [Generate Flow Configuration For Your Case](#42-generate-flow-configuration-for-your-case)
- after 24 iterations the traffic generator will automatically stop all traffic
    - setting Flag `--killcollector` also stops a running netflow collector and the Netflow is also directly connected (`ipd-implementation/tools/connect_netflow.py`)

### 4.5 Apply IPD *TBD*

**TBA**

### 4.6 Apply Metrics *TBD*

**TBA**
