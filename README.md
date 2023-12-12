# Mini-IPD

This Repository allows you to start a Mini-Internet, generate Traffic and apply the Ingress Point Detection Algorithm, which we call Mini-IPD. In the following, we explain how you can setup the Mini-IPD on your machine.

## 1. TODOs

- [x] test single modules using relative paths
    - [x] garbage collector
    - [x] netflow collector
    - [x] traffic generator
    - [x] IPD
- [x] Instructions for general usage
- [ ] Finaler Test @Stefan :-)

Optional:
- [ ] update Mini-Internet configuration to announce and assign more different prefixes? (`configure.py`)
    - [ ] `generate_scapy_configs.py l.167` & `configure_balancing.py l.106` change somethinge here to generate more specific/variable prefixes to generate from -> What is the impact on the balancing/traffic flow?

## 2. Requirements

- Docker (+ rights to execute it)
- Miniconda (will be installed when running executing the Mini-IPD setup if not already installed)

**TBA**

## 3. Installation & First Startup

1. Clone this [Repository](https://git.informatik.tu-cottbus.de/bergmmax/mini-ipd.git)
2. Setup your Repository: `$ bash ./setup_repo.sh`
    - Installs [Miniconda](https://docs.conda.io/projects/miniconda/en/latest/index.html#) if you have not installed it yet
        - **if installed**:
            - if **env installed** call script like: `$ bash ./setup_repo.sh path/to/miniconda/installation 1`
            - if **env not installed** call script like: `$ bash ./setup_repo.sh path/to/miniconda/installation 0`
    - Creates a conda environment including required packages (`mini-ipd`)
    - git submodule setup (Mini-Internet and IPD)
    - Startup basic Mini-IPD (`$ bash ./start_mini_ipd_example.sh path/to/miniconda/installation`)
        - Startup a Mini-Internet with 5 ASes
        - Configure Mini-Internet for IPD usage
        - Start Traffic Generator to get a first 24-Hour Trace within 2 hours

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