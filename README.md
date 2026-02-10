\# PLUM-based Decentralised Earthquake Early Warning System Simulation



A discrete event simulation (DES) of a decentralised Earthquake Early Warning (EEW) system inspired by the PLUM algorithm, implemented using Python and SimPy.



\## Overview



This simulation models a network of MEMS-based seismic sensors that collaboratively detect and confirm earthquake events without a central processing unit. Sensors communicate peer-to-peer and autonomously transition through operational states based on local observations and neighbour confirmations.



\## Key Features



\- \*\*Decentralized Architecture\*\*: No central authority; sensors operate autonomously

\- \*\*Collaborative Confirmation\*\*: Events confirmed through peer-to-peer messaging

\- \*\*State Machine Implementation\*\*: Sensors transition through defined operational states

\- \*\*Batch Processing\*\*: Supports multiple earthquake scenarios from CSV files

\- \*\*Comprehensive Logging\*\*: Detailed event logs for post-analysis



\## Installation



\### Prerequisites



\- Python 3.7+

\- Required packages:



```bash

pip install -r requirements.txt

```



Or install manually:



```bash

pip install simpy pandas numpy pyproj

```



\### Optional Visualization Tools



For generating visualizations (optional):



\*\*Static Frames (\[PyGMT](https://www.pygmt.org/latest/install.html)):\*\*



\- Requires: GMT software installed on your system (\[GMT Installation](https://www.generic-mapping-tools.org/download/))

\- Python package: `pip install pygmt geopandas shapely`



\*\*Animation (\[Manim](https://docs.manim.community/en/stable/installation.html)):\*\*



\- Requires: LaTeX distribution installed (\[LaTeX Installation](https://www.latex-project.org/get/))

\- Python package: `pip install manim`



\## Quick Start



```bash

\# Clone repository

git clone https://github.com/mirzaei-sadjad/decentralised-eews-simulation.git

cd decentralised-eews-simulation



\# Create output directory

mkdir -p outputs



\# Run simulation

python plum\_des\_simulation.py

```



\## Project Structure



```

decentralised-eews-simulation/

├── plum\_des\_simulation.py        # Main simulation code

├── pygmt\_visualization.py        # Static frame generation (optional)

├── plum\_manim\_animation.py       # Animation generation (optional)

├── requirements.txt              # Python dependencies

├── data/

│   ├── sensors.csv               # Sensor network configuration

│   ├── earthquake.csv            # Earthquake scenarios

│   └── nz\_borders\_multipolygon\_2.shp  # Geographic boundaries (for animation)

├── outputs/

│   ├── log\_file.csv             # Simulation results

│   └── pygmt\_figures/           # Generated visualization frames

└── README.md                    # This file

```



\## Input Files



The simulation requires two CSV files in the `./data/` directory:



\### 1. `sensors.csv`



Defines the sensor network configuration.



```csv

id,latitude,longitude

S01,35.6892,51.3890

S02,35.7000,51.4000

S03,35.7100,51.4100

```



\*\*Columns:\*\*



\- `id`: Unique sensor identifier

\- `latitude`: Sensor latitude (decimal degrees)

\- `longitude`: Sensor longitude (decimal degrees)



\### 2. `earthquake.csv`



Defines earthquake scenarios to simulate.



```csv

id,latitude,longitude

EQ001,35.7500,51.4500

EQ002,35.8000,51.5000

```



\*\*Columns:\*\*



\- `id`: Unique earthquake identifier

\- `latitude`: Epicenter latitude (decimal degrees)

\- `longitude`: Epicenter longitude (decimal degrees)



\## Configuration Parameters



Key parameters in `plum\_des\_simulation.py`:



```python

TRANSMISSION\_RANGE\_KM = 30.0      # Sensor communication range (km)

P\_WAVE\_SPEED\_KM\_PER\_S = 6.0       # P-wave velocity (km/s)

transmission\_delay = 0.05          # Network latency (seconds)

waiting\_window = 5.0               # Confirmation timeout (seconds)

```



\## Sensor States



Sensors operate as a state machine with the following states:



| State           | Description                                                                  |

| --------------- | ---------------------------------------------------------------------------- |

| \*\*Observation\*\* | Normal monitoring mode, waiting for seismic activity                         |

| \*\*Detection\*\*   | P-wave detected, waiting for confirmation from neighbors or second detection |

| \*\*Alerted\*\*     | Event confirmed, sensor is in alert state                                    |



\## Message Types



Sensors communicate using the following message types:



|Message Type|Description|When Sent|

|---|---|---|

|\*\*Detection\*\*|P-wave detection notification|When a sensor detects a P-wave|



\*\*Note:\*\* The current implementation focuses on the Detection message type. Confirmed and Update message types are defined in the code structure but not actively used in message passing.



\## Output



\### Simulation Log



Results are saved to `./outputs/log\_file.csv` with the following columns:



| Column      | Description                                                      |

| ----------- | ---------------------------------------------------------------- |

| `time`      | Simulation time (seconds)                                        |

| `sensor\_id` | Sensor identifier                                                |

| `status`    | Current sensor state (Observation/Detection/Alerted)             |

| `action`    | Action performed (Produce/Receive/ChangeStatus/EventCancelation) |

| `event`     | Message type (P\_Wave\_Detection/ConfirmedAlert)                   |

| `sender\_id` | ID of message sender (if applicable)                             |

| `reaction`  | Sensor's reaction to the event                                   |

| `value`     | Peak displacement value (cm)                                     |

| `eq\_id`     | Earthquake scenario ID                                           |



\### Action Types



\- \*\*Produce\*\*: Sensor generates and broadcasts a message

\- \*\*Receive\*\*: Sensor receives a message from a neighbor

\- \*\*ChangeStatus\*\*: Sensor changes operational state

\- \*\*EventCancelation\*\*: Detection timeout, sensor returns to Observation



\## Visualization (Optional)



\### Static Frames



Generate images showing simulation evolution:



```bash

python pygmt\_visualization.py

```



Output: Series of JPEG images in `./outputs/pygmt\_figures/`



\### Animation



Create an animated video:



```bash

manim plum\_manim\_animation.py original\_plum

```



Output: MP4 video file in `./media/videos/`



\*\*Note:\*\* These visualization tools work with later versions of the simulation and may include features not present in the base simulation.



\## Research Applications



This simulation can be used to study:



\- Network topology effects on detection performance

\- Confirmation strategies and optimal waiting windows

\- Communication protocol impact (delays, range limitations)

\- False alarm reduction through collaborative confirmation

\- Warning time analysis

\- System robustness under sensor/network failures



\## Limitations



Current implementation:



\- S-wave detection code is present but disabled

\- Peak displacement values are randomly generated

\- No epicentre localisation implemented

\- Stochastic detection parameters defined but not active

\- Single message type actively used (Detection)



\## References



1\. Prasanna, R., Chandrakumar, C., Nandana, R., Holden, C., Punchihewa, A., Becker, J. S., Jeong, S., Liyanage, N., Ravishan, D., Sampath, R., \& Tan, M. L. (2022). “Saving Precious Seconds”—A Novel Approach to Implementing a Low-Cost Earthquake Early Warning System with Node-Level Detection and Alert Generation. Informatics, 9(1), 25. doi: \[10.3390/informatics9010025](https://doi.org/10.3390/informatics9010025)

&nbsp;	

2\. Yuki Kodera, Yasuyuki Yamada, Kazuyuki Hirano, Koji Tamaribuchi, Shimpei Adachi, Naoki Hayashimoto, Masahiko Morimoto, Masaki Nakamura, Mitsuyuki Hoshiba; The Propagation of Local Undamped Motion (PLUM) Method: A Simple and Robust Seismic Wavefield Estimation Approach for Earthquake Early Warning. \_\_Bulletin of the Seismological Society of America\_\_ 2018;; 108 (2): 983–1003. doi: \[10.1785/0120170085](https://doi.org/10.1785/0120170085)

&nbsp;   

3\. Richard M. Allen, Diego Melgar. 2019. Earthquake Early Warning: Advances, Scientific Challenges, and Societal Needs. \_Annual Review Earth and Planetary Sciences\_. 47:361-388. doi: \[annurev-earth-053018-060457](https://doi.org/10.1146/annurev-earth-053018-060457 "DOI")

&nbsp;	

4\. The Manim Community Developers. (2026). Manim – Mathematical Animation Framework (Version v0.19.2) \[Computer software]. https://www.manim.community/

