class Project():
    pass

class ProjectObject():
    name = ""
    project = Project()
    def __unicode__(self):
        return self.name

class Group(ProjectObject):
    pass

class PowerFlowObject(ProjectObject):
    phases = ""
    nominal_voltage = 0.0

class Node(PowerFlowObject):
    BUS_CHOICES = (
        (u'Q', u'PQ - uncontrolled'),
        (u'V', u'PV - constrainted voltage controlled'),
        (u'S', u'Swing - unconstrained voltage controlled'),
    )
    bustype = ""
    voltage_A_real = 0.0
    voltage_A_imaginary = 0.0
    voltage_B_real = 0.0
    voltage_B_imaginary = 0.0
    voltage_C_real = 0.0
    voltage_C_imaginary = 0.0

class NodeLink(PowerFlowObject):
    from_node = Node()
    to_node = Node()

class ConnectedPowerFlowObject(PowerFlowObject):
    phases_connected = ""
    parent = Node()
    # todo: add logic to ensure that phases_connected is subset of phases

class OverheadLineConductor(PowerFlowObject):
    geometric_mean_radius = 0.0
    resistance = 0.0
    cable_diameter = 0.0

class UndergroundLineConductor(OverheadLineConductor):
    neutral_geometric_mean_radius = 0.0
    neutral_diameter = 0.0
    neutral_resistance = 0.0
    neutral_strands = 0
    insulation_permittivity = 0.0
    shield_geometric_mean_radius = 0.0
    sheild_resistance = 0.0

class Capacitor(ConnectedPowerFlowObject):
    CONTROL_CHOICES = (
        (u'MA', u'Manual'),
        (u'VA', u'VAR'),
        (u'VO', u'Volt'),
        (u'VV', u'VARVolt'),
        (u'CU', u'Current'),
    )   
    SWITCH_CHOICES = (
        (u'O', u'Open'),
        (u'C', u'Closed'),
    )
    CONTROL_LEVEL_CHOICES = (
        (u'B', u'Bank'),
        (u'I', u'Individual'),
    )
    UNIT_CHOICES = (
        (u'k', u'kVAr'),
        (u'M', u'MVAr'),
    )
    control = ""
    control_level = ""
    switch_A = ""
    switch_B = ""
    switch_C = ""
    pt_phase = ""
    voltage_set_high = 0.0
    voltage_set_low = 0.0
    capacitor_A_unit = ""
    capacitor_A_value = 0.0
    capacitor_B_unit = ""
    capacitor_B_value = 0.0
    capacitor_C_unit = ""
    capacitor_C_value = 0.0
    time_delay = 0.0
    dwell_time = 0.0

class Configuration(ProjectObject):
    pass

class LineSpacing(Configuration):
    distance_AC = 0.0
    distance_AB = 0.0
    distance_BC = 0.0
    distance_AN = 0.0
    distance_CN = 0.0
    distance_BN = 0.0

class LineConfiguration(Configuration):
    conductor_A = []
    conductor_B = []
    conductor_C = []
    conductor_N = []
    spacing = []

class TransformerConfiguration(Configuration):
    CONNECT_CHOICES = (
        (u'WW', u'WYE_WYE'),
        (u'DD', u'DELTA_DELTA'),
        (u'DG', u'DELTA_GWYE'),
        (u'SP', u'SINGLE_PHASE'),
        (u'CT', u'SINGLE_PHASE_CENTER_TAPPED'),
    )
    INSTALL_CHOICES = (
        (u'PT', u'Pole Top'),
        (u'PM', u'Pad Mount'),
        (u'VA', u'Vault'),
    )
    UNIT_CHOICES = (
        (u'k', u'kVA'),
        (u'M', u'MVA'),
    )
    connect_type = ""
    install_type = ""
    power_rating_unit = ""
    power_rating = 0.0
    primary_voltage = 0.0
    secondary_voltage = 0.0
    resistance = 0.0

