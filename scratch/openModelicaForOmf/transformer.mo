model SimpleTransformerPinney "Transformer circuit to show the magnetization facilities"
  constant Modelica.SIunits.Angle pi = Modelica.Constants.pi;
  parameter Modelica.SIunits.Voltage Vdc = 0.1 "DC offset of voltage source";
  parameter Modelica.SIunits.Voltage Vpeak = 0.1 "Peak voltage of voltage source";
  parameter Modelica.SIunits.Frequency f = 10 "Frequency of voltage source";
  parameter Modelica.SIunits.Angle phi0 = pi / 2 "Phase of voltage source";
  parameter Real n = 2 "Turns ratio primary:secondary voltage";
  parameter Modelica.SIunits.Resistance R1 = 0.01 "Primary resistance w.r.t. primary side";
  parameter Modelica.SIunits.Inductance L1sigma = 0.05 / (2 * pi * f) "Primary leakage inductance w.r.t. primary side";
  parameter Modelica.SIunits.Inductance Lm1 = 10.0 / (2 * pi * f) "Magnetizing inductance w.r.t. primary side";
  parameter Modelica.SIunits.Inductance L2sigma = 0.05 / (2 * pi * f) / n ^ 2 "Secondary leakage inductance w.r.t. secondary side";
  parameter Modelica.SIunits.Resistance R2 = 0.01 / n ^ 2 "Secondary resistance w.r.t. secondary side";
  parameter Modelica.SIunits.Resistance RL = 1 / n ^ 2 "Load resistance";
  final parameter Modelica.SIunits.Inductance L1 = L1sigma + M * n "Primary no-load inductance";
  final parameter Modelica.SIunits.Inductance L2 = L2sigma + M / n "Secondary no-load inductance";
  final parameter Modelica.SIunits.Inductance M = Lm1 / n "Mutual inductance";
  output Modelica.SIunits.Voltage v1B = resistor11.n.v "Primary voltage, basic transformer";
  output Modelica.SIunits.Current i1B = resistor11.i "Primary current, basic transformer";
  output Modelica.SIunits.Voltage v2B = resistor12.p.v "Secondary voltage, basic transformer";
  output Modelica.SIunits.Current i2B = resistor12.i "Secondary current, basic transformer";
  Modelica.Electrical.Analog.Basic.Transformer basicTransformer(L1 = L1, L2 = L2, M = M) annotation(Placement(visible = true, transformation(origin = {-2.54237,10.5327}, extent = {{-10,-10},{10,10}}, rotation = 0)));
  Modelica.Electrical.Analog.Sources.SineVoltage sineVoltage1(V = Vpeak, phase = phi0, freqHz = f, offset = Vdc) annotation(Placement(visible = true, transformation(origin = {-81.937,6.94915}, extent = {{-10,-10},{10,10}}, rotation = 270)));
  Modelica.Electrical.Analog.Basic.Ground ground11 annotation(Placement(visible = true, transformation(origin = {-81.2107,-27.6514}, extent = {{-10,-10},{10,10}}, rotation = 0)));
  Modelica.Electrical.Analog.Basic.Resistor resistor11(R = R1) annotation(Placement(visible = true, transformation(origin = {-71.6949,38.6925}, extent = {{-10,-10},{10,10}}, rotation = 0)));
  Modelica.Electrical.Analog.Basic.Resistor load1(R = RL) annotation(Placement(visible = true, transformation(origin = {80.8475,12.7603}, extent = {{-10,-10},{10,10}}, rotation = 270)));
  Modelica.Electrical.Analog.Basic.Resistor resistor12(R = R2) annotation(Placement(visible = true, transformation(origin = {70.9685,37.4818}, extent = {{-10,-10},{10,10}}, rotation = 0)));
  Modelica.Electrical.Analog.Basic.Ground ground12 annotation(Placement(visible = true, transformation(origin = {81.3317,-27.5303}, extent = {{-10,-10},{10,10}}, rotation = 0)));
initial equation
  basicTransformer.i1 = 0;
  basicTransformer.i2 = 0;
equation
  connect(load1.n,ground12.p) annotation(Line(points = {{80.8475,2.76029},{81.3317,-17.5303}}, color = {0,0,255}));
  connect(basicTransformer.n2,ground12.p) annotation(Line(points = {{7.45763,5.5327},{10,-17.5303},{81.3317,-17.5303}}, color = {0,0,255}));
  connect(resistor12.n,load1.p) annotation(Line(points = {{80.9685,37.4818},{80.8475,22.7603}}, color = {0,0,255}));
  connect(basicTransformer.p2,resistor12.p) annotation(Line(points = {{7.45763,15.5327},{10,37.4818},{60.9685,37.4818}}, color = {0,0,255}));
  connect(sineVoltage1.p,resistor11.p) annotation(Line(points = {{-81.937,16.9492},{-81.6949,38.6925}}, color = {0,0,255}));
  connect(basicTransformer.p1,resistor11.n) annotation(Line(points = {{-12.5424,15.5327},{-10,38.6925},{-61.6949,38.6925}}, color = {0,0,255}));
  connect(sineVoltage1.n,ground11.p) annotation(Line(points = {{-81.937,-3.05085},{-81.2107,-17.6514}}, color = {0,0,255}));
  connect(ground11.p,basicTransformer.n1) annotation(Line(points = {{-81.2107,-17.6514},{-10,-17.6514},{-12.5424,5.5327}}, color = {0,0,255}));
  annotation(experiment(StopTime = 50, Interval = 0.001), Documentation(revisions = "<html>
<dl>
<dt><i>2014</i></dt>
<dd>by David Pinney based on Anton Haumer's work</dd>
</dl>
</html>", info = "<html>
<p>A simple transformer to get our feet wet.</p>
</html>"), Diagram(coordinateSystem(extent = {{-100,-50},{100,50}}, preserveAspectRatio = false, initialScale = 0.1, grid = {2,2}), graphics = {Text(origin = {3.75299,-42.8571}, lineColor = {0,0,255}, extent = {{-60,20},{60,0}}, textString = "Basic.Transformer (mutual inductance)")}));
end SimpleTransformerPinney;

