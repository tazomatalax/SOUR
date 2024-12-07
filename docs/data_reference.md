# Data Reference Guide

## Raw Data from Reactor Database
### Process Parameters
- `DateTime`: Timestamp of measurements
- `LB_MFC_1_SP`: Mass Flow Controller 1 setpoint
- `LB_MFC_1_PV`: Mass Flow Controller 1 process value

### Reactor 1 Measurements
#### Dissolved Oxygen
- `Reactor_1_DO_Value_PPM`: DO concentration in PPM
- `Reactor_1_DO_T_Value`: DO temperature value

#### pH
- `Reactor_1_PH_Value`: pH value
- `Reactor_1_PH_T_Value`: pH temperature value

#### Weights
- `R1_Weight_Bal`: Reactor 1 weight balance
- `R2_Weight_Bal`: Reactor 2 weight balance

#### Pump Settings
- `LB_Perastaltic_P_1`: Peristaltic pump 1 settings
- `R1_Perastaltic_1_Time`: Pump 1 on time
- `R1_Perastaltic_1_Time_off`: Pump 1 off time

#### Operation Parameters
- `Reactor_1_Speed_RPM`: Agitation speed in RPM
- `Reactor_1_Torque_Real`: Real-time torque measurement

## Calculated Metrics
### Feed Detection
- `reactor_weight_change`: Change in reactor weight
- `feed_bottle_weight_change`: Change in feed bottle weight
- `volume`: Calculated feed volume (L)
- `feed_type`: Determined type of feed event





## Feed Event Data
### Event Parameters
- `timestamp`: Time of feed event
- `feed_type`: Type of feed added
- `volume`: Volume of feed added
- `composition`: Dictionary of feed composition

## Configuration Parameters
### Feed Detection Settings
- `weight_threshold`: Minimum weight change to detect feed (default: 0.05 kg)
- `time_window`: Time window for feed detection (default: 60 seconds)
- `noise_filter`: Weight noise filter threshold (default: 0.02 kg)

### Analysis Settings
- `analysis_window`: Default window for analysis (default: 300 seconds)
- `recovery_threshold`: DO recovery threshold (default: 95% of initial value)
