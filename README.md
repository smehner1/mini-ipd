# Mini-IPD

Welcome to the Mini-IPD project. This project enables you to experiment with the Ingress Point Detection algorithm in an ISP scenario that is emulated in the [mini Internet](https://github.com/nsg-ethz/mini_internet_project) environment.

The code in this repository enables you to start a Mini-Internet, generate traffic, and apply the Ingress Point Detection algorithm, which we call Mini-IPD. In the following, we explain how you can setup the Mini-IPD on your server.

Note: The prototypic version of our Ingress Point Detection algorithm that is used by Mini-IPD is available as [seperate repository](https://github.com/smehner1/ipd) and used in this repo as sub module. If you are only interested in the pure IPD implementation, please refer to to the [IPD algorithm](https://github.com/smehner1/ipd) repository instead.

For the details of our Ingress Point Detection Algorithm, please refer to our [SIGCOMM'24 paper](https://www.ohohlfeld.com/paper/ipd-paper-sigcomm24.pdf).

If you use this project in an academic context, please cite our SIGCOMM'24 paper:
```
@inproceedings{IPD,
    title = {{IPD: Detecting Traffic Ingress Points at ISPs}},
    author = {Stefan Mehner and Helge Reelfs and Ingmar Poese and Oliver Hohlfeld},
    booktitle = {ACM SIGCOMM},
    year = 2024
}
```

## Contacts
Stefan Mehner <uk101435 [at] uni-kassel . de> \
Oliver Hohlfeld <oliver . hohlfeld [at] uni-kassel . de> \
[Distributed Systems Group at University of Kassel](https://www.vs.uni-kassel.de)

## 2. Requirements

To run Mini-IPD with the provided ISP scenario, we assume that you have a server available with about 100 GB of available memory and enough CPU cores.

- `docker` (+ rights to execute it) (See e.g., [this page](https://docs.docker.com/engine/install/ubuntu/) on how to install Docker on Ubuntu)
- `miniconda` (will be installed when running executing the Mini-IPD setup if not already installed)
- `screen` - if not available, install with `sudo apt-get install screen` on Ubuntu systems
- Mini Internet requirements: since we use the Mini Internet, make sure that you have satisfied all the requirements that the original mini internet project has set. To do so, [follow the steps on this page](https://github.com/nsg-ethz/mini_internet_project/wiki/prerequisite). This includes to install `openvswitch-switch`.

## 3. Installation & First Startup

1. Clone this repository with all submodules: `git clone --recurse-submodules https://github.com/smehner1/mini-ipd.git`
2. Check if the basic requirements are met by running `bash requirements.sh` [Note: this assumes that you are using Ubuntu or Debian].
3. Setup your Repository: `$ bash ./setup_repo.sh`
    - Installs [Miniconda](https://docs.conda.io/projects/miniconda/en/latest/index.html#) if you have not installed it yet
    - Creates a conda environment including required packages (`mini-ipd`)
    - Startup basic Mini-IPD (`$ bash ./start_mini_ipd_example.sh path/to/miniconda/installation`)
        - Startup a Mini-Internet with 5 ASes
        - Configure Mini-Internet for IPD usage
        - Start Traffic Generator to get a first 24-hour trace within 2 hours

## 4. Further Usage Instructions

### 4.1 Configure Your Mini-Internet

- **Start Mini-Internet** with given configuration with `start_mini_internet.sh <path-to-miniconda>`

- Increase the number of ASes by running `scalability/create_mini_internet_configs.py <value>` where the value is the number of ASes you want
    - The ASes will be incrementally placed arround the center AS and configured equally
    - This will only write the configurations $\rightarrow$ you need to restart your Mini-Internet after it

- If you want to build your very own Mini-Internet configure it within the `mini-internet` directory
    - For further information read configuration instructions at [Mini-Internet](https://github.com/nsg-ethz/mini_internet_project/wiki)
    - Please note that the Mini-Internet is still evelopying and the wiki can change over time
    - Please note that we do not guarantee functionality of our tools when changing the basic structure of our Mini-Internet

### 4.2 Generate Flow Configuration For Your Case

- To generate scapy flows run the `traffic_generator/generate_scapy_configs.py`
- For specific use cases see the following $\downarrow$

#### 4.2.1 Static Flow Generation

- Run the configuration script with flag `--static`
- Define what portion of flows is generated from what AS in `traffic_generator/configs/as_traffic_distro.csv`

#### 4.2.2 24-Hour Flow Generation (Diurnal Pattern)

- When not using the `--static` flag traffic for 24 iterations will be generated
- Each iteration has a given portion of flows $\rightarrow$ diurnal pattern
- Define what portion of flows is generated from what AS in `traffic_generator/configs/as_traffic_distro.csv`

#### 4.2.2.1 Offloading in Diurnal Pattern **TBD**

- To add an offloading event run **TBA**
- You need to give:
    - *Prefix* to offload
    - *Iteration* of offloading
    - The AS the flow originally originated
    - The AS the flows are offloaded to
- This will apply the canges directly in your configurations from th diurnal pattern

#### 4.2.2.2 Hypergiants in Diurnal Pattern

- To increase portion of flows from a given prefix for a given iteration use the `traffic_generator/configs/hypergiants.csv`
- Add for each increase:
    - *Network* within the number of flows shall be increased
    - *Prefix* from which the flows are generated
    - *Ratio* of increase
    - *Iteration* to increase the flows

#### 4.2.3 Increase Variability In Generation *TBD*

- By adding more ASes to your Mini-IPD automatically more prefixes will be added
    - Note, that this will add more `/8` prefixes
- To add more different prefixes **TBD**

### 4.3 Start Netflow Collector

- Start Netflow Collector by executing `netflow_collector/netflow_collector.py -conda <your_conda_env>`
- If necessary specify ipd-implementation directory (`-ipd <path>`), the netflow directory (`-nf <path>`)
- Define how many minutes to wait before collecting netflow by using `-offset <value>`
- Define interval of collection using `-i <value>`

- If you use the Netflow Collector to directly pipe the Netflow into the IPD do not use the verbose flag `-v`

- *Optionally connect Netflow after execution to have your Netflow within one file for later usage (`ipd_implementation/tools/connect_netflow.py`)*


### 4.4 Start Traffic Generator

**!!! Starting the traffic generator does not start the Netflow Collector, so you need to start it in parallel !!!**

- You have 2 ways to generate traffic:
    - Static generation with continuously sending the same packages (set flag `--static`)
        - Needs manual stopping
    - 24-hour trace generation
        - Writes a log file into `time_yyyy_mm_dd_hh_mm.log` within the traffic generator directory that enables full tracking when what iteration started for later analyzes

#### 4.4.1 Static Generation

- Needs configured Mini-Internet
- Needs configured flows for a single iteration using `generate_scapy_configs.py` $\rightarrow$ [Static Flow Generation](#421-static-flow-generation)
- Start traffic generator by ` traffic_generator/traffic_generator.py --start --static`
    - You can add noise by using `-n <value>` (with value between 0 and 1)
    - If necessary adapt pathes to Mini-Internet using `--dir <path>`
- Stop traffic generator by ` traffic_generator/traffic_generator.py --kill`

- *Optionally connect Netflow after execution to have your Netflow within one file for later usage*

#### 4.4.2 24-Hour generation

- Needs configured Mini-Internet
- **Does not need configured flows $\rightarrow$ can be configured using the traffic controller**
    - Configure them manually as shown in [Generate Flow Configuration For Your Case](#42-generate-flow-configuration-for-your-case)
- Start day traffic with
    - Flow generation `-g`
    - Noise `-n <value>` (value between 0 and 1)
    - Warp factor `-w <value>` (value represents seconds that each iteration will last)
    - Given overall flows number `-f <value>`
    - For definition of overflow and hypergiants see [Generate Flow Configuration For Your Case](#42-generate-flow-configuration-for-your-case)
- After 24 iterations the traffic generator will automatically stop all traffic
    - Setting Flag `--killcollector` also stops a running netflow collector and the Netflow is also directly connected (`ipd-implementation/tools/connect_netflow.py`)

### 4.5 Apply IPD

`ipd-implementation/start_algo_{offline,online}.sh`

- Pipe one of your Netflow Traces into the IPD
- In best case you used the `connect_netflow.py` to get one big file for easier usage
- The generated Netflow is placed within `ipd-implementation/netflow` directory

- When running in **online modus** (Mini-IPD is running and we can pipe directly from the Netflow-Collector into the IPD) you only need to give path to your Miniconda directory using `-m <path/to/conda>`
    - the IPD and Netflow Collector will run as long as you want
    - stop the full process by pressing `ctrl+C`, which will stop and connect your collected Netflow
- When running in **offline modus** (Netflow Trace already exists) you additionally need to give the path to `.csv.gz` file using `-f <path/to/csv.gz>`

- Change the parameters within those files to impact the IPD results