class RegulatorConfiguration(Configuration):
    CONNECT_CHOICES = (
        (u'WW', u'WYE_WYE'),
        (u'D1', u'OPEN_DELTA_ABBC'),
        (u'D2', u'OPEN_DELTA_BCAC'),
        (u'D3', u'OPEN_DELTA_CABA'),
        (u'CD', u'CLOSED_DELTA'),
        (u'CD', u'CONNECT_TYPE_MAX'),
    )
    CONTROL_CHOICES = (
        (u'MA', u'MANUAL'),
        (u'OV', u'OUTPUT_VOLTAGE'),
        (u'RN', u'REMOTE_NODE'),
        (u'LD', u'LINE_DROP_COMP'),
    )
    TYPE_CHOICES = (
        (u'A', u'A'),
        (u'B', u'B'),
    )
    connect_type = ""
    band_center = 0.0
    band_width = 0.0
    time_delay = 0.0
    raise_taps = 0
    lower_taps = 0
    current_transducer_ratio = 0.0
    power_transducer_ratio = 0.0
    compensator_r_setting_A = 0.0
    compensator_r_setting_B = 0.0
    compensator_r_setting_C = 0.0
    compensator_x_setting_A = 0.0
    compensator_x_setting_B = 0.0
    compensator_x_setting_C = 0.0
    ct_phase = ""
    pt_phase = ""
    regulation = 0.0
    control_type = ""
    type_type = ""
    tap_pos_A = 0
    tap_pos_B = 0
    tap_pos_C = 0

class Regulator(NodeLink):
    sense_node = Node()
    configuration = RegulatorConfiguration()

class RegulatorVoltVar(ProjectObject):
    regulator = Regulator()
    low_load_deadband = 0.0
    high_load_deadband = 0.0
    max_voltage_drop = 0.0
    desired_voltage = 0.0

class VoltVarControl(ConnectedPowerFlowObject):  # derived from c++ code, volt_var_control.cpp
    CONTROL_CHOICES = (
        (u'A', u'Active'),
        (u'S', u'Standby'),
    )
    control_method = ""
    capacitor_delay = 0.0
    regulator_delay = 0.0
    desired_pf = 0.0
    d_max = 0.0
    d_min = 0.0
    substation_link = Regulator()
    regulator_list = []
    capacitor_list = []
    voltage_measurement_PowerFlowObjects = []

class TriplexLineConductor(ProjectObject):
    resistance = 0.0
    geometric_mean_radius = 0.0

class LineConfiguration(Configuration):
    conductor_1 = TriplexLineConductor()
    conductor_2 = TriplexLineConductor()
    conductor_N = TriplexLineConductor()
    line_spacing = LineSpacing()

class TriplexLineConfiguration(LineConfiguration):
    insulation_thickness = 0.0
    diameter = 0.0
    reactance = 0.0

class Transformer(NodeLink):
    configuration = TransformerConfiguration()
    group = Group()

class TriplexMeter(PowerFlowObject):
    group = Group()

class TriplexLine(NodeLink):
    length = 0.0
    configuration = LineConfiguration()
    group = Group()

class ZipLoad(ProjectObject):
    base_power = ""
    schedule_skew = 0.0
    heatgain_fraction = 0.0
    power_pf = 0.0
    current_pf = 0.0
    impedance_pf = 0.0
    impedance_fraction = 0.0
    current_fraction = 0.0
    power_fraction = 0.0

class WaterHeater(ProjectObject):
    UNIT_CHOICES = (
        (u'k', u'kW'),
        (u'M', u'MW'),
    )
    LOCATION_CHOICES = (
        (u'IN', u'Inside'),
        (u'GA', u'Garage'),
    )
    schedule_skew = 0.0
    tank_volume = 0.0
    heating_element_capacity_unit = ""
    heating_element_capacity = 0.0
    tank_setpoint = 0.0
    temperature = 0.0
    thermostat_deadband = 0.0
    location = ""
    tank_UA = 0.0
    demand = ""

class House(ProjectObject):
    HEATING_CHOICES = (
        (u'GA', u'Gas'),
        (u'HE', u'Heat Pump'),
        (u'RE', u'Resistance'),
        (u'OT', u'Other'),
        (u'UN', u'Unknown'),
        (u'NO', u'None'),
    )
    COOLING_CHOICES = (
        (u'NO', u'None'),
        (u'EL', u'Electric'),
        (u'OT', u'Other'),
    )
    THERMAL_INTEGRITY_CHOICES = (
        (u'L1', u'Very Little'),
        (u'L2', u'Little'),
        (u'L3', u'Below Normal'),
        (u'N1', u'Normal'),
        (u'H1', u'Above Normal'),
        (u'H2', u'Good'),
        (u'H3', u'Very Good'),
        (u'UK', u'Unknown'),
    )
    parent = TriplexMeter()
    floor_area = 0.0
    schedule_skew = 0.0
    heating_system_type = ""
    cooling_system_type = ""
    cooling_setpoint = ""
    heating_setpoint = ""
    thermal_integrity_level = ""
    air_temperature = 0.0
    mass_temperature = 0.0
    cooling_COP = 0.0
    zip_load = ZipLoad()
    water_heater = WaterHeater()

class Recorder(ProjectObject):
    interval = 0
    parent = ProjectObject()
    file_name = ""
    limit = 0
    property_list = ""