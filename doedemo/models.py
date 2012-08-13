class ProjectObject():
    def __init__(self):
        self.name = ""
    def __unicode__(self):
        return self.name

class Group(ProjectObject):
    pass

class PowerFlowObject(ProjectObject):
    def __init__(self):
        self.phases = ""
        self.nominal_voltage = 0.0

class Node(PowerFlowObject):
    BUS_CHOICES = (
        (u'Q', u'PQ - uncontrolled'),
        (u'V', u'PV - constrainted voltage controlled'),
        (u'S', u'Swing - unconstrained voltage controlled'),
    )
    def __init__(self):
        self.bustype = ""
        self.voltage_A_real = 0.0
        self.voltage_A_imaginary = 0.0
        self.voltage_B_real = 0.0
        self.voltage_B_imaginary = 0.0
        self.voltage_C_real = 0.0
        self.voltage_C_imaginary = 0.0

class NodeLink(PowerFlowObject):
    def __init__(self):
        self.from_node = Node()
        self.to_node = Node()

class ConnectedPowerFlowObject(PowerFlowObject):
    def __init__(self):
        self.phases_connected = ""
        self.parent = Node()
    # todo: add logic to ensure that phases_connected is subset of phases

class OverheadLineConductor(PowerFlowObject):
    def __init__(self):
        self.geometric_mean_radius = 0.0
        self.resistance = 0.0
        self.cable_diameter = 0.0

class UndergroundLineConductor(OverheadLineConductor):
    def __init__(self):
        self.neutral_geometric_mean_radius = 0.0
        self.neutral_diameter = 0.0
        self.neutral_resistance = 0.0
        self.neutral_strands = 0
        self.insulation_permittivity = 0.0
        self.shield_geometric_mean_radius = 0.0
        self.sheild_resistance = 0.0

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
    def __init__(self):
        self.control = ""
        self.control_level = ""
        self.switch_A = ""
        self.switch_B = ""
        self.switch_C = ""
        self.pt_phase = ""
        self.voltage_set_high = 0.0
        self.voltage_set_low = 0.0
        self.capacitor_A_unit = ""
        self.capacitor_A_value = 0.0
        self.capacitor_B_unit = ""
        self.capacitor_B_value = 0.0
        self.capacitor_C_unit = ""
        self.capacitor_C_value = 0.0
        self.time_delay = 0.0
        self.dwell_time = 0.0

class Configuration(ProjectObject):
    pass

class LineSpacing(Configuration):
    def __init__(self):
        self.distance_AC = 0.0
        self.distance_AB = 0.0
        self.distance_BC = 0.0
        self.distance_AN = 0.0
        self.distance_CN = 0.0
        self.distance_BN = 0.0

class LineConfiguration(Configuration):
    def __init__(self):
        self.conductor_A = []
        self.conductor_B = []
        self.conductor_C = []
        self.conductor_N = []
        self.spacing = []

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
    def __init__(self):
        self.connect_type = ""
        self.install_type = ""
        self.power_rating_unit = ""
        self.power_rating = 0.0
        self.primary_voltage = 0.0
        self.secondary_voltage = 0.0
        self.resistance = 0.0

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
    def __init__(self):
        self.connect_type = ""
        self.band_center = 0.0
        self.band_width = 0.0
        self.time_delay = 0.0
        self.raise_taps = 0
        self.lower_taps = 0
        self.current_transducer_ratio = 0.0
        self.power_transducer_ratio = 0.0
        self.compensator_r_setting_A = 0.0
        self.compensator_r_setting_B = 0.0
        self.compensator_r_setting_C = 0.0
        self.compensator_x_setting_A = 0.0
        self.compensator_x_setting_B = 0.0
        self.compensator_x_setting_C = 0.0
        self.ct_phase = ""
        self.pt_phase = ""
        self.regulation = 0.0
        self.control_type = ""
        self.type_type = ""
        self.tap_pos_A = 0
        self.tap_pos_B = 0
        self.tap_pos_C = 0

class Regulator(NodeLink):
    def __init__(self):
        self.sense_node = Node()
        self.configuration = RegulatorConfiguration()

class RegulatorVoltVar(ProjectObject):
    def __init__(self):
        self.regulator = Regulator()
        self.low_load_deadband = 0.0
        self.high_load_deadband = 0.0
        self.max_voltage_drop = 0.0
        self.desired_voltage = 0.0

class VoltVarControl(ConnectedPowerFlowObject):  # derived from c++ code, volt_var_control.cpp
    CONTROL_CHOICES = (
        (u'A', u'Active'),
        (u'S', u'Standby'),
    )
    def __init__(self):
        self.control_method = ""
        self.capacitor_delay = 0.0
        self.regulator_delay = 0.0
        self.desired_pf = 0.0
        self.d_max = 0.0
        self.d_min = 0.0
        self.substation_link = Regulator()
        self.regulator_list = []
        self.capacitor_list = []
        self.voltage_measurement_PowerFlowObjects = []

class TriplexLineConductor(ProjectObject):
    def __init__(self):
        self.resistance = 0.0
        self.geometric_mean_radius = 0.0

class LineConfiguration(Configuration):
    def __init__(self):
        self.conductor_1 = TriplexLineConductor()
        self.conductor_2 = TriplexLineConductor()
        self.conductor_N = TriplexLineConductor()
        self.line_spacing = LineSpacing()

class TriplexLineConfiguration(LineConfiguration):
    def __init__(self):
        self.insulation_thickness = 0.0
        self.diameter = 0.0
        self.reactance = 0.0

class Transformer(NodeLink):
    def __init__(self):
        self.configuration = TransformerConfiguration()
        self.group = Group()

class TriplexMeter(PowerFlowObject):
    def __init__(self):
        self.group = Group()

class TriplexLine(NodeLink):
    def __init__(self):
        self.length = 0.0
        self.configuration = LineConfiguration()
        self.group = Group()

class ZipLoad(ProjectObject):
    def __init__(self):
        self.base_power = ""
        self.schedule_skew = 0.0
        self.heatgain_fraction = 0.0
        self.power_pf = 0.0
        self.current_pf = 0.0
        self.impedance_pf = 0.0
        self.impedance_fraction = 0.0
        self.current_fraction = 0.0
        self.power_fraction = 0.0

class WaterHeater(ProjectObject):
    UNIT_CHOICES = (
        (u'k', u'kW'),
        (u'M', u'MW'),
    )
    LOCATION_CHOICES = (
        (u'IN', u'Inside'),
        (u'GA', u'Garage'),
    )
    def __init__(self):
        self.schedule_skew = 0.0
        self.tank_volume = 0.0
        self.heating_element_capacity_unit = ""
        self.heating_element_capacity = 0.0
        self.tank_setpoint = 0.0
        self.temperature = 0.0
        self.thermostat_deadband = 0.0
        self.location = ""
        self.tank_UA = 0.0
        self.demand = ""

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
    def __init__(self):
        self.parent = TriplexMeter()
        self.floor_area = 0.0
        self.schedule_skew = 0.0
        self.heating_system_type = ""
        self.cooling_system_type = ""
        self.cooling_setpoint = ""
        self.heating_setpoint = ""
        self.thermal_integrity_level = ""
        self.air_temperature = 0.0
        self.mass_temperature = 0.0
        self.cooling_COP = 0.0
        self.zip_load = ZipLoad()
        self.water_heater = WaterHeater()

class Recorder(ProjectObject):
    def __init__(self):
        self.interval = 0
        self.parent = ProjectObject()
        self.file_name = ""
        self.limit = 0
        self.property_list = ""