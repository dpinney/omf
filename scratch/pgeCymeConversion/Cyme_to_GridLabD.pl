# NOTE:  These scripts are being provided to the open source "as is".  These are scripts developed
#        for certain project applications, and are not designed to be "all encompassing" -- users
#        are expected to make modifications to these scripts to fit their needs and their database
#        requirements.  While some help may be available from the GridLAB-D support team, this is 
#        not a fully supported feature.

#!/usr/bin/perl
# Name: Cyme_to_GridLabD.pl
#
# Description: Convert Cyme Access database to .glm format for GridLABD for a user specified feeder
#  In many cases, this is also applicable to Synergee database formats
#  In all cases, custom modifications will need to be made as databases structure (i.e. naming, locations of devices, etc.) are
#   usually similar within a particular utility, but rarely similar between utilities.  The key is that the output (or print) functions
#   are needed to create a GLM file which is compatible with Matlab scripts available online.  Some form of database sorting will be
#   needed, either as a separate function or as an internal modification, to make it compatible with the current read-in format.
#
# There is a special call to an Excel spreadsheet indicated by YOUR_CABLE_SOURCE.  This is only needed if cable types are not specified
#   in the main database.
#
# Author: Yousu Chen
# PNNL operated by Battelle
# 7/9/2009
# Modified: Jason Fuller
# 11/20/2011

# log:
# 1. initial start 
# 7/9/2009

# 1. Found following Device ID:

# 1 cable
# 2/3 overhead line
# 4 regulator
# 10 recloser
# 12 sectionalizer
# 13 switch
# 14 fuse
# 17 capacitor
# 20 spot load
# 21 distributed load

# 2. Found following load value type:
#LoadValueType = 0 : KW, KVAR
#LoadValueType = 1 : KVA, PF
#LoadValueType = 2 : KW, PF

# 3. converged w/o fuse/sw/reg/cap
# 8/9/2009

# 1. combined three-phase loads
# 8/10/2009

# 1. Found following capacitor control mode:
# 0: Manual
# 1: Time
# 2: kVAR
# 3: Current
# 4: Power Factor
# 5: Reactive Current
# 6: Temperature
# 7: Voltage
# 8/11/2009

# 1. added capacitor object
# 2. added switch object
# 8/12/2009

# 1. added fuse object
# 8/13/2009

# 1. added sectionalizer object
# 2. added regulator object 
# 8/17/2009

# 1. updated underground cable
# 2. using cyme cable object
# 8/19/2009

# 1. Added underground cable hash table based on Kersting's book
# 8/30/2009

# 1. minor changes on printHeader to add solution method
# 2. add one more argument for printUGSecs1 and printUGSecs2 subroutines.
# 3. add solution method option
# 9/15/2009

# 1. added post-fix for devices number for type number 4-17, since identical device number are used in Cyme for different device types.
# the type numbers are:
# 	 4 regulator
#	10 recloser
# 	12 sectionalizer
#	13 switch
# 	14 fuse
# 	17 capacitor

# 1. changed the no-load-loss (NL) anf full-loand-loss (FL) from actual values to percentages. 
# The equations are:
#     impedance: FL + $RXRatio*FL j
#     shunt_imdedance: 1/NL + 1/NL * $RXRatio j 
# FL and NL is in percentage, for exam FL = 1% => FL = 0.01
# 2. added $RXRatio parameter, the current setting is $RXRatio = 4.5
# 10/08/2009

# 1. added var control capacitor
# 2. added printOHSecs1 and printOHSecs2 subroutines, and cleaned code a little bit
# 10/12/2009

# 1. added wye_wye transformer for non-residential load
# 2. removed unique ID
# 10/18/2009

# 1. set status to OPEN for all devices.(removed ActualStatus)
# 2. connected single phase commercial loads with a center tapped transformer and tag them as commercial.
# 3. added no-load-loss and full-load-loss for 30KVA, 45KVA rating transformer.
#	no-load-loss "45.0", 0.00267; full-load-loss "45.0", 0.01451,
# 10/19/2009

# 1. changed configuration/conductor names to be feeder specific.
# 2. reduced the length of configuration names by using the first letter of spacing configuration
# 3. added the number of customers for each split-phase load
# 10/20/2009

# 1. added feedname to the SPCT transformer name to make it feeder specific.
# 2. cleaned code.
# 10/21/2009

# 1. added serial reactance
# 10/23/2009

# 1. changed the order of objects (put configuration before actural objects)
# 11/02/2009

# 1. added normal distribution for triplex cable length (175+/-75 ft)
# 11/04/2009

# 1. removed wye_wye xfmr for commercial/industrial load 
# 2. added overhead_line_configuration and underground_line_configuration for non_residential load. Length = 25 ft.
# 11/05/2009

# 1. changed object names to bigin with a letter, instead of a number
# 03/31/2010

use Win32::ODBC;
use Math::Trig;
use POSIX;
use strict;
#use List::MoreUtils qw(uniq);
use Spreadsheet::ParseExcel;
use Math::Random qw(random_normal);

# print usage information
if ( $#ARGV != 2 ) {
    printUsage();
}
my $sm_flag = 1;  #0 = FBS, 1=NR
my $sm;
if ($sm_flag eq 0 ){
	$sm = "FBS";
} else {	
	$sm = "NR";
}	
# constant
my $pi = atan(1.0) * 4;
my $poletop     = "POLETOP";
my $padmount    = "PADMOUNT";
my $single      = "SINGLE_PHASE_CENTER_TAPPED";  #transformer type
my $three       = "WYE_WYE";   
my $iwarning    = 0;  # flag to turn on warning messege.

# The following transformer impedance is based on 10KVA rating, 
# the impedance will changed based on KVA rating.
my $R_pu_single = 0.015;
my $R_pu_three  = 0.01;
my $X_pu_single = 0.01;
my $X_pu_three  = 0.05;
my $mean_replacement_time = 2;
my $length      = 1;
my $meter2ft    = 3.2808399;
my $flag_current = 0;
my $flag_kvar = 0;
my $flag_pf = 0;
my $flag_reactive = 0;
my $flag_temp = 0;
my $flag_time = 0;
my $flag_voltage = 0;
my $ic = 0; # counter
my $RXRatio = 4.5;  #R/X ratio for transformer
my $mean = 45; # mean length for triplex cable
my $sdev = 15;  # standard deviation for triplex cable
my $xfmr_length = 25; # length used to connect non_residential loads

# DEFINE HASH TABLES
# 1. phase
my %convertPhase = (1, "AN", 2, "BN", 3, "CN", 4, "ABN", 5, "ACN", 6,"BCN", 7,"ABCN");
my %RegconvertPhase = (1, "A", 2, "B", 3, "C", 4, "AB", 5, "AC", 6,"BC", 7,"ABC");
# 2. xfmr no load loss
my %NL = ("10.0", 0.0038, "15.0", 0.0032, "25.0", 0.00244, "30.0", 0.00253, "37.5", 0.00267, "45.0", 0.00267, "50.0", 0.00268, "75.0", 0.00229);
# 3. xfmr full load loss
my %FL = ("10.0", 0.0261, "15.0", 0.0216, "25.0", 0.01924, "30.0", 0.01773, "37.5", 0.01547, "45.0", 0.01451, "50.0", 0.01354, "75.0", 0.01557);
# 4. underground cable hash table

my $default_nl = 0.003; #default no load loss
my $default_fl = 0.015; #default full load loss
my $sum_DL_KW = 0;
my $sum_DL_KVAR = 0;
my $sum_spot_KW = 0;
my $sum_spot_KVAR = 0;
my $triplex_length;
#0 -- file names
my $dbDevFile = $ARGV[0];    
my $dbModFile = $ARGV[1];   
my $feederName   = $ARGV[2];     
my $glmFile = $ARGV[2].".glm";

#1 -- equipment source
my (%NominalVLL, %DisiredVLL) = ();

#2 -- conductor
my (%condR25, %condGMR, %condRating) = ();
my (%LineIDP, %LineIDN, %LineIDSpacing) = ();

#3 -- cable
my (@cables, @UGcables,@UGLineCFGs);
my (%cableRating, %cablePR, %cableZR, %cablePX, %cableZX, %cablePB, %cableZB) = ();
my (%UGOD,%UGRating,%UGCGMR,%UGCR,%UGCD,%UGNGMR,%UGNR,%UGND,%UGStrands,%UGDAB,%UGDAC,%UGDBC)=();
my (%UGCFG) =();

#4 -- network
my @networkIDs;

#5 -- node
my @nodes;
my (%nodeX, %nodeY, %nodeNetworkID) =();
my %hashNodePhase = ();

#6 -- overhead line
my (@OHSecs, @OHConds, @UniqueOHConds);
my (%OHA, %OHB, %OHC, %OHN, %OHSpacing, %OHLength, %OHCFG) = ();

#7 -- underground line
my @UGSecs;
my (%UGCable, %UGLength) = ();

#8 -- section
my (@secs, @LineCFGs, @UniqueLineCFGs, @UniqueUGLineCFGs,@LineSpacings,@UniqueLineSpacings, @To);
my (%secFrom, %secTo, %secPhase) = ();

#9 -- custom load
my (%loadType, %loadCustomerNum, %loadClass, %loadPhase, %loadnoCust) = ();
my ($loadValueType,$loadV1, $loadV2);
my (@residential, @tn1,@loads,@spotloads,@uniquespotloads);
my (@non_residential, @unique_non_residential);
my (%non_residential_phase, %non_residential_KVA1, %non_residential_KW1, %non_residential_KVAR1);
my (%non_residential_KVA2, %non_residential_KW2, %non_residential_KVAR2,%non_residential_KVA3, %non_residential_KW3,%non_residential_KVAR3);
my (%residential_phase, %tn1_phase);
my (@SPCTCFG, @UniqueSPCTCFG, @WYEWYECFG,@uniqueWYEWYECFG);
my (%loadKVA,%loadKW,%loadKVAR,%SPCTID,%tn_cfg) = ();
my (%spotload,%spotloadKW1,%spotloadKW2,%spotloadKW3,) = ();
my (%spotloadKVAR1,%spotloadKVAR2,%spotloadKVAR3,%spotloadPhase) = ();
my (%spotloadKVA1,%spotloadKVA2,%spotloadKVA3,%spotloadKVA) = ();
my %loadphase = ();

#10 -- source
my $source;
my %sourceEqID = ();

#11 -- device
my @deviceNums;
my (%DevType, %DevSection, %DevLoc, %sectionDev ) = ();
my (@fusesec, @swsec, @recsec, @sectionalizersec, @regsec);
# devloc = 0: n/a
# devloc = 1: at from node
# devloc = 2: at to node

#12 -- shuntcapacitor
my @shuntcaps;
my (%capEquID, %capST, %capPhase, %capCFG, %capA, %capB, %capC, %capVLN, %capType) = ();

#13 -- equipment capacitor
my (%capEquRatedKVAR, %capEquRatedKVLL);	   

#14 -- capacitorcontrol_current CYMCAPACITORCONTROL_KVAR
my (%capcurrentOn,%capcurrentOff,%capcurrentPhase) = ();
my (%capvarOn,%capvarOff,%capvarPhase) = ();

#15 -- switch
my (%swEquID, %swPhase, %swST, %swTCC, %swFeedingNodeID ) = (); 

#16 -- recloser
my (%recEquID, %recPhase, %recST, %recTCC, %recFeedingNodeID ) = (); 

#17 -- fuse
my (%fuseEquID, %fusePhase, %fuseST, %fuseTCC, %fuseFeedingNodeID ) = (); 

#18 -- equipment fuse
my (%fuseEquRatedI1,%fuseEquRatedI2, %fuseEquRatedV, %fuseEquReversible,%fuseEquSinglPhaseLocking );	   

#19 -- sectionalizer
my (%sectionalizerEquID, %sectionalizerPhase, %sectionalizerST, %sectionalizerTCC, %sectionalizerFeedingNodeID) = (); 

#20 -- regulator
my (%regEquID, %regPhase, %regCFG, %regCT, %regPT, %regBW, %regBoost, %regBuck,%regSetting, %regTapA,
    %regTapB,%regTapC,%regCtrST, %regNormalFeedingNodeId, %hashRegCFG ) = (); 

#21 -- equipment regulator
my (%regEquRatedKVA1,%regEquRatedKVA2, %regEquRatedKVLN, %regEquMaxBoost, %regEquMaxBuck, %regEquBW, %regEquCT, %regEquPT, %regEquTaps );	   

#22 -- series reactance
my (%SXEquID, %SXPhase, %SXX, %SXEquRatedI1, %SXEquRatedI2 ) = (); 
my @SXSec;
	
open( GLM_FILE, ">$glmFile" ) or die "Error: Cannot open file $glmFile";

# read underground cable information from YOUR_CABLE_SOURCE
#printUsage() unless @ARGV;
my $input_cable = "YOUR_CABLE_SOURCE.xls";
my $oExcel = new Spreadsheet::ParseExcel;
my $oBook = $oExcel->Parse($input_cable);

print "Your YOUR_CABLE_SOURCE underground cable spreatsheet is:", $oBook->{File} , "\n" if ($iwarning eq 1);

# Read cable data
my $sheet_bus = $oBook->{Worksheet}[0];
my $n_row = $sheet_bus->{MaxRow};

foreach my $i(3..$n_row) {
	my $eqID = $sheet_bus->{Cells}[$i][0]->Value;
	my $rating = $sheet_bus->{Cells}[$i][1]->Value;
	my $OD = $sheet_bus->{Cells}[$i][19]->Value;
	my $DAB = $sheet_bus->{Cells}[$i][16]->Value;
	my $DAC = $sheet_bus->{Cells}[$i][17]->Value;
	my $DBC = $sheet_bus->{Cells}[$i][18]->Value;
	my $CGMR = $sheet_bus->{Cells}[$i][12]->Value;
	my $CR = $sheet_bus->{Cells}[$i][13]->Value;
	my $CD = $sheet_bus->{Cells}[$i][11]->Value;
	my $NGMR = $sheet_bus->{Cells}[$i][23]->Value;
	my $NR = $sheet_bus->{Cells}[$i][24]->Value;
	my $ND = $sheet_bus->{Cells}[$i][22]->Value;
	my $strands = $sheet_bus->{Cells}[$i][25]->Value;
	$UGOD{$eqID} = $OD;
	$UGCGMR{$eqID} = $CGMR;
	$UGCR{$eqID} = $CR;
	$UGCD{$eqID} = $CD;
	$UGNGMR{$eqID} = $NGMR;
	$UGNR{$eqID} = $NR;
	$UGND{$eqID} = $ND;
	$UGStrands{$eqID} = $strands;
	$UGRating{$eqID} = $rating;
	$UGDAB{$eqID} = $DAB;
	$UGDAC{$eqID} = $DAC;
	$UGDBC{$eqID} = $DBC;	
}

# Open equipment database file for data of source, conductor and cable
my $dsnDev="Driver={Microsoft Access Driver (*.mdb)};Dbq=$dbDevFile;Uid=Admin;Pwd=";
my $db = Win32::ODBC->new($dsnDev) or die( Win32::ODBC::Error() );

# ************************ read data for CYMEQSOURCE
my $sql =
  "SELECT EquipmentId, NominalKVLL, DesiredKVLL "
  . "FROM CYMEQSOURCE;";
SQLError() if ( $db->Sql($sql) );

while ( $db->FetchRow() ) {
	my $temp = $db->Data("EquipmentId");
	$NominalVLL{$temp} = $db->Data("NominalKVLL");
	$DisiredVLL{$temp} = $db->Data("DesiredKVLL");
}

# ************************ read data for CYMEQCONDUCTOR
my $sql =
  "SELECT EquipmentId, FirstRating, GMR, R25 "
  . "FROM CYMEQCONDUCTOR;";
SQLError() if ( $db->Sql($sql) );

while ( $db->FetchRow() ) {
	my $temp = $db->Data("EquipmentId");
	$temp = $temp."_OH" if ($temp =~ /DEFAULT/i);		
	$condRating{$temp} = $db->Data("FirstRating");
	$condGMR{$temp} = $db->Data("GMR");
	$condR25{$temp} = $db->Data("R25");    
}

# ************************ read data for CYMEQCABLE
my $sql =
  "SELECT EquipmentId, FirstRating, PositiveSequenceResistance, PositiveSequenceReactance, "
  . "ZeroSequenceResistance, ZeroSequenceReactance, PosSeqShuntSusceptance, ZeroSequenceShuntSusceptance "
  . "FROM CYMEQCABLE;";
SQLError() if ( $db->Sql($sql) );

while ( $db->FetchRow() ) {
	my $temp = $db->Data("EquipmentId");
	#push @cables, $temp;
	$cableRating{$temp} = $db->Data("FirstRating");
	$cablePR{$temp} = sprintf("%.4f", $db->Data("PositiveSequenceResistance")/$meter2ft);
	$cableZR{$temp} = sprintf("%.4f", $db->Data("ZeroSequenceResistance")/$meter2ft);
	$cablePX{$temp} = sprintf("%.4f", $db->Data("PositiveSequenceReactance")/$meter2ft);
	$cableZX{$temp} = sprintf("%.4f", $db->Data("ZeroSequenceReactance")/$meter2ft);
	$cablePB{$temp} = sprintf("%.4f", $db->Data("PosSeqShuntSusceptance")/$meter2ft);
	$cableZB{$temp} = sprintf("%.4f", $db->Data("ZeroSequenceShuntSusceptance")/$meter2ft);
}

# ************************ read data for CYMEQSHUNTCAPACITOR
my $sql =
  "SELECT EquipmentId, RatedKVAR, RatedVoltageKVLL "
  . "FROM CYMEQSHUNTCAPACITOR;";
SQLError() if ( $db->Sql($sql) );

while ( $db->FetchRow() ) {
	my $temp = $db->Data("EquipmentId"); 
	$capEquRatedKVAR{$temp} =  $db->Data("RatedKVAR"); 
	$capEquRatedKVLL{$temp} =  $db->Data("RatedVoltageKVLL")*1000; 
}	

# ************************ read data for CYMEQFUSE
my $sql =
  "SELECT EquipmentId, FirstRatedCurrent, SecondRatedCurrent, "
  . "RatedVoltage, Reversible,SinglePhaseLocking "
  . "FROM CYMEQFUSE;";
SQLError() if ( $db->Sql($sql) );

while ( $db->FetchRow() ) {
	my $temp = $db->Data("EquipmentId"); 
	$fuseEquRatedI1{$temp} =  $db->Data("FirstRatedCurrent"); 
	$fuseEquRatedI2{$temp} =  $db->Data("SecondRatedCurrent"); 
	$fuseEquRatedV{$temp} =  $db->Data("RatedVoltage"); 
	$fuseEquReversible{$temp} =  $db->Data("Reversible"); 
	$fuseEquSinglPhaseLocking{$temp} =  $db->Data("SinglePhaseLocking"); 
}	

# ************************ read data for CYMEQREGULATOR
my $sql =
  "SELECT EquipmentId, FirstRatedKVA, SecondRatedKVA, "
  . "RatedKVLN, MaximumBoost,MaximumBuck, BandWidth, CTPrimaryRating, "
  . "PTRatio,NumberOfTaps "
  . "FROM CYMEQREGULATOR;";
SQLError() if ( $db->Sql($sql) );

while ( $db->FetchRow() ) {
	my $temp = $db->Data("EquipmentId"); 
	$regEquRatedKVA1{$temp} =  $db->Data("FirstRatedKVA"); 	   
	$regEquRatedKVA2{$temp} =  $db->Data("SecondRatedKVA"); 	   
	$regEquRatedKVLN{$temp} =  $db->Data("RatedKVLN"); 	   
	$regEquMaxBoost{$temp} =  $db->Data("MaximumBoost"); 	   
	$regEquMaxBuck{$temp} =  $db->Data("MaximumBuck"); 	   
	$regEquBW{$temp} =  $db->Data("BandWidth"); 	   
	$regEquCT{$temp} =  $db->Data("CTPrimaryRating"); 	   
	$regEquPT{$temp} =  $db->Data("PTRatio"); 	   
	$regEquTaps{$temp} =  $db->Data("NumberOfTaps"); 	   	   
}	

# ************************ read data for CYMEQOVERHEADLINE
my $sql =
  "SELECT EquipmentId, PhaseConductorId, NeutralConductorId, "
  . "ConductorSpacingId, FirstRating "
  . "FROM CYMEQOVERHEADLINE;";
SQLError() if ( $db->Sql($sql) );
while ( $db->FetchRow() ) {
	my $temp = $db->Data("EquipmentId"); 
	my $temp_p = $db->Data("PhaseConductorId");
	my $temp_n = $db->Data("NeutralConductorId");
	$temp_p = $temp_p."_OH" if ($temp_p =~ /DEFAULT/i);
	$temp_n = $temp_n."_OH" if ($temp_n =~ /DEFAULT/i);		
	$LineIDP{$temp}  =  $temp_p; 
	$LineIDN{$temp}  =  $temp_n; 
	$LineIDSpacing{$temp}  =  $db->Data("ConductorSpacingId");
	push @OHConds,  $temp_p;
	push @OHConds,  $temp_n;
	
}	

# ************************ read data for CYMEQSERIESREACTOR
my $sql =
  "SELECT EquipmentId, FirstRatedCurrent, SecondRatedCurrent, ReactanceOhms "
  . "FROM CYMEQSERIESREACTOR;";
SQLError() if ( $db->Sql($sql) );

while ( $db->FetchRow() ) {
	my $temp = $db->Data("EquipmentId"); 
	$SXEquRatedI1{$temp} =  $db->Data("FirstRatedCurrent"); 
	$SXEquRatedI2{$temp} =  $db->Data("SecondRatedCurrent"); 
	$SXX{$temp} =  $db->Data("ReactanceOhms"); 
}	

# End of reading from equipment database
$db->Close();

# Open network database file for data
my $dsnMod="Driver={Microsoft Access Driver (*.mdb)};Dbq=".$dbModFile.";Uid=Admin;Pwd=";
print "DEBBBBBUG".$dsnMod."\n";
print "DEBBBBBUG".$dbModFile."\n";
my $db = Win32::ODBC->new($dsnMod) or die( Win32::ODBC::Error() );

# ************************  read data from  CYMNETWORK
$sql = "SELECT NetworkId FROM CYMNETWORK;";
SQLError() if ( $db->Sql($sql) );
while ( $db->FetchRow() ){  
	push @networkIDs, $db->Data("NetworkId"); 
}
	
# ************************ read data from CYMNODE:
$sql = "SELECT NodeId, X, Y FROM CYMNODE;";
SQLError() if ( $db->Sql($sql) );

while ( $db->FetchRow() ){  
	my $temp = $db->Data("NodeId");
	push @nodes, $temp;
	$nodeX{$temp} = $db->Data("X");
	$nodeY{$temp} = $db->Data("Y");
	#$nodeNetworkID{$temp} = $db->Data("NetworkId");
}	

my %OHLineID = {};
# ************************ read data from CYMOVERHEADLINE:
$sql = "SELECT DeviceNumber, LineId, Length "
	   ."FROM CYMOVERHEADLINE;";
SQLError() if ( $db->Sql($sql) );

while ( $db->FetchRow() ){  
	my $temp = $db->Data("DeviceNumber");
	push @OHSecs, $temp;
	$OHLineID{$temp} = $db->Data("LineId");
	$OHLength{$temp} = sprintf("%.3f", $db->Data("Length") * $meter2ft);
}	

# ************************ read data from CYMOVERHEADBYPHASE:
$sql = "SELECT DeviceNumber, PhaseConductorIdA, PhaseConductorIdB, PhaseConductorIdC, "
       ."NeutralConductorId, ConductorSpacingId, Length "
	   ."FROM CYMOVERHEADBYPHASE;";
SQLError() if ( $db->Sql($sql) );

while ( $db->FetchRow() ){  
	my $temp = $db->Data("DeviceNumber");
	push @OHSecs, $temp;
	$OHA{$temp} = $db->Data("PhaseConductorIdA");
	$OHB{$temp} = $db->Data("PhaseConductorIdB");
	$OHC{$temp} = $db->Data("PhaseConductorIdC");
	$OHN{$temp} = $db->Data("NeutralConductorId");
	push @OHConds, $db->Data("PhaseConductorIdA");
	push @OHConds, $db->Data("PhaseConductorIdB");
	push @OHConds, $db->Data("PhaseConductorIdC");
	push @OHConds, $db->Data("NeutralConductorId");	
	$OHSpacing{$temp} = $db->Data("ConductorSpacingId");
	$OHLength{$temp} = sprintf("%.3f", $db->Data("Length") * $meter2ft);
}	

# ************************ read data from CYMUNDERGROUNDLINE:
$sql = "SELECT DeviceNumber, CableId, Length "
	   ."FROM CYMUNDERGROUNDLINE;";
SQLError() if ( $db->Sql($sql) );

while ( $db->FetchRow() ){  
	my $temp = $db->Data("DeviceNumber");
	push @UGSecs, $temp;
	my $temp_cable = $db->Data("CableId");
	$UGCable{$temp} = $db->Data("CableId");
	push @cables, $temp_cable;
	$UGLength{$temp} = sprintf("%.3f", $db->Data("Length") * $meter2ft);
}	

# ************************ read data from CYMSECTION:
$sql = "SELECT SectionId, FromNodeId, ToNodeId, Phase "
	   ."FROM CYMSECTION;";
SQLError() if ( $db->Sql($sql) );

while ( $db->FetchRow() ){  
	my $temp = $db->Data("SectionId");
	push @secs, $temp;
	my $temp_Fnode = $db->Data("FromNodeId");
	my $temp_Tnode = $db->Data("ToNodeId");
	my $temp_p = int($db->Data("Phase"));
	my $temp_phase;
	$temp_phase= $convertPhase{$temp_p};
	# save spacing and line configuration for OH lines;
	if ( grep{$_ eq $temp} @OHSecs ) {
		my $temp_spacing = $OHSpacing{$temp}.":".$temp_phase;
		$temp_spacing = $LineIDSpacing{$OHLineID{$temp}}.":".$temp_phase if (exists $LineIDSpacing{$OHLineID{$temp}});
		push @LineSpacings, $temp_spacing;
		my $temp_cfg;
		$temp_cfg = $OHA{$temp}.":".$OHB{$temp}.":".$OHC{$temp}.":".$OHN{$temp}.":".$temp_spacing;
		$temp_cfg = $LineIDP{$OHLineID{$temp}}.":".$LineIDN{$OHLineID{$temp}}.":".$temp_spacing if (exists $LineIDSpacing{$OHLineID{$temp}});
		push @LineCFGs, $temp_cfg;
		$OHCFG{$temp} = $temp_cfg;
	}
	if ( grep{$_ eq $temp} @UGSecs ) {
		my $temp_cfg = $UGCable{$temp}.":".$temp_phase;
		push @UGLineCFGs, $temp_cfg;
		$UGCFG{$temp} = $temp_cfg;
	}
	$secPhase{$temp} = $temp_phase;	
	$secFrom{$temp} = $db->Data("FromNodeId");
	$secTo{$temp} = $db->Data("ToNodeId");
	push @To, $db->Data("ToNodeId");
	
	if ( !exists $hashNodePhase{$temp_Fnode} ) {
		$hashNodePhase{$temp_Fnode}	= $temp_phase; 
	} else {
		if ($hashNodePhase{$temp_Fnode}	ne $temp_phase){
			my $new_phase = combinePhases($temp_phase, $hashNodePhase{$temp_Fnode}) ;
			$hashNodePhase{$temp_Fnode} = $new_phase;
		}	
	}
	if ( !exists $hashNodePhase{$temp_Tnode} ) {
		$hashNodePhase{$temp_Tnode}	= $temp_phase; 
	} else {
		if ($hashNodePhase{$temp_Tnode}	ne $temp_phase){
			my $new_phase = combinePhases($temp_phase, $hashNodePhase{$temp_Tnode});
			$hashNodePhase{$temp_Tnode} = $new_phase;
		}	
	}		
}	

# check loop
my @temp_to = findDuplicate(@To);
if ($#temp_to >=0) {
	print "  warning: potential loops: \n";
	print join("\n",@temp_to) if ($iwarning eq 1);
}
print "\n";

# ************************ read data from CYMSECTIONDEVICE:
$sql = "SELECT DeviceNumber, DeviceType, SectionId, Location "
	   ."FROM CYMSECTIONDEVICE;";
SQLError() if ( $db->Sql($sql) );

# 4 regulator 
# 10 recloser
# 12 sectionalizer
# 13 switch
# 14 fuse
# 17 capacitor

my @temp_sec_chks;
while ( $db->FetchRow() ){  
	my $temp_dev = $db->Data("DeviceNumber");	
	my $temp_type = $db->Data("DeviceType");
	# added a post-fix for type number 4-17.
	if (($temp_type >3) and ($temp_type<18)) {
		$temp_dev = $temp_dev."_".$temp_type;
		my $temp_devsec = $db->Data("SectionId");
		push @temp_sec_chks, $temp_devsec;
	}
	push @deviceNums, $temp_dev;
	$DevType{$temp_dev} = $db->Data("DeviceType");
	$DevSection{$temp_dev} = $db->Data("SectionId");
	$DevLoc{$temp_dev} = $db->Data("Location") if (($temp_type >3) and ($temp_type<18)) ;
	my $temp_sec = $db->Data("SectionId");
	$sectionDev{$temp_sec} = $temp_dev if (($temp_type >3) and ($temp_type<18)) ;
	if ($DevType{$temp_dev} eq 4 ) {
		push @regsec, $DevSection{$temp_dev};
	}
	if ($DevType{$temp_dev} eq 10 ) {
		push @recsec, $DevSection{$temp_dev};
	}
	if ($DevType{$temp_dev} eq 12 ) {
		push @sectionalizersec, $DevSection{$temp_dev};
	}
	if ($DevType{$temp_dev} eq 13 ) {
		push @swsec, $DevSection{$temp_dev};
	}
	if ($DevType{$temp_dev} eq 14 ) {
		push @fusesec, $DevSection{$temp_dev};
	}
	if ($DevType{$temp_dev} eq 16 ) {
		push @SXSec, $DevSection{$temp_dev};
	}
	
}
my @temp_check_section = findDuplicate(@temp_sec_chks);
if ($#temp_check_section >=0) {
	print "\n";
	print "  warning: at least two devices located at same line: \n";
	print join("\n",@temp_check_section) ;
}
print "\n";

# ************************ read data from CYMSWITCH:
$sql = "SELECT DeviceNumber, EquipmentId, Phase, " #, ActualStatus, "
	   ."TCCSettingId, NormalFeedingNodeId "
	   ."FROM CYMSWITCH;";
SQLError() if ( $db->Sql($sql) );

while ( $db->FetchRow() ){  
	my $temp = $db->Data("DeviceNumber")."_13";
	$swEquID{$temp} = $db->Data("EquipmentId");
	$swPhase{$temp} = $convertPhase{int($db->Data("Phase"))};
	$swST{$temp} = 1;#$db->Data("ActualStatus");
	$swTCC{$temp} = $db->Data("TCCSettingId");
	$swFeedingNodeID{$temp} = $db->Data("NormalFeedingNodeId");
}	

# ************************ read data from CYMSECTIONALIZER:
$sql = "SELECT DeviceNumber, EquipmentId, Phase, "#ActualStatus, "
	   ."TCCSettingId, NormalFeedingNodeId "
	   ."FROM CYMSECTIONALIZER;";
SQLError() if ( $db->Sql($sql) );

while ( $db->FetchRow() ){  
	my $temp = $db->Data("DeviceNumber")."_12"; #added device type
	$sectionalizerEquID{$temp} = $db->Data("EquipmentId");
	$sectionalizerPhase{$temp} = $convertPhase{int($db->Data("Phase"))};
	$sectionalizerST{$temp} = 1;#$db->Data("ActualStatus");
	$sectionalizerTCC{$temp} = $db->Data("TCCSettingId");
	$sectionalizerFeedingNodeID{$temp} = $db->Data("NormalFeedingNodeId");
}	

# ************************ read data from CYMFUSE:
$sql = "SELECT DeviceNumber, EquipmentId, Phase, "#ActualStatus, "
	   ."TCCSettingId, NormalFeedingNodeId "
	   ."FROM CYMFUSE;";
SQLError() if ( $db->Sql($sql) );

while ( $db->FetchRow() ){  
	my $temp = $db->Data("DeviceNumber")."_14"; #added device type
	$fuseEquID{$temp} = $db->Data("EquipmentId");
	$fusePhase{$temp} = $convertPhase{int($db->Data("Phase"))};
	$fuseST{$temp} = 1;#$db->Data("ActualStatus");
	$fuseTCC{$temp} = $db->Data("TCCSettingId");
	$fuseFeedingNodeID{$temp} = $db->Data("NormalFeedingNodeId");
}	

# ************************ read data from CYMSERIESREACTOR:
$sql = "SELECT DeviceNumber, EquipmentId, Phase "
	   ."FROM CYMSERIESREACTOR;";
SQLError() if ( $db->Sql($sql) );

while ( $db->FetchRow() ){  
	my $temp = $db->Data("DeviceNumber")."_16"; #added device type
	$SXEquID{$temp} = $db->Data("EquipmentId");
	$SXPhase{$temp} = $convertPhase{int($db->Data("Phase"))};	
}	

# ************************ read data from CYMRECLOSER:
$sql = "SELECT DeviceNumber, EquipmentId, Phase, "#ActualStatus, "
	   ."TCCSettingId, NormalFeedingNodeId "
	   ."FROM CYMRECLOSER;";
SQLError() if ( $db->Sql($sql) );

while ( $db->FetchRow() ){  
	my $temp = $db->Data("DeviceNumber")."_10"; #added device type;
	$recEquID{$temp} = $db->Data("EquipmentId");
	$recPhase{$temp} = $convertPhase{int($db->Data("Phase"))};
	$recST{$temp} = 1;#$db->Data("ActualStatus");
	$recTCC{$temp} = $db->Data("TCCSettingId");
	$recFeedingNodeID{$temp} = $db->Data("NormalFeedingNodeId");
}	

# ************************ read data from CYMREGULATOR:
$sql = "SELECT DeviceNumber, EquipmentId, ConnectedPhase, ConnectionConfiguration, "
	   ."CTPrimaryRating, PTRatio,BandWidth,BoostPercent, BuckPercent,SettingOption,  "
	   ."TapPositionA, TapPositionB, TapPositionC, ControlStatus, NormalFeedingNodeId "
	   ."FROM CYMREGULATOR;";
SQLError() if ( $db->Sql($sql) );

while ( $db->FetchRow() ){  
	my $temp = $db->Data("DeviceNumber")."_4"; #added device type
	$regEquID{$temp} = $db->Data("EquipmentId");
	$regPhase{$temp} = $RegconvertPhase{$db->Data("ConnectedPhase")};
	$regCFG{$temp} = $db->Data("ConnectionConfiguration");
	$regCT{$temp} = $db->Data("CTPrimaryRating");
	$regPT{$temp} = $db->Data("PTRatio");
	$regBW{$temp} = $db->Data("BandWidth");
	$regBoost{$temp} = $convertPhase{$db->Data("BoostPercent")};
	$regBuck{$temp} = $db->Data("BuckPercent");
	$regSetting{$temp} = $db->Data("SettingOption");
	$regTapA{$temp} = $db->Data("TapPositionA");
	$regTapB{$temp} = $db->Data("TapPositionB");
	$regTapC{$temp} = $db->Data("TapPositionC");
	$regCtrST{$temp} = $db->Data("ControlStatus");
	$regNormalFeedingNodeId{$temp} = $db->Data("NormalFeedingNodeId");	
}	

# ************************ read data from CYMSOURCE:
$sql = "SELECT NodeId, NetworkId, EquipmentId "
	   ."FROM CYMSOURCE;";
SQLError() if ( $db->Sql($sql) );

while ( $db->FetchRow() ){  
	$source = $db->Data("NodeId");
	$sourceEqID{$source} = $db->Data("EquipmentId");
}	

# ************************ read data from CYMSHUNTCAPACITOR:
$sql = "SELECT DeviceNumber, EquipmentId, Status, Phase, "
	   ."ConnectionConfiguration, KVARA,KVARB,KVARC,KVLN, CapacitorControlType "
	   ."FROM CYMSHUNTCAPACITOR;";
SQLError() if ( $db->Sql($sql) );

while ( $db->FetchRow() ){  
	my $temp = $db->Data("DeviceNumber")."_17"; #added device type
	push @shuntcaps, $temp;
	$capEquID{$temp} = $db->Data("EquipmentId");
	$capST{$temp} = $db->Data("Status");
	$capPhase{$temp} = $convertPhase{int($db->Data("Phase"))};
	$capCFG{$temp} = $db->Data("ConnectionConfiguration");
	$capA{$temp} = $db->Data("KVARA");
	$capB{$temp} = $db->Data("KVARB");
	$capC{$temp} = $db->Data("KVARC");
	$capVLN{$temp} = $db->Data("KVLN,");
	my $type = $db->Data("CapacitorControlType");
	$capType{$temp} = $type;	
	$flag_time = 1 if ($type eq 1);
	$flag_kvar = 1 if ($type eq 2);
	$flag_current = 1 if ($type eq 3);
	$flag_pf = 1 if ($type eq 4);
	$flag_reactive = 1 if ($type eq 5);
	$flag_temp = 1 if ($type eq 6);
	$flag_voltage = 1 if ($type eq 7);
}

if ($flag_current eq 1) {
# ************************ read data from CYMCAPACITORCONTROL_CURRENT
	$sql = "SELECT DeviceNumber, OnCurrent, OffCurrent, ControlledPhase "
	   ."FROM CYMCAPACITORCONTROL_CURRENT;";
	SQLError() if ( $db->Sql($sql) );

	while ( $db->FetchRow() ){     
		my $temp = $db->Data("DeviceNumber")."_17";
		$capcurrentOn{$temp} = $db->Data("OnCurrent");
		$capcurrentOff{$temp} = $db->Data("OffCurrent");
		$capcurrentPhase{$temp} = $convertPhase{$db->Data("ControlledPhase")};
	}	
}	   

if ($flag_kvar eq 1) {
# ************************ read data from CYMCAPACITORCONTROL_CURRENT
	$sql = "SELECT DeviceNumber, OnKVAR, OffKVAR, ControlledPhase "
	   ."FROM CYMCAPACITORCONTROL_KVAR;";
	SQLError() if ( $db->Sql($sql) );

	while ( $db->FetchRow() ){     
		my $temp = $db->Data("DeviceNumber")."_17";
		$capvarOn{$temp} = $db->Data("OnKVAR")*1000;
		$capvarOff{$temp} = $db->Data("OffKVAR")*1000;
		$capvarPhase{$temp} = $convertPhase{$db->Data("ControlledPhase")};
	}	
}	   

# ************************ read data from CYMCUSTOMERLOAD to find the load phases:
$sql = "SELECT DeviceNumber, DeviceType, CustomerNumber, ConsumerClassId, "
	   ."LoadValueType, Phase, LoadValue1, LoadValue2, ConnectedKVA "
	   ."FROM CYMCUSTOMERLOAD;";
SQLError() if ( $db->Sql($sql) );

while ( $db->FetchRow() ){  
	my $temp = $db->Data("DeviceNumber");
	my $temp_phase = int($db->Data("Phase"));
	my $phase;
	$phase = "A" if ($temp_phase eq 1);
	$phase = "B" if ($temp_phase eq 2);
	$phase = "C" if ($temp_phase eq 3);	
	if ( exists $loadphase{$temp}) {
		$loadphase{$temp} = combinePhases($loadphase{$temp}, $phase);
	} else {
		$loadphase{$temp}  = $phase;			
	}	
}	

# ************************ reopen CYMCSTOMERLOAD table and read data:
$sql = "SELECT DeviceNumber, DeviceType, CustomerNumber, ConsumerClassId, "
	   ."LoadValueType, Phase, LoadValue1, LoadValue2, ConnectedKVA, NumberOfCustomer "
	   ."FROM CYMCUSTOMERLOAD;";
SQLError() if ( $db->Sql($sql) );
my $total_Rload=0;
my $total_Xload=0;
while ( $db->FetchRow() ){  
	my $temp = $db->Data("DeviceNumber");
	my $temp_phase = int($db->Data("Phase"));	
	my $phase;
	my $temp_load = $db->Data("LoadValue1");
	if (($temp_phase ne 0) and ($temp_load ne 0)){
		$phase = "A" if ($temp_phase eq 1);
		$phase = "B" if ($temp_phase eq 2);
		$phase = "C" if ($temp_phase eq 3);		
		my $temp_tn = $temp.":".$phase;	
		push @loads, $temp_tn;
		$loadPhase{$temp_tn} = $phase;
		$loadType{$temp_tn} = int($db->Data("DeviceType"));
		print "loadtype $temp_tn-> $loadType{$temp_tn}\n";
		$loadCustomerNum{$temp_tn} = $db->Data("CustomerNumber");
		$loadClass{$temp_tn} = $db->Data("ConsumerClassId");
		$loadClass{$temp} = $db->Data("ConsumerClassId");
		$loadValueType = $db->Data("LoadValueType");
		$loadV1 = $db->Data("LoadValue1");
		$loadV2 = $db->Data("LoadValue2");
		$loadKVA{$temp_tn} = $db->Data("ConnectedKVA");
		my $no_of_customer = $db->Data("NumberOfCustomer");
		$loadnoCust{$temp_tn} = sprintf("%d",$no_of_customer);
		if ($loadValueType eq 0) { #(KW & KVAR)
			$loadKW{$temp_tn} = $loadV1*1000;
			$loadKVAR{$temp_tn} = $loadV2*1000;
			$total_Rload = $total_Rload + $loadV1;
			$total_Xload = $total_Xload + $loadV2;
		} elsif	($loadValueType eq 1) { #(KVA & PF)
			if ($loadV2 >0) {
				$loadKW{$temp_tn} = sprintf("%.3f", $loadV1 * $loadV2/100 *1000);
				$loadKVAR{$temp_tn} = sprintf("%.3f", $loadV1 * sqrt(1-($loadV2/100)**2) * 1000);
			} else {	
				$loadKW{$temp_tn} = sprintf("%.3f", -$loadV1 * $loadV2/100 *1000);
				$loadKVAR{$temp_tn} = sprintf("%.3f", -$loadV1 * sqrt(1-($loadV2/100)**2) * 1000);
			}	
			$total_Rload = $total_Rload + $loadKW{$temp_tn}/1000;
			$total_Xload = $total_Xload + $loadKVAR{$temp_tn}/1000;
		} else	{ #(KW & PF)
			$loadKW{$temp_tn} = $loadV1*1000;
			$loadKVAR{$temp_tn} = sprintf("%.3f", $loadV1/($loadV2/100)* sqrt(1-($loadV2/100)**2) * 1000);
			$total_Rload = $total_Rload + $loadV1;
			$total_Xload = $total_Xload + $loadKVAR{$temp_tn}/1000;
		}	
		# spot loads
		if ($loadType{$temp_tn} eq 20) {
			if ($phase =~/A/i) {
				$spotloadKW1{$temp}= $loadKW{$temp_tn};
				$spotloadKVAR1{$temp}= $loadKVAR{$temp_tn};
				my $temp_rating = sqrt($loadKW{$temp_tn}**2 + $loadKVAR{$temp_tn}**2)/1000;
				my $return_rating = sprintf("%.1f", return_rating($temp_rating));
				$spotloadKVA1{$temp}= $return_rating;
			} elsif ($phase =~/B/i) {	
				$spotloadKW2{$temp}= $loadKW{$temp_tn};
				$spotloadKVAR2{$temp}= $loadKVAR{$temp_tn};
				my $temp_rating = sqrt($loadKW{$temp_tn}**2 + $loadKVAR{$temp_tn}**2)/1000;
				my $return_rating = sprintf("%.1f", return_rating($temp_rating));
				$spotloadKVA2{$temp}= $return_rating;
			} elsif ($phase =~ /C/i) {
				$spotloadKW3{$temp}= $loadKW{$temp_tn};
				$spotloadKVAR3{$temp}= $loadKVAR{$temp_tn};
				my $temp_rating = sqrt($loadKW{$temp_tn}**2 + $loadKVAR{$temp_tn}**2)/1000;
				my $return_rating = sprintf("%.1f", return_rating($temp_rating));
				$spotloadKVA3{$temp}= $return_rating;
			} else {
				print "*** warning: cannot recognize phase $phase at $temp_tn\n";
			}
			if ( !exists $spotload{$temp} ) {
				$spotload{$temp} = $temp;
				$spotloadPhase{$temp} = $phase;
			} else {	
				$spotloadPhase{$temp} = $spotloadPhase{$temp}.$phase;
			}	
			push @spotloads, $temp;
		}	
	}	
}
=pod
# find distributed loads
for ( my $i = 0 ; $i <= $#loads ; $i++ ) {	
	my @temp = split(/\:/,$loads[$i]);
	my $type = $DevType{$DevSection{$temp[0]} };
	#print " $loads[$i] - >$loadClass{$loads[$i]} -> $loadType{$loads[$i]} \n";# if ($loads[$i] =~/776/);
	if (($loadType{$loads[$i]} eq 21) and ($loadKW{$loads[$i]} ne 0) and ($loadKVAR{$loads[$i]} ne 0)){
		# if single phase non-residential load, use SPCT as well
		#print " $loads[$i] - >$loadClass{$loads[$i]} \n";# if ($loads[$i] =~/776/);
		if (($loadClass{$loads[$i]} =~ /Residential/i ) or (length($loadphase{$temp[0]}) <2)) {			
			my $temp_spct_cfg = $loadKVA{$loads[$i]}.":".$loadPhase{$loads[$i]}.":".$type;
			$tn_cfg{$loads[$i]} = $temp_spct_cfg;
			push @SPCTCFG,$temp_spct_cfg;
			push @residential, $loads[$i];
			my $temp_tn1 = $loads[$i]."_tn";
			push @tn1, $temp_tn1;
			$tn1_phase{$temp_tn1} = $loadPhase{$loads[$i]};
		} else { #non_residential
			my @temp_key = split(/:/,$loads[$i]);
			$non_residential_phase{$temp_key[0]} = $loadphase{$temp_key[0]};
			push @non_residential, $temp_key[0];
			# 2. load
			if($temp_key[1] =~/A/i){ 
				$non_residential_KVA1{$temp_key[0]} = $loadKVA{$loads[$i]}; 
				$non_residential_KW1{$temp_key[0]} = $loadKW{$loads[$i]};
				$non_residential_KVAR1{$temp_key[0]} = $loadKVAR{$loads[$i]};				
			}	
			if($temp_key[1] =~/B/i){ 
				$non_residential_KVA2{$temp_key[0]} = $loadKVA{$loads[$i]}; 
				$non_residential_KW2{$temp_key[0]} = $loadKW{$loads[$i]};
				$non_residential_KVAR2{$temp_key[0]} = $loadKVAR{$loads[$i]};
			}
			if($temp_key[1] =~/C/i){ 
				$non_residential_KVA3{$temp_key[0]} = $loadKVA{$loads[$i]}; 
				$non_residential_KW3{$temp_key[0]} = $loadKW{$loads[$i]};
				$non_residential_KVAR3{$temp_key[0]} = $loadKVAR{$loads[$i]};
			}
		}	
	}
}	
=cut

# find distributed loads
for ( my $i = 0 ; $i <= $#loads ; $i++ ) {	
	my @temp = split(/\:/,$loads[$i]);
	my $type = $DevType{$DevSection{$temp[0]} };
	#print " $loads[$i] - >$loadClass{$loads[$i]} -> $loadType{$loads[$i]} \n";# if ($loads[$i] =~/776/);
	if (($loadType{$loads[$i]} eq 21) and ($loadKW{$loads[$i]} ne 0) and ($loadKVAR{$loads[$i]} ne 0)){
		# if residential load, use SPCT
		#if (($loadClass{$loads[$i]} =~ /Residential/i ) or (length($loadphase{$temp[0]}) <2)) {			
		if ($loadClass{$loads[$i]} =~ /Residential/i ) {			
			my $temp_spct_cfg = $loadKVA{$loads[$i]}.":".$loadPhase{$loads[$i]}.":".$type;
			$tn_cfg{$loads[$i]} = $temp_spct_cfg;
			push @SPCTCFG,$temp_spct_cfg;
			push @residential, $loads[$i];
			my $temp_tn1 = $loads[$i]."_tn";
			push @tn1, $temp_tn1;
			$tn1_phase{$temp_tn1} = $loadPhase{$loads[$i]};
		} else { #non_residential
			my @temp_key = split(/:/,$loads[$i]);
			$non_residential_phase{$temp_key[0]} = $loadphase{$temp_key[0]};
			push @non_residential, $temp_key[0];
			# 2. load
			if($temp_key[1] =~/A/i){ 
				$non_residential_KVA1{$temp_key[0]} = $loadKVA{$loads[$i]}; 
				$non_residential_KW1{$temp_key[0]} = $loadKW{$loads[$i]};
				$non_residential_KVAR1{$temp_key[0]} = $loadKVAR{$loads[$i]};				
			}	
			if($temp_key[1] =~/B/i){ 
				$non_residential_KVA2{$temp_key[0]} = $loadKVA{$loads[$i]}; 
				$non_residential_KW2{$temp_key[0]} = $loadKW{$loads[$i]};
				$non_residential_KVAR2{$temp_key[0]} = $loadKVAR{$loads[$i]};
			}
			if($temp_key[1] =~/C/i){ 
				$non_residential_KVA3{$temp_key[0]} = $loadKVA{$loads[$i]}; 
				$non_residential_KW3{$temp_key[0]} = $loadKW{$loads[$i]};
				$non_residential_KVAR3{$temp_key[0]} = $loadKVAR{$loads[$i]};
			}
		}	
	}
}	


# define voltages
#$my $temp_VLN = ($NominalVLL{$sourceEqID{$source}}+$DisiredVLL{$sourceEqID{$source}})/2;
my $VLN = sprintf("%.3f",($DisiredVLL{$sourceEqID{$source}})*1000/sqrt(3)) ;
my $realb  = sprintf("%.3f", $VLN * cos( -120 * $pi / 180.0 ) );
my $imageb = sprintf("%.3f", $VLN * sin( -120 * $pi / 180.0 ) );
my $realc  = sprintf("%.3f", $VLN * cos( 120  * $pi / 180.0 ) );
my $imagec = sprintf("%.3f", $VLN * sin( 120  * $pi / 180.0 ) );
my $VA = $VLN."+0.000j";
my $VB = $realb.$imageb."j";
my $VC = $realc."+".$imagec."j";
my $V2nd = 124;
my $temp_ratio = $VLN/$V2nd;
#print "ratio = $temp_ratio \n";
my $realb2  = sprintf("%.3f", $V2nd * cos( -120 * $pi / 180.0 ) );
my $imageb2 = sprintf("%.3f", $V2nd * sin( -120 * $pi / 180.0 ) );
my $realc2  = sprintf("%.3f", $V2nd * cos( 120  * $pi / 180.0 ) );
my $imagec2 = sprintf("%.3f", $V2nd * sin( 120  * $pi / 180.0 ) );
my $VA2 = $V2nd."+0.000j";
my $VB2 = $realb2.$imageb2."j";
my $VC2 = $realc2."+".$imagec2."j";

@UniqueLineCFGs=findUnique(@LineCFGs);
@UniqueUGLineCFGs=findUnique(@UGLineCFGs);
@UniqueLineSpacings=findUnique(@LineSpacings);
@UniqueOHConds=findUnique(@OHConds);
@UniqueSPCTCFG = findUnique(@SPCTCFG);
@uniquespotloads = findUnique(@spotloads);
@UGcables = findUnique(@cables);
@unique_non_residential = findUnique(@non_residential);

# find spot loads
for ( my $i = 0 ; $i <= $#uniquespotloads ; $i++ ) {	
	my $temp_type = $DevType{$DevSection{$uniquespotloads[$i]} };
	my $temp_cfg = $spotloadKVA1{$uniquespotloads[$i]}.":".$spotloadKVA2{$uniquespotloads[$i]}.":".
		$spotloadKVA3{$uniquespotloads[$i]}.":".$spotloadPhase{$uniquespotloads[$i]}.":".$temp_type;
	push @WYEWYECFG, $temp_cfg;
}		

# find non_residential distribute loads
for ( my $i = 0 ; $i <= $#unique_non_residential ; $i++ ) {	
	my $temp_type = $DevType{$DevSection{$unique_non_residential[$i]} };
	my $temp_cfg = $non_residential_KVA1{$unique_non_residential[$i]}.":"
		.$non_residential_KVA2{$unique_non_residential[$i]}.":"
		.$non_residential_KVA3{$unique_non_residential[$i]}.":"
		.$non_residential_phase{$unique_non_residential[$i]}.":".$temp_type;
	push @WYEWYECFG, $temp_cfg;
}		
@uniqueWYEWYECFG = findUnique(@WYEWYECFG);


# start creating .glm file
printHeader();

for ( my $i = 0 ; $i <= $#UniqueOHConds ; $i++ ) {
	printOHCond($UniqueOHConds[$i]);
}

for ( my $i = 0 ; $i <= $#UGcables ; $i++ ) {	
	printUGCond($UGcables[$i]);
}

printTLCond();

for ( my $i = 0 ; $i <= $#UniqueLineSpacings ; $i++ ) {	
	printLineSpacing($UniqueLineSpacings[$i]);
}

for ( my $i = 0 ; $i <= $#UniqueUGLineCFGs ; $i++ ) {	
	printUGLineSpacing($UniqueUGLineCFGs[$i]);
}	

for ( my $i = 0 ; $i <= $#UniqueLineCFGs ; $i++ ) {	
	printLineCFG($UniqueLineCFGs[$i]);
}	

for ( my $i = 0 ; $i <= $#UniqueUGLineCFGs ; $i++ ) {
	printUGLineCFG($UniqueUGLineCFGs[$i]);
}	

for ( my $i = 0 ; $i <= $#UniqueSPCTCFG ; $i++ ) {	
	printSPCTCFG($UniqueSPCTCFG[$i]);
}	
=pod
for ( my $i = 0 ; $i <= $#uniqueWYEWYECFG ; $i++ ) {	
	printWYEWYECFG($uniqueWYEWYECFG[$i]);
}	
=cut
for ( my $i = 0 ; $i <= $#nodes ; $i++ ) {	
	printNodes($nodes[$i]);
}	

for ( my $i = 0 ; $i <= $#uniquespotloads ; $i++ ) {	
	#$ic = $ic + 1;
	printSPOTLOAD($uniquespotloads[$i]);
}	

for ( my $i = 0 ; $i <= $#uniquespotloads ; $i++ ) {	
	printMeter($uniquespotloads[$i]);
}	

for ( my $i = 0 ; $i <= $#uniquespotloads ; $i++ ) {	
	#printXFMR($uniquespotloads[$i]);
	printLine($uniquespotloads[$i]);
}	

for ( my $i = 0 ; $i <= $#unique_non_residential ; $i++ ) {	
	printNon_Res($unique_non_residential[$i]);
}	

for ( my $i = 0 ; $i <= $#unique_non_residential ; $i++ ) {	
	printNon_Res_Meter($unique_non_residential[$i]);
}	

for ( my $i = 0 ; $i <= $#unique_non_residential ; $i++ ) {	
	#printNon_Res_XFMR($unique_non_residential[$i]);
	printNon_Res_Line($unique_non_residential[$i]);
}	


for ( my $i = 0 ; $i <= $#swsec ; $i++ ) {	
	printsw($swsec[$i]);
}

for ( my $i = 0 ; $i <= $#swsec ; $i++ ) {	
	printswnode($swsec[$i]);
}

for ( my $i = 0 ; $i <= $#recsec ; $i++ ) {	
	printrec($recsec[$i]);
}

for ( my $i = 0 ; $i <= $#recsec ; $i++ ) {	
	printrecnode($recsec[$i]);
}

for ( my $i = 0 ; $i <= $#fusesec ; $i++ ) {
	printfuse($fusesec[$i]);
}

for ( my $i = 0 ; $i <= $#fusesec ; $i++ ) {	
	printfusenode($fusesec[$i]);
}

for ( my $i = 0 ; $i <= $#sectionalizersec ; $i++ ) {	
	printsectionalizer($sectionalizersec[$i]);
}

for ( my $i = 0 ; $i <= $#sectionalizersec ; $i++ ) {	
	printsectionalizernode($sectionalizersec[$i]);
}

#print regulator configurations
for ( my $i = 0 ; $i <= $#regsec ; $i++ ) {
	$hashRegCFG{$regsec[$i]} = $regsec[$i]."-regcfg";
	printRegCFG($regsec[$i]);
	
}
#print regulator 
for ( my $i = 0 ; $i <= $#regsec ; $i++ ) {
	printReg($regsec[$i]);
}

#print regulator node
for ( my $i = 0 ; $i <= $#regsec ; $i++ ) {
	printRegnode($regsec[$i]);
}

for ( my $i = 0 ; $i <= $#SXSec ; $i++ ) {
	printSX($SXSec[$i]);
}

for ( my $i = 0 ; $i <= $#SXSec ; $i++ ) {	
	printSXnode($SXSec[$i]);
}

# print OH
for ( my $i = 0 ; $i <= $#deviceNums ; $i++ ) {	
	if (($DevType{$deviceNums[$i]} eq 2) or ($DevType{$deviceNums[$i]} eq 3)) {
		if ( ( !grep{$_ eq $deviceNums[$i]} @swsec ) and
			 ( !grep{$_ eq $deviceNums[$i]} @fusesec ) and
			 ( !grep{$_ eq $deviceNums[$i]} @SXSec ) and
			 ( !grep{$_ eq $deviceNums[$i]} @regsec ) and
			 ( !grep{$_ eq $deviceNums[$i]} @sectionalizersec ) and
			 ( !grep{$_ eq $deviceNums[$i]} @recsec )) {
			printOHSecs($deviceNums[$i]);
		} else {
		}	
	}	
}

# print cable
for ( my $i = 0 ; $i <= $#deviceNums+1 ; $i++ ) {	
	if ($DevType{$deviceNums[$i]} eq 1) {
		if ( ( !grep{$_ eq $deviceNums[$i]} @swsec ) and
			 ( !grep{$_ eq $deviceNums[$i]} @fusesec ) and
			 ( !grep{$_ eq $deviceNums[$i]} @SXSec ) and
			 ( !grep{$_ eq $deviceNums[$i]} @regsec ) and
			 ( !grep{$_ eq $deviceNums[$i]} @sectionalizersec ) and
			 ( !grep{$_ eq $deviceNums[$i]} @recsec )) {
			printUGSecs($deviceNums[$i]);
		}	
	}	
}

# print tn1
for ( my $i = 0 ; $i <= $#tn1 ; $i++ ) {	
	printTN1($tn1[$i]);
}

# print tn load
for ( my $i = 0 ; $i <= $#residential ; $i++ ) {	
	printTN($residential[$i]);
}

# print tn meter
for ( my $i = 0 ; $i <= $#residential ; $i++ ) {	
	printTM($residential[$i]);
}

# print triplex line (from $TN1 to $TM)
for ( my $i = 0 ; $i <= $#residential ; $i++ ) {	
	printTL($residential[$i]);
}

# print SPCT (from $TO to $TN1)
for ( my $i = 0 ; $i <= $#residential ; $i++ ) {	
	$ic = $ic+1;
	printSPCT($residential[$i]);
}

# print capacitor
for ( my $i = 0 ; $i <= $#deviceNums ; $i++ ) {	
	if ($DevType{$deviceNums[$i]} eq 17) {
		printCap($deviceNums[$i]);
	}	
}

printSubstation_Meter() if ($sm_flag eq 0);

$sum_DL_KW = sprintf("%.3f",$sum_DL_KW);
$sum_DL_KVAR = sprintf("%.3f",$sum_DL_KVAR);
$sum_spot_KW = sprintf("%.3f",$sum_spot_KW);
$sum_spot_KVAR = sprintf("%.3f",$sum_spot_KVAR);

my $sum_KW = $sum_DL_KW + $sum_spot_KW;
my $sum_KVAR = $sum_DL_KVAR + $sum_spot_KVAR;
print "\n\t\tKW   \tKVAR\n";
print"Dist. Load: $sum_DL_KW\t$sum_DL_KVAR\n";
print"Spot  Load: $sum_spot_KW\t$sum_spot_KVAR\n";
print"Total Load: $sum_KW\t$sum_KVAR\n";
print"Total load 2: $total_Rload, $total_Xload\n";

while( my ($k, $v) = each %recPhase ) {
	#print "key: $k, value: $v \n";
}
for ( my $i = 0 ; $i <= $#recsec ; $i++ ) {	
	#print "recloser: $recsec[$i]\n";
}	

#########################################
# *********** Sub functions *********** #
#########################################

sub printUsage() {
    print qq~
---------------------------------------------------------------------
Usage:

$0 <dbEquFile> <dbNetworkFile> <FeederName> 

<dbEquFile> Required 
	- An absolute or relative path to the network database file(s) that is 
	  to be parsed and imported.	

<dbNetworkFile> Required 
	- An absolute or relative path to the network database file(s) that is 
	  to be parsed and imported.	

<FeederName> Required 
	- A feeder name that user specified

Example: perl Cyme_to_GridLabD.pl Equ_file.mdb Network_file.mdb
         	    

---------------------------------------------------------------------
~;
    exit(0);
}

sub SQLError() {
	print "$sql\n";
    print( "SQL Error 1: " . $db->Error() . "\n" );
    $db->Close();
    exit(123);
}

sub findUnique {
    my @array = @_;
	my %seen = ();
	my @unique = grep{! $seen{$_}++}@array;
    return @unique;
}

sub findDuplicate {
	my %s;
    undef %s;
    my @out = grep( $s{$_}++, @_ );
    return @out;
}

sub combinePhases($) {
	my $p1 = shift;
	my $p2 = shift;
	my @out1 = ();
	my @out2 = ();
	@out1 = splitStrings($p1);
	@out2 = splitStrings($p2);
	my @union = ();
	my %count = ();
	foreach my $element (@out1, @out2){$count{$element}++}
	foreach my $element (keys %count) {
		push @union, $element;
	}
	@union = sort (@union);	
	my $final_phase;
	for ( my $i = 0 ; $i <= $#union; $i++ ) {
		$final_phase = $final_phase.$union[$i];
	}
	return $final_phase;	
}

sub splitStrings($) {
	my $array = shift;	
	my $b = length($array);
	my @out;
	for ( my $i = 0 ; $i < length($array) ; $i++ ) {
		my $temp = substr($array, $i, 1);
		push @out, $temp;
	}
	return @out;
}

sub return_rating($) {
	my @standard_ratings=(0, 5,10,15,25,30,37.5,50,75,87.5,100,112.5,125,137.5,150,162.5,175,187.5,200,225,250,262.5,300, 337.5, 400, 412.5, 450, 500, 750, 1000, 1250, 1500, 2000, 2500, 3000, 4000, 5000);
	my $input = shift;
	my $out;	
	for ( my $i = 0 ; $i < $#standard_ratings ; $i++ ) {	
		if ( ( $standard_ratings[$i] < $input ) and ( $standard_ratings[$i+1] >= $input ) )  {
			$out = $standard_ratings[$i+1];
		}	
		if ( $input > $standard_ratings[-1] ) {
			$out = $input;
		}	
	}
	return $out;
}	

sub printHeader (){
	my $temp_date = date_time ();
	chomp($temp_date);
	print GLM_FILE "// \$Id: $feederName.glm $temp_date ychen \$\n" ;
	print GLM_FILE "//*********************************************\n\n";
	print GLM_FILE "#set iteration_limit=50\n";
	print GLM_FILE "#set profiler=1\n";
	print GLM_FILE "#set pauseatexit=1\n";
	print GLM_FILE "#set relax_naming_rules=1\n";
	print GLM_FILE "#define stylesheet=http://gridlab-d.svn.sourceforge.net/viewvc/gridlab-d/trunk/core/gridlabd-2_0\n\n";
	print GLM_FILE "clock{\n\t timezone EST+5EDT;\n\t timestamp '2000-01-01 0:00:00';\n}\n\n";
	print GLM_FILE "//*********************************************\n";
	print GLM_FILE "// modules\n";
	print GLM_FILE "module powerflow {\n\tsolver_method $sm;\n\tdefault_maximum_voltage_error 1e-9;\n};\n\n\n";
}	

sub date_time() {
	my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst)=localtime(time);
	my $out = sprintf ("%4d-%02d-%02d %02d:%02d:%02d\n", $year+1900,$mon+1,$mday,$hour,$min,$sec);
	return $out;
}

sub printNodes() {
	my $temp_node = shift;
	print GLM_FILE "object node {\n";
	print GLM_FILE "\tname $feederName-$temp_node;\n";
	my $source_meter = "$feederName-Substation_Meter";
	print GLM_FILE "\tparent $source_meter;\n" if (($temp_node eq $source) and ($sm_flag eq 0));
	print GLM_FILE "\tbustype SWING;\n" if ($temp_node eq $source);
	my $temp_phase = $hashNodePhase{$temp_node};
	print GLM_FILE "\tphases $temp_phase;\n";
	print GLM_FILE "\tnominal_voltage $VLN;\n";
	print GLM_FILE "}\n\n";
}	

sub printsw() {
	my $a = shift;
	my $temp_node = $sectionDev{$a}."_swnode";
	if ($DevLoc{$sectionDev{$a}} == 1) { #from side
		print GLM_FILE "object switch {\n";
		my $name = $a."_sw";
		print GLM_FILE "\tname $feederName-$name;\n";
		print GLM_FILE "\tphases $swPhase{$sectionDev{$a}};\n";
		print GLM_FILE "\tfrom $feederName-$secFrom{$a};\n"; 
		print GLM_FILE "\tto $feederName-$temp_node;\n"; 	
		if ( $swST{$sectionDev{$a}} == 1 ) {
			print GLM_FILE "\tstatus CLOSED;\n}\n\n";  
		} else {	
			print GLM_FILE "\tstatus CLOSED;\n}\n\n";  
		}	
		if ( grep{$_ eq $a} @OHSecs ) {
			printOHSecs1($a,$temp_node,"SW");
		}	
		if ( grep{$_ eq $a} @UGSecs ) {
			printUGSecs1($a,$temp_node,"SW");		
		}		
	}		
	if ($DevLoc{$sectionDev{$a}} == 2) { #to side
		print GLM_FILE "object switch {\n";
		my $name = $a."_sw";
		print GLM_FILE "\tname $feederName-$name;\n";
		print GLM_FILE "\tphases $swPhase{$sectionDev{$a}};\n";
		print GLM_FILE "\tfrom $feederName-$temp_node;\n"; 	
		print GLM_FILE "\tto $feederName-$secTo{$a};\n"; 	
		if ( $swST{$sectionDev{$a}} == 1 ) {
			print GLM_FILE "\tstatus CLOSED;\n}\n\n";  
		} else {	
			print GLM_FILE "\tstatus CLOSED;\n}\n\n";  
		}	
		if ( grep{$_ eq $a} @OHSecs ) {
			printOHSecs2($a,$temp_node,"SW");
		}	
		if ( grep{$_ eq $a} @UGSecs ) {
			printUGSecs2($a,$temp_node,"SW");		
		}		
	}	
}	

sub printswnode() {
	my $a = shift;
	my $temp_node = $sectionDev{$a}."_swnode";
	print GLM_FILE "object node {\n";
	print GLM_FILE "\tname $feederName-$temp_node;\n";
	print GLM_FILE "\tphases $swPhase{$sectionDev{$a}};\n";
	print GLM_FILE "\tnominal_voltage $VLN;\n";
	print GLM_FILE "}\n\n";	
}	

sub printrec() {
	my $a = shift;
	my $temp_node = $sectionDev{$a}."_recnode";
	if ($DevLoc{$sectionDev{$a}} == 1) { #from side
		print GLM_FILE "//Recloser, used as switch for now \n";
		print GLM_FILE "object switch {\n";
		my $name = $a."_rec";
		print GLM_FILE "\tname $feederName-$name;\n";
		print GLM_FILE "\tphases $recPhase{$sectionDev{$a}};\n";
		print GLM_FILE "\tfrom $feederName-$secFrom{$a};\n"; 	
		print GLM_FILE "\tto $feederName-$temp_node;\n"; 	
		if ( $recST{$sectionDev{$a}} == 1 ) {
			print GLM_FILE "\tstatus CLOSED;\n}\n\n";  
		} else {	
			print GLM_FILE "\tstatus CLOSED;\n}\n\n";  
		}	
		if ( grep{$_ eq $a} @OHSecs ) {
			printOHSecs1($a,$temp_node,"rec");
		}	
		if ( grep{$_ eq $a} @UGSecs ) {
			printUGSecs1($a,$temp_node,"rec");		
		}
	}		
	if ($DevLoc{$sectionDev{$a}} == 2) { #to side
		print GLM_FILE "//Recloser, used as switch for now \n";
		print GLM_FILE "object switch {\n";
		my $name = $a."_rec";
		print GLM_FILE "\tname $feederName-$name;\n";
		print GLM_FILE "\tphases $recPhase{$sectionDev{$a}};\n";
		print GLM_FILE "\tfrom $feederName-$temp_node;\n"; 	
		print GLM_FILE "\tto $feederName-$secTo{$a};\n"; 	
		if ( $recST{$sectionDev{$a}} == 1 ) {
			print GLM_FILE "\tstatus CLOSED;\n}\n\n";  
		} else {	
			print GLM_FILE "\tstatus CLOSED;\n}\n\n";  
		}	
		if ( grep{$_ eq $a} @OHSecs ) {
			printOHSecs2($a,$temp_node,"rec");
		}	
		if ( grep{$_ eq $a} @UGSecs ) {
			printUGSecs2($a,$temp_node,"rec");		
		}		
	}	
}	

sub printrecnode() {
	my $a = shift;
	my $temp_node = $sectionDev{$a}."_recnode";
	print GLM_FILE "object node {\n";
	print GLM_FILE "\tname $feederName-$temp_node;\n";
	print GLM_FILE "\tphases $recPhase{$sectionDev{$a}};\n";
	print GLM_FILE "\tnominal_voltage $VLN;\n";
	print GLM_FILE "}\n\n";	
}	

sub printfuse() {
	my $a = shift;	
	my $temp_node = $sectionDev{$a}."_fusenode";
	if ( grep{$_ eq $a} @UGSecs ) {
	} else {
		if ( grep{$_ eq $a} @OHSecs ) {
		} else {
			print "warning fuse $a connetcted to nowhere!\n";
		}
	}	
	if ($DevLoc{$sectionDev{$a}} == 1) { #from side
		print GLM_FILE "object fuse {\n";
		my $name = $a."_fuse";
		print GLM_FILE "\tname $feederName-$name;\n";
		print GLM_FILE "\tphases $secPhase{$a};\n";
		print GLM_FILE "\tfrom $feederName-$secFrom{$a};\n"; 	
		print GLM_FILE "\tto $feederName-$temp_node;\n"; 	
		print GLM_FILE "\tmean_replacement_time $mean_replacement_time;\n"; 	
		print GLM_FILE "\tcurrent_limit $fuseEquRatedI1{$fuseEquID{$sectionDev{$a}}};\n";
		if ( $fuseST{$sectionDev{$a}} == 1 ) {
			print GLM_FILE "\tstatus CLOSED;\n}\n\n";  
		} else {	
			print GLM_FILE "\tstatus CLOSED;\n}\n\n";  
		}	
		if ( grep{$_ eq $a} @OHSecs ) {
			printOHSecs1($a,$temp_node,"fuse");
		}
		if ( grep{$_ eq $a} @UGSecs ) {	
			printUGSecs1($a,$temp_node,"fuse");		
		}		
	}		
	if ($DevLoc{$sectionDev{$a}} == 2) { #to side
		print GLM_FILE "object fuse {\n";
		my $name = $a."_fuse";
		print GLM_FILE "\tname $feederName-$name;\n";
		print GLM_FILE "\tphases $secPhase{$a};\n";
		print GLM_FILE "\tfrom $feederName-$temp_node;\n"; 	
		print GLM_FILE "\tto $feederName-$secTo{$a};\n"; 	
		print GLM_FILE "\tmean_replacement_time $mean_replacement_time;\n"; 	
		print GLM_FILE "\tcurrent_limit $fuseEquRatedI1{$fuseEquID{$sectionDev{$a}}};\n";		
		if ( $fuseST{$sectionDev{$a}} == 1 ) {
			print GLM_FILE "\tstatus CLOSED;\n}\n\n";  
		} else {	
			print GLM_FILE "\tstatus CLOSED;\n}\n\n";  
		}	
		if ( grep{$_ eq $a} @OHSecs ) {
			printOHSecs2($a,$temp_node,"fuse");
		}	
		if ( grep{$_ eq $a} @UGSecs ) {
			printUGSecs2($a,$temp_node,"fuse");		
		}	
	}	
}	

sub printfusenode() {
	my $a = shift;
	my $temp_node = $sectionDev{$a}."_fusenode";
	print GLM_FILE "object node {\n";
	print GLM_FILE "\tname $feederName-$temp_node;\n";
	print GLM_FILE "\tphases $secPhase{$a};\n";
	print GLM_FILE "\tnominal_voltage $VLN;\n";
	print GLM_FILE "}\n\n";	
}	

sub printSX() {
	my $a = shift;	
	my $temp_node = $sectionDev{$a}."_SXnode";
	if ( grep{$_ eq $a} @UGSecs ) {
	} else {
		if ( grep{$_ eq $a} @OHSecs ) {
		} else {
			print "warning SX $a connetcted to nowhere!\n";
		}
	}	
	if ($DevLoc{$sectionDev{$a}} == 1) { #from side
		print GLM_FILE "object series_reactor {\n";
		my $name = $a."_SX";
		print GLM_FILE "\tname $feederName-$name;\n";
		print GLM_FILE "\tphases $secPhase{$a};\n";
		print GLM_FILE "\tfrom $feederName-$secFrom{$a};\n"; 	
		print GLM_FILE "\tto $feederName-$temp_node;\n"; 	
		print GLM_FILE "\tphase_A_reactance  $SXX{$SXEquID{$sectionDev{$a}}};\n" if ($secPhase{$a} =~ /A/i); 	
		print GLM_FILE "\tphase_B_reactance  $SXX{$SXEquID{$sectionDev{$a}}};\n" if ($secPhase{$a} =~ /B/i); 	 	
		print GLM_FILE "\tphase_C_reactance  $SXX{$SXEquID{$sectionDev{$a}}};\n" if ($secPhase{$a} =~ /C/i); 	 	
		print GLM_FILE "\trated_current_limit $SXEquRatedI1{$SXEquID{$sectionDev{$a}}};\n}\n\n";	
		if ( grep{$_ eq $a} @OHSecs ) {
			printOHSecs1($a,$temp_node,"SX");
		}
		if ( grep{$_ eq $a} @UGSecs ) {	
			printUGSecs1($a,$temp_node,"SX");		
		}		
	}		
	if ($DevLoc{$sectionDev{$a}} == 2) { #to side
		print GLM_FILE "object series_reactor {\n";
		my $name = $a."_SX";
		print GLM_FILE "\tname $feederName-$name;\n";
		print GLM_FILE "\tphases $secPhase{$a};\n";
		print GLM_FILE "\tfrom $feederName-$temp_node;\n"; 	
		print GLM_FILE "\tto $feederName-$secTo{$a};\n"; 	
		print GLM_FILE "\tphase_A_reactance  $SXX{$SXEquID{$sectionDev{$a}}};\n" if ($secPhase{$a} =~ /A/i); 	
		print GLM_FILE "\tphase_B_reactance  $SXX{$SXEquID{$sectionDev{$a}}};\n" if ($secPhase{$a} =~ /B/i); 	 	
		print GLM_FILE "\tphase_C_reactance  $SXX{$SXEquID{$sectionDev{$a}}};\n" if ($secPhase{$a} =~ /C/i); 	 	
		print GLM_FILE "\trated_current_limit $SXEquRatedI1{$SXEquID{$sectionDev{$a}}};\n}\n\n";	
		if ( grep{$_ eq $a} @OHSecs ) {
			printOHSecs2($a,$temp_node,"SX");
		}	
		if ( grep{$_ eq $a} @UGSecs ) {
			printUGSecs2($a,$temp_node,"SX");		
		}	
	}	
}	

sub printSXnode() {
	my $a = shift;
	my $temp_node = $sectionDev{$a}."_SXnode";
	print GLM_FILE "object node {\n";
	print GLM_FILE "\tname $feederName-$temp_node;\n";
	print GLM_FILE "\tphases $secPhase{$a};\n";
	print GLM_FILE "\tnominal_voltage $VLN;\n";
	print GLM_FILE "}\n\n";	
}	

sub printsectionalizer() {
	my $a = shift;
	my $temp_node = $sectionDev{$a}."_sectionalizernode";
	if ($DevLoc{$sectionDev{$a}} == 1) { #from side
		print GLM_FILE "//Sectionalizer, used as switch for now \n";
		print GLM_FILE "object switch {\n";
		my $name = $a."_sw";
		print GLM_FILE "\tname $feederName-$name;\n";
		print GLM_FILE "\tphases $sectionalizerPhase{$sectionDev{$a}};\n";
		print GLM_FILE "\tfrom $feederName-$secFrom{$a};\n"; 	
		print GLM_FILE "\tto $feederName-$temp_node;\n"; 	
		if ( $sectionalizerST{$sectionDev{$a}} == 1 ) {
			print GLM_FILE "\tstatus CLOSED;\n}\n\n";  
		} else {	
			print GLM_FILE "\tstatus CLOSED;\n}\n\n";  #was OPEN, remove floating node for NR
		}	
		if ( grep{$_ eq $a} @OHSecs ) {
			printOHSecs1($a,$temp_node,"sectionalizer");
		}	
		if ( grep{$_ eq $a} @UGSecs ) {
			printUGSecs1($a,$temp_node,"sectionalizer");
		}	
		
	}		
	if ($DevLoc{$sectionDev{$a}} == 2) { #to side
		print GLM_FILE "//Sectionalizer, used as switch for now \n";
		print GLM_FILE "object switch {\n";
		my $name = $a."_sw";
		print GLM_FILE "\tname $feederName-$name;\n";
		print GLM_FILE "\tphases $sectionalizerPhase{$sectionDev{$a}};\n";
		print GLM_FILE "\tfrom $feederName-$temp_node;\n"; 	
		print GLM_FILE "\tto $feederName-$secTo{$a};\n"; 	
		if ( $sectionalizerST{$sectionDev{$a}} == 1 ) {
			print GLM_FILE "\tstatus CLOSED;\n}\n\n";  
		} else {	
			print GLM_FILE "\tstatus CLOSED;\n}\n\n";  #was OPEN, remove floating node for NR
		}	
		if ( grep{$_ eq $a} @OHSecs ) {
			printOHSecs2($a,$temp_node,"sectionalizer");
		}	
		if ( grep{$_ eq $a} @UGSecs ) {	
			printUGSecs2($a,$temp_node,"sectionalizer");
		}			
	}	
}	

sub printsectionalizernode() {
	my $a = shift;
	my $temp_node = $sectionDev{$a}."_sectionalizernode";
	print GLM_FILE "object node {\n";
	print GLM_FILE "\tname $feederName-$temp_node;\n";
	print GLM_FILE "\tphases $sectionalizerPhase{$sectionDev{$a}};\n";
	print GLM_FILE "\tnominal_voltage $VLN;\n";
	print GLM_FILE "}\n\n";	
}	

sub printRegCFG {
	my $a = shift; # regrec
	print GLM_FILE "object regulator_configuration {\n";
	print GLM_FILE "\tname $feederName-$hashRegCFG{$a};\n";
	print GLM_FILE "\tconnect_type WYE_WYE;\n";
	print GLM_FILE "\tband_center $V2nd;\n";
	print GLM_FILE "\tband_width $regBW{$sectionDev{$a}};\n";
	print GLM_FILE "\ttime_delay 30;\n";
	my $tap_r = $regEquTaps{$regEquID{$sectionDev{$a}}}/2;
	print GLM_FILE "\traise_taps $tap_r;\n";
	print GLM_FILE "\tlower_taps $tap_r;\n";
	print GLM_FILE "\tcurrent_transducer_ratio  $regCT{$sectionDev{$a}};\n";
	print GLM_FILE "\tpower_transducer_ratio   $regPT{$sectionDev{$a}};\n";
	print GLM_FILE "\tcompensator_r_setting_A   6.0;\n";
	print GLM_FILE "\tcompensator_r_setting_B   6.0;\n";
	print GLM_FILE "\tcompensator_r_setting_C   6.0;\n";
	print GLM_FILE "\tcompensator_x_setting_A   12.0;\n";
	print GLM_FILE "\tcompensator_x_setting_B   12.0;\n";
	print GLM_FILE "\tcompensator_x_setting_C   12.0;\n";
	print GLM_FILE "\tCT_phase $regPhase{$sectionDev{$a}};\n";
	print GLM_FILE "\tPT_phase $regPhase{$sectionDev{$a}};\n";
	print GLM_FILE "\tregulation 0.10;\n";
	print GLM_FILE "\ttap_pos_A $regTapA{$sectionDev{$a}};\n";
	print GLM_FILE "\ttap_pos_B $regTapB{$sectionDev{$a}};\n";
	print GLM_FILE "\ttap_pos_C $regTapC{$sectionDev{$a}};\n}\n\n";  
}

sub printReg () {
	my $a = shift;
	my $temp_node = $sectionDev{$a}."_regnode";
	# replaced "=" with "_"
	if ( $temp_node =~ /\=|\:/) {
		$temp_node =~ s/\=/\_/;				
		$temp_node =~ s/\:/\_/;
	}
	if ($DevLoc{$sectionDev{$a}} == 1) { #from side
		print GLM_FILE "object regulator {\n";
		my $name = $a."_reg";
		print GLM_FILE "\tname $feederName-$name;\n";
		print GLM_FILE "\tphases $secPhase{$a};\n";
		print GLM_FILE "\tfrom $feederName-$secFrom{$a};\n"; 	
		print GLM_FILE "\tto $feederName-$temp_node;\n"; 	
		print GLM_FILE "\tconfiguration $feederName-$hashRegCFG{$a};\n}\n\n"; 

		# print line
		#$ic = $ic + 1;

		if ( grep{$_ eq $a} @OHSecs ) {
			printOHSecs1($a,$temp_node);
		}	

		if ( grep{$_ eq $a} @UGSecs ) {
			printUGSecs1($a,$temp_node);
		}			
	}		
	if ($DevLoc{$sectionDev{$a}} == 2) { #to side
		print GLM_FILE "object regulator {\n";
		my $name = $a."_reg";
		print GLM_FILE "\tname $feederName-$name;\n";
		print GLM_FILE "\tphases $secPhase{$a};\n";
		print GLM_FILE "\tfrom $feederName-$temp_node;\n"; 	
		print GLM_FILE "\tto $feederName-$secTo{$a};\n"; 	
		print GLM_FILE "\tconfiguration $feederName-$hashRegCFG{$a};\n}\n\n"; 
		if ( grep{$_ eq $a} @OHSecs ) {
			printOHSecs2($a,$temp_node);
		}
		if ( grep{$_ eq $a} @UGSecs ) {	
			printUGSecs2($a,$temp_node);
		}	
	}	
}	

sub printRegnode() {
	my $a = shift;
	my $temp_node = $sectionDev{$a}."_regnode";
	# replaced "=" with "_"
	if ( $temp_node =~ /\=|\:/) {
		$temp_node =~ s/\=/\_/;				
		$temp_node =~ s/\:/\_/;
	}
	print GLM_FILE "object node {\n";
	print GLM_FILE "\tname $feederName-$temp_node;\n";
	#print GLM_FILE "\tphases $secPhase{$sectionDev{$a}};\n";	
	print GLM_FILE "\tphases $secPhase{$a};\n";
	print GLM_FILE "\tnominal_voltage $VLN;\n";
	print GLM_FILE "}\n\n";	
}	

sub printOHSecs() {
	my $temp_sec = shift;
	print GLM_FILE "object overhead_line {\n";
	my $temp_name =$temp_sec."_OH";
	print GLM_FILE "\tname $feederName-$temp_name;\n";
	print GLM_FILE "\tphases $secPhase{$temp_sec};\n";
	print GLM_FILE "\tfrom $feederName-$secFrom{$temp_sec};\n";
	print GLM_FILE "\tto $feederName-$secTo{$temp_sec};\n";
	print GLM_FILE "\tlength $OHLength{$temp_sec};\n";
	my $temp_cfg = $OHCFG{$temp_sec};
	$temp_cfg =~ tr/\./\-/;
	$temp_cfg =~ tr/\:/\-/;
	$temp_cfg =~ s/HORIZONTAL/H/g;
	$temp_cfg =~ s/PINTOP/P/g;
	$temp_cfg =~ s/VERTICAL/V/g;
	$temp_cfg =~ s/SPACERCABLE/S/g;
	print GLM_FILE "\tconfiguration $feederName-$temp_cfg;\n";
	print GLM_FILE "}\n\n";
}	

sub printUGSecs() {
	my $temp_sec = shift;
	print GLM_FILE "object underground_line {\n";
	my $name = $temp_sec."_UG";
	print GLM_FILE "\tname $feederName-$name;\n";
	print GLM_FILE "\tphases $secPhase{$temp_sec};\n";
	print GLM_FILE "\tfrom $feederName-$secFrom{$temp_sec};\n";
	print GLM_FILE "\tto $feederName-$secTo{$temp_sec};\n";
	print GLM_FILE "\tlength $UGLength{$temp_sec};\n";
	my $temp = $name.":".$secPhase{$temp_sec};
	#print GLM_FILE "\tconfiguration $UGCFG{$temp_sec};\n";
	my $temp_cfg = $UGCFG{$temp_sec};
	$temp_cfg =~ tr/\./\-/;
	$temp_cfg =~ tr/\:/\-/;
	print GLM_FILE "\tconfiguration $feederName-$temp_cfg;\n";
	print GLM_FILE "}\n\n";
}

sub printLineCFG() {
	my $temp_cfg = shift;
	my @temp = split (/\:/,$temp_cfg);
	print GLM_FILE "object line_configuration {\n";
	$temp_cfg =~ tr/\./\-/;
	$temp_cfg =~ tr/\:/\-/;
	$temp_cfg =~ s/HORIZONTAL/H/g;
	$temp_cfg =~ s/PINTOP/P/g;
	$temp_cfg =~ s/VERTICAL/V/g;
	$temp_cfg =~ s/SPACERCABLE/S/g;
	
	print GLM_FILE "\tname $feederName-$temp_cfg;\n";
	if ($#temp >4) {
		print GLM_FILE "\tconductor_A $feederName-$temp[0]; \n" if ($temp[-1] =~ /A/i);
		print GLM_FILE "\tconductor_B $feederName-$temp[1]; \n" if ($temp[-1] =~ /B/i);
		print GLM_FILE "\tconductor_C $feederName-$temp[2]; \n" if ($temp[-1] =~ /C/i);
		print GLM_FILE "\tconductor_N $feederName-$temp[3]; \n" if ($temp[-1] =~ /N/i);
	} else {	
		print GLM_FILE "\tconductor_A $feederName-$temp[0]; \n" if ($temp[-1] =~ /A/i);
		print GLM_FILE "\tconductor_B $feederName-$temp[0]; \n" if ($temp[-1] =~ /B/i);
		print GLM_FILE "\tconductor_C $feederName-$temp[0]; \n" if ($temp[-1] =~ /C/i);
		print GLM_FILE "\tconductor_N $feederName-$temp[1]; \n" if ($temp[-1] =~ /N/i);
	}	
	my $temp_spacing = $temp[-2]."_".$temp[-1];
	print GLM_FILE "\tspacing $feederName-$temp_spacing;\n";	
	print GLM_FILE "}\n\n";
}

sub printUGLineCFG() {
	my $temp_cfg = shift;
	my @temp = split (/\:/,$temp_cfg);
	$temp_cfg =~ tr/\./\-/;
	$temp_cfg =~ tr/\:/\-/;	
	print GLM_FILE "object line_configuration {\n";
	print GLM_FILE "\tname $feederName-$temp_cfg;\n";
	print GLM_FILE "\tconductor_A $feederName-$temp[0]; \n" if ($temp[-1] =~ /A/i);
	print GLM_FILE "\tconductor_B $feederName-$temp[0]; \n" if ($temp[-1] =~ /B/i);
	print GLM_FILE "\tconductor_C $feederName-$temp[0]; \n" if ($temp[-1] =~ /C/i);
	print GLM_FILE "\tconductor_N $feederName-$temp[0]; \n" if ($temp[-1] =~ /N/i);
	print GLM_FILE "\tspacing $feederName-$temp[0]_$temp[1]_spacing;\n";	
	print GLM_FILE "}\n\n";
}
	
sub printLineSpacing() {
	my $temp_spacing = shift;
	my @temp = split (/\:/,$temp_spacing );
	my $name = $temp[0]."_".$temp[1];
	print GLM_FILE "object line_spacing {\n";
	print GLM_FILE "\tname $feederName-$name;\n";
	my $dpp;
	my $dpn;
	if ($temp[0] =~ /HORIZONTAL|PINTOP/i) {
		$dpp = 4.6730972;
		$dpn = 6.2040028;
	} elsif ($temp[0] =~ /VERTICAL/i) {	
		$dpp = 5.0396983;
		$dpn = 8.0378939;
	} elsif ($temp[0] =~ /SPACERCABLE/i) {	
		$dpp = 0.6814009;
		$dpn = 0.8275;
	} elsif	($temp[0] eq "") {
		$dpp = 4.6730972;
		$dpn = 6.2040028;
	} else {
		print " ****** warning: cannot find spacing: $temp_spacing\n";
		exit(123);
	}	
	if ( $temp[1] =~ /A/ & $temp[1] =~ /B/ ) {
		print GLM_FILE "\tdistance_AB $dpp ft; \n";	
	} 
	if ( $temp[1] =~ /B/ & $temp[1] =~ /C/ ) {
		print GLM_FILE "\tdistance_BC $dpp ft; \n";	
	}
	if ( $temp[1] =~ /A/ & $temp[1] =~ /C/ ) {
		print GLM_FILE "\tdistance_AC $dpp ft; \n";	
	} 
	if ($temp[1] =~/N/i) {
		print GLM_FILE "\tdistance_AN $dpn ft; \n" if ($temp[1] =~/A/i);
		print GLM_FILE "\tdistance_BN $dpn ft; \n" if ($temp[1] =~/B/i);
		print GLM_FILE "\tdistance_CN $dpn ft; \n" if ($temp[1] =~/C/i);
	}	
	print GLM_FILE "}\n\n";
}	

sub printUGLineSpacing() {
	my $temp_spacing = shift;
	my @temp = split (/\:/,$temp_spacing );
	my $name = $temp[0]."_".$temp[1]."_spacing";
	print GLM_FILE "object line_spacing {\n";
	print GLM_FILE "\tname $feederName-$name;\n";
	if ( $temp[1] =~ /A/ & $temp[1] =~ /B/ ) {
		print GLM_FILE "\tdistance_AB $UGDAB{$temp[0]} in; \n";	
	} 
	if ( $temp[1] =~ /B/ & $temp[1] =~ /C/ ) {
		print GLM_FILE "\tdistance_BC $UGDBC{$temp[0]} in; \n";	
	}
	if ( $temp[1] =~ /A/ & $temp[1] =~ /C/ ) {
		print GLM_FILE "\tdistance_AC $UGDAC{$temp[0]} in; \n";		
	} 
	if ($temp[1] =~/N/i) {
		print GLM_FILE "\tdistance_AN 0; \n" if ($temp[1] =~/A/i);
		print GLM_FILE "\tdistance_BN 0; \n" if ($temp[1] =~/B/i);
		print GLM_FILE "\tdistance_CN 0; \n" if ($temp[1] =~/C/i);
	}	
	print GLM_FILE "}\n\n";
}	

sub printSPCTCFG() {
	my $a = shift; # rating and phase
	my @temp = split (/\:/, $a );
	print GLM_FILE "object transformer_configuration {\n";
	my $temp_cfg = $a;
	$temp_cfg =~ tr/\./\-/;
	$temp_cfg =~ tr/\:/\-/;
	print GLM_FILE "\tname $feederName-$temp_cfg;\n";
	print GLM_FILE "\tconnect_type $single;\n";			
	print GLM_FILE "\tinstall_type $poletop;\n" if ($temp[2] eq 3 ) ;		
	print GLM_FILE "\tinstall_type $padmount;\n" if ($temp[2] eq 1 ) ;	
	print GLM_FILE "\tprimary_voltage $VLN V;\n";
	print GLM_FILE "\tsecondary_voltage $V2nd V;\n";
	print GLM_FILE "\tpower_rating $temp[0];\n";
	print GLM_FILE "\tpower$temp[1]_rating $temp[0];\n";
	my $Rs;
	my $Xs;
	my $Rsh;
	my $Xsh;
	my $itemp;
	if ( exists $NL{$temp[0]} ){
		$Rs = $FL{$temp[0]};		
		$Rsh = sprintf("%.4f", 1/$NL{$temp[0]});		
	} else {
		print " warning, no transformer loss exist for SPCT rating $temp[0] KVA\n" if ($itemp eq 0);
		$itemp = 1;
		if ($temp[0] > 75) {
			$Rs  = 0.015;
			$Rsh = sprintf("%.4f", 1/0.0022);		
			print " set to no-load-loss = 0.0022, full-load-loss = 0.015 \n" if ($iwarning eq 1);
		}
		if ($temp[0] <10) {
			$Rs  = 0.028;
			$Rsh = sprintf("%.4f", 1/0.004);		
			print " set to no-load-loss = 0.004, full-load-loss = 0.028 \n" if ($iwarning eq 1);
		}
	}	
	$Xs = $RXRatio * $Rs;	
	$Xsh = sprintf("%.4f", $RXRatio * $Rsh);
	print GLM_FILE "\timpedance $Rs+$Xs";
	print GLM_FILE "j;\n\tshunt_impedance $Rsh+$Xsh";
	print GLM_FILE "j;\n}\n\n";		
}

sub printWYEWYECFG(){
	my $a = shift;
	my @temp = split (/\:/, $a );
	my $p = $temp[3];
	my $temp_cfg = $a;
	$temp_cfg =~ tr/\./\-/;
	$temp_cfg =~ tr/\:/\-/;
	print GLM_FILE "object transformer_configuration {\n";
	print GLM_FILE "\tname $feederName-$temp_cfg;\n";													     
	print GLM_FILE "\tconnect_type $three;\n";		
	if ($temp[4] eq 3|12 ) {
		print GLM_FILE "\tinstall_type $poletop;\n";		
	} elsif ($temp[4] eq 1 ) {
		print GLM_FILE "\tinstall_type $padmount;\n";		
	} else {
		print "*** warning, cannot recognize install_type $temp[4]\n";
		exist(123);
	}			
	print GLM_FILE "\tprimary_voltage $VLN V;\n";
	print GLM_FILE "\tsecondary_voltage $V2nd V;\n";
	my $temp_KVA = 0;
	$temp_KVA = $temp_KVA + $temp[0] if ($temp[3] =~ /A/i ) ;
	$temp_KVA = $temp_KVA + $temp[1] if ($temp[3] =~ /B/i ) ;
	$temp_KVA = $temp_KVA + $temp[2] if ($temp[3] =~ /C/i ) ;
	$temp_KVA = sprintf("%.1f",$temp_KVA);	
	print GLM_FILE "\tpower_rating $temp_KVA;\n";
	print GLM_FILE "\tpowerA_rating $temp[0];\n" if ($temp[3] =~ /A/i ) ;
	print GLM_FILE "\tpowerB_rating $temp[1];\n" if ($temp[3] =~ /B/i ) ;
	print GLM_FILE "\tpowerC_rating $temp[2];\n" if ($temp[3] =~ /C/i ) ;
	my $Rs;
	my $Xs;
	my $Rsh;
	my $Xsh;
	if ( exists $NL{$temp_KVA} ){
		$Rs = $FL{$temp_KVA};		
		$Rsh = sprintf("%.4f", 1/$NL{$temp_KVA});		
	} else {
		print " warning, no transformer loss exist for WYE_WYE rating $temp[0] KVA\n" if ($iwarning eq 1);
		if ($temp_KVA > 75) {
			$Rs  = 0.015;
			$Rsh = sprintf("%.4f", 1/0.0022);		
			print " set to no-load-loss = 0.0022, full-load-loss = 0.015 \n" if ($iwarning eq 1);
		}
		if ($temp_KVA <10) {
			$Rs  = 0.028;
			$Rsh = sprintf("%.4f", 1/0.004);		
			print " set to no-load-loss = 0.004, full-load-loss = 0.028 \n" if ($iwarning eq 1);
		}
	}	
	$Xs = $RXRatio * $Rs;	
	$Xsh = sprintf("%.4f", $RXRatio * $Rsh);
	print GLM_FILE "\timpedance $Rs+$Xs";
	print GLM_FILE "j;\n\tshunt_impedance $Rsh+$Xsh";
	print GLM_FILE "j;\n}\n\n";		
	
}

sub printSPOTLOAD() {
	my $a = shift;
	my $parent = $a."_M";
	print GLM_FILE "//spotload;\n";
	print GLM_FILE "object load {\n";	
	print GLM_FILE "\tname $feederName-$a;\n";
	print GLM_FILE "\tparent $feederName-$parent;\n";
	print GLM_FILE "\tphases $spotloadPhase{$a};\n";
	print GLM_FILE "\tnominal_voltage $VLN;\n";
	my $temp_loss;
    $sum_spot_KW = $sum_spot_KW + $spotloadKW1{$a}+ $spotloadKW2{$a}+ $spotloadKW3{$a};
	$sum_spot_KVAR = $sum_spot_KVAR + $spotloadKVAR1{$a}+ $spotloadKVAR2{$a}+ $spotloadKVAR3{$a};
	
    if ( $spotloadPhase{$a} =~ /A/i ) {
		if ( exists $FL{$spotloadKVA1{$a}} ) {
			$temp_loss = $spotloadKW1{$a} - $FL{$spotloadKVA1{$a}} ;
		} else {
			#print "warning, spot load $default_fl loss is used for $spotloadKW1{$a} rating xfmr.\n";
			$temp_loss = $spotloadKW1{$a}*(1-$default_fl);
		}
		$temp_loss = $spotloadKW1{$a};
        print GLM_FILE "\tconstant_power_A $temp_loss";
		#print GLM_FILE "\tconstant_power_A $spotloadKW1{$a}";
		if ($spotloadKVAR1{$a} >=0.0) {
			print GLM_FILE "+$spotloadKVAR1{$a}j;\n";
		} else {
			print GLM_FILE "$spotloadKVAR1{$a}j;\n";
		}	
	}	
    if ( $spotloadPhase{$a} =~ /B/i ) {
		if ( exists $FL{$spotloadKVA2{$a}} ) {
			$temp_loss = $spotloadKW2{$a} - $FL{$spotloadKVA2{$a}} ;
		} else {
			#print "warning, spot load $default_fl loss is used for $spotloadKW1{$a} rating xfmr.\n";
			$temp_loss = $spotloadKW2{$a}*(1-$default_fl);
		}
		$temp_loss = $spotloadKW2{$a};
        print GLM_FILE "\tconstant_power_B $temp_loss";
		#print GLM_FILE "\tconstant_power_B $spotloadKW2{$a}";
		if ($spotloadKVAR2{$a} >=0) {
			print GLM_FILE "+$spotloadKVAR2{$a}j;\n";
		} else {
			print GLM_FILE "$spotloadKVAR2{$a}j;\n";
		}
    }
    if ( $spotloadPhase{$a} =~ /C/i ) {
        if ( exists $FL{$spotloadKVA3{$a}} ) {
			$temp_loss = $spotloadKW3{$a} - $FL{$spotloadKVA3{$a}} ;
		} else {
			#print "warning, spot load phase C $default_fl loss is used for $spotloadKW1{$a} rating xfmr.\n";
			$temp_loss = $spotloadKW3{$a}*(1-$default_fl);
		}
		$temp_loss = $spotloadKW3{$a};
        print GLM_FILE "\tconstant_power_C $temp_loss";
		if ($spotloadKVAR3{$a} >=0) {
			print GLM_FILE "+$spotloadKVAR3{$a}j;\n";
		} else {
			print GLM_FILE "$spotloadKVAR3{$a}j;\n";
		}	
	}	
	my $class =  substr $loadClass{$a}, 0, 1;
	$class = "U" if ($class =~/O/i);
	print GLM_FILE "\tload_class $class;\n";
	print GLM_FILE "\t//house_tag $loadClass{$a};\n";
    print GLM_FILE "}\n\n";	
}	

sub printNon_Res() {
	my $a = shift;
	my $parent = $a."_M";	
	#print GLM_FILE "//non_residential;\n";
	print GLM_FILE "object load {\n";	
	print GLM_FILE "\tname $feederName-$a;\n";
	print GLM_FILE "\tparent $feederName-$parent;\n";
	print GLM_FILE "\tphases $non_residential_phase{$a};\n";
	print GLM_FILE "\tnominal_voltage $VLN;\n";

	my $total_KVA = $non_residential_KVA1{$a} + $non_residential_KVA2{$a} + $non_residential_KVA3{$a};
    if ( $non_residential_phase{$a} =~ /A/i ) {
        print GLM_FILE "\tconstant_power_A $non_residential_KW1{$a}";
		if ($non_residential_KVAR1{$a} >=0.0) {
			print GLM_FILE "+$non_residential_KVAR1{$a}j;\n";
		} else {
			print GLM_FILE "$non_residential_KVAR1{$a}j;\n";
		}	
	}	
    if ( $non_residential_phase{$a} =~ /B/i ) {
        print GLM_FILE "\tconstant_power_B $non_residential_KW2{$a}";
		if ($non_residential_KVAR2{$a} >=0.0) {
			print GLM_FILE "+$non_residential_KVAR2{$a}j;\n";
		} else {
			print GLM_FILE "$non_residential_KVAR2{$a}j;\n";
		}	
	}	
    if ( $non_residential_phase{$a} =~ /C/i ) {
        print GLM_FILE "\tconstant_power_C $non_residential_KW3{$a}";
		if ($non_residential_KVAR3{$a} >=0.0) {
			print GLM_FILE "+$non_residential_KVAR3{$a}j;\n";
		} else {
			print GLM_FILE "$non_residential_KVAR3{$a}j;\n";
		}	
	}	
	my $class =  substr $loadClass{$a}, 0, 1;
	$class = "U" if ($class =~ /O/i);	
	print GLM_FILE "\tload_class $class;\n";	
	print GLM_FILE "\t//house_tag $loadClass{$a};\n";
	#print GLM_FILE "\t//no_of_customer $loadnoCust{$a};\n";
    print GLM_FILE "}\n\n";	
}	
	
sub	printMeter($) {
	my $a = shift; #load
	my $name = $a."_M"; #meter name
	print GLM_FILE "object meter {\n";
	print GLM_FILE "\tname $feederName-$name;\n";	
	print GLM_FILE "\tphases $spotloadPhase{$a};\n";	
	print GLM_FILE "\tnominal_voltage $VLN;\n";	
	print GLM_FILE "}\n\n";	
}

sub	printNon_Res_Meter($) {
	my $a = shift; #load
	my $name = $a."_M"; #meter name
	print GLM_FILE "object meter {\n";
	print GLM_FILE "\tname $feederName-$name;\n";	
	print GLM_FILE "\tphases $non_residential_phase{$a};\n";	
	print GLM_FILE "\tnominal_voltage $VLN;\n";	
	print GLM_FILE "}\n\n";	
}

=pod
sub printXFMR($) {
	my $a = shift; # loads	
	my $from = $secTo{$DevSection{$a}};
	my $to = $a."_M";
	my $temp_type = $DevType{$DevSection{$a} };
	my $temp_cfg = $spotloadKVA1{$a}.":".$spotloadKVA2{$a}.":".
		$spotloadKVA3{$a}.":".$spotloadPhase{$a}.":".$temp_type;
	$temp_cfg =~ tr/\./\-/;
	$temp_cfg =~ tr/\:/\-/;
	print GLM_FILE "object transformer  {\n";
	print GLM_FILE "\tphases $spotloadPhase{$a};\n";	
	print GLM_FILE "\tfrom $from;\n";
	print GLM_FILE "\tto $to;\n";			
	print GLM_FILE "\tconfiguration $feederName-$temp_cfg;\n}\n\n";		
}	
	
sub printNon_Res_XFMR($) {
	my $a = shift; # loads	
	my $from = $secTo{$DevSection{$a}};
	my $to = $a."_M";
	my $temp_type = $DevType{$DevSection{$a} };
	my $temp_cfg = $non_residential_KVA1{$a}.":".$non_residential_KVA2{$a}.":"
		.$non_residential_KVA3{$a}.":".$non_residential_phase{$a}.":".$temp_type;	
	$temp_cfg =~ tr/\./\-/;
	$temp_cfg =~ tr/\:/\-/;
	print GLM_FILE "object transformer  {\n";
	print GLM_FILE "\tphases $non_residential_phase{$a};\n";	
	print GLM_FILE "\tfrom $from;\n";
	print GLM_FILE "\tto $to;\n";				
	print GLM_FILE "\tconfiguration $feederName-$temp_cfg;\n}\n\n";		
}	
=cut

sub printLine($) {
	my $a = shift; # loads	
	my $b = $DevSection{$a};		
	my $from = $secTo{$DevSection{$a}};
	my $to = $a."_M";
	my $temp_type = $DevType{$DevSection{$a} };
	my $temp_cfg;
	my $nameOH = $feederName."-".$b."_OH1";
	my $nameUG = $feederName."-".$b."_UG1";
	if ($temp_type eq 1) {
		print GLM_FILE "object underground_line  {\n";
		print GLM_FILE "\tname $nameUG;\n";	
		$temp_cfg = $UGCFG{$b};
	} else {
		print GLM_FILE "object overhead_line  {\n";
		print GLM_FILE "\tname $nameOH;\n";	
		$temp_cfg = $OHCFG{$b};
	}	
	$temp_cfg =~ tr/\./\-/;
	$temp_cfg =~ tr/\:/\-/;
	$temp_cfg =~ s/HORIZONTAL/H/g;
	$temp_cfg =~ s/PINTOP/P/g;
	$temp_cfg =~ s/VERTICAL/V/g;
	$temp_cfg =~ s/SPACERCABLE/S/g;	
	
	print GLM_FILE "\tphases $spotloadPhase{$a};\n";	
	print GLM_FILE "\tfrom $feederName-$from;\n";
	print GLM_FILE "\tto $feederName-$to;\n";			
	print GLM_FILE "\tlength $xfmr_length;\n";
	print GLM_FILE "\tconfiguration $feederName-$temp_cfg;\n}\n\n";		
}	

sub printNon_Res_Line($) {
	my $a = shift; # loads	
	my $b = $DevSection{$a};		
	my $from = $secTo{$DevSection{$a}};
	my $to = $a."_M";
	my $temp_type = $DevType{$DevSection{$a} };
	my $temp_cfg;
	my $nameOH = $feederName."-".$b."_OH2";
	my $nameUG = $feederName."-".$b."_UG2";	
	if ($temp_type eq 1) {
		print GLM_FILE "object underground_line  {\n";
		print GLM_FILE "\tname $nameUG;\n";	
		$temp_cfg = $UGCFG{$b};
	} else {
		print GLM_FILE "object overhead_line  {\n";
		print GLM_FILE "\tname $nameOH;\n";	
		$temp_cfg = $OHCFG{$b};
	}	
	print GLM_FILE "\tphases $non_residential_phase{$a};\n";	
	print GLM_FILE "\tfrom $feederName-$from;\n";
	print GLM_FILE "\tto $feederName-$to;\n";					
	print GLM_FILE "\tlength $xfmr_length;\n";
	$temp_cfg =~ tr/\./\-/;
	$temp_cfg =~ tr/\:/\-/;
	$temp_cfg =~ s/HORIZONTAL/H/g;
	$temp_cfg =~ s/PINTOP/P/g;
	$temp_cfg =~ s/VERTICAL/V/g;
	$temp_cfg =~ s/SPACERCABLE/S/g;	
	print GLM_FILE "\tconfiguration $feederName-$temp_cfg;\n}\n\n";		
}	
	
sub printTN1() {
	my $TN1 = shift; # triplex_node
	my @temp = split (/\:/, $TN1 );
	my $name = $temp[0]."_".$temp[1];
	my @phase = split (/\_/, $temp[1]);
	print GLM_FILE "object triplex_node {\n";
	print GLM_FILE "\tname $feederName-$name;\n";		
	print GLM_FILE "\tphases $phase[0]S;\n";
	print GLM_FILE "\tnominal_voltage $V2nd;\n}\n\n";				
}	

sub printTN ($) {
	my $TN = shift; # triplex_node load
	my @temp = split (/\:/, $TN );
	my $name = $temp[0]."_".$temp[1];
	my @phase = split (/\_/, $temp[1]);
	my $TNM = $name."_tm";
	print GLM_FILE "object triplex_node {\n";
	print GLM_FILE "\tname $feederName-$name;\n";		
	print GLM_FILE "\tphases $phase[0]S;\n";
	print GLM_FILE "\tparent $feederName-$TNM;\n";
	my $temp_loss = $loadKW{$TN};
	if ( $loadKVAR{$TN} >=0 ) {
		print GLM_FILE "\tpower_1 $temp_loss+$loadKVAR{$TN}";
		print GLM_FILE "j;\n";
	} else {	
		print GLM_FILE "\tpower_1 $temp_loss$loadKVAR{$TN}";
		print GLM_FILE "j;\n";
	}	
	$sum_DL_KW = $sum_DL_KW + $loadKW{$TN};
	$sum_DL_KVAR = $sum_DL_KVAR + $loadKVAR{$TN};
	print GLM_FILE "\t//house_tag $loadClass{$TN};\n";
	print GLM_FILE "\t//no_of_customer $loadnoCust{$TN};\n";
	print GLM_FILE "\tnominal_voltage $V2nd;\n}\n\n";				
}	

sub printTM ($) {
	my $TN = shift; # triplex_node load
	my @temp = split (/\:/, $TN );
	my @phase = split (/\_/, $temp[1]);
	my $name = $temp[0]."_".$temp[1];
	my $TNM = $name."_tm";
	print GLM_FILE "object triplex_meter {\n";
	print GLM_FILE "\tname $feederName-$TNM;\n";		
	print GLM_FILE "\tphases $phase[0]S;\n";
	print GLM_FILE "\tnominal_voltage $V2nd;\n}\n\n";				
}	

sub printTL() {
	my $a = shift; # residential
	my @temp = split (/\:/, $a );
	my $temp_to = $temp[0]."_".$temp[1];
	my $from = $temp_to."_tn";	
	my $to = $temp_to."_tm";
	my $name = $temp_to."_TL";
	$triplex_length =  sprintf("%.1f",random_normal($mean,$mean,$sdev/2));
	if ($triplex_length >60) {
		$triplex_length = 60.0;
	}	
	if ($triplex_length <30) {
		$triplex_length = 30.0;
	}
	print GLM_FILE "object triplex_line {\n";
	print GLM_FILE "\tname $feederName-$name;\n";		
	print GLM_FILE "\tphases $temp[1]S;\n";
	print GLM_FILE "\tfrom $feederName-$from;\n";
	print GLM_FILE "\tto $feederName-$to;\n";
	print GLM_FILE "\tlength $triplex_length;\n";
	#print GLM_FILE "\tlength 70;\n";
	print GLM_FILE "\tconfiguration $feederName-TLCFG;\n}\n\n";	
}	

sub printSPCT($) {
	my $a = shift; #residential
	my @temp = split (/\:/, $a );
	my $temp_to = $temp[0]."_".$temp[1];
	my $to = $temp_to."_tn";		
	my $from = $secTo{$DevSection{$temp[0]}};
	my $name = "SPCT_".$ic;
	print GLM_FILE "object transformer {\n";	
	print GLM_FILE "\tname $feederName-$name;\n";
	print GLM_FILE "\tphases $temp[1]S;\n";				
	print GLM_FILE "\tfrom $feederName-$from;\n";
	print GLM_FILE "\tto $feederName-$to;\n";			
	my $temp_cfg = $tn_cfg{$a};
	$temp_cfg =~ tr/\./\-/;
	$temp_cfg =~ tr/\:/\-/;
	print GLM_FILE "\tconfiguration $feederName-$temp_cfg;\n}\n\n";	
}	

sub printCap() {
	my $a = shift; # capacitor
	print GLM_FILE "object capacitor{\n";			
	print GLM_FILE "\tname $feederName-$a;\n";
	my $parent = $secTo{$DevSection{$a}};
	print GLM_FILE "\tparent $feederName-$parent;\n";
	print GLM_FILE "\tphases $capPhase{$a};\n";		
	my $temp_CTR_phase;
	my $temp_CTR;
	if ($capType{$a} == 0 ) {
		$temp_CTR_phase = $capPhase{$a};
		$temp_CTR = "MANUAL";
	}	elsif ($capType{$a} == 3 ) {
		$temp_CTR_phase = $capcurrentPhase{$a};
		$temp_CTR = "CURRENT";
	}	elsif ($capType{$a} == 7 ) {
		$temp_CTR_phase = $capcurrentPhase{$a};
		$temp_CTR = "VOLT";
	}	elsif ($capType{$a} == 2 ) {
		$temp_CTR_phase = $capPhase{$a};
		$temp_CTR = "VAR";
	}	else {
		$temp_CTR_phase = $capPhase{$a};
		$temp_CTR = "MANUAL";
		print " warning: unrecognized capacitor type $capType{$a}, replaced by \"MANUAL\" mode.\n";
	}		
	print GLM_FILE "\tpt_phase $temp_CTR_phase;\n";		
	print GLM_FILE "\tphases_connected $capPhase{$a};\n";		
	print GLM_FILE "\tcontrol $temp_CTR;\n"; 	 	
	print GLM_FILE "\tcapacitor_A $capA{$a} kVAr;\n" if ($capPhase{$a}=~/A/i );
	print GLM_FILE "\tcapacitor_B $capB{$a} kVAr;\n" if ($capPhase{$a}=~/B/i );
	print GLM_FILE "\tcapacitor_C $capC{$a} kVAr;\n" if ($capPhase{$a}=~/C/i );
	print GLM_FILE "\tcontrol_level INDIVIDUAL;\n"; # INDIVIDUAL for now
	my $temp_sec = $DevSection{$a};
	$temp_sec = $temp_sec."_OH" if ( grep{$_ eq $temp_sec} @OHSecs ); 
	$temp_sec = $temp_sec."_UG" if ( grep{$_ eq $temp_sec} @UGSecs );
	print GLM_FILE "\tremote_sense $feederName-$temp_sec;\n" if ($capType{$a} == 3 );	
	print GLM_FILE "\tcurrent_set_high $capcurrentOn{$a};\n" if ($capType{$a} == 3 );
	print GLM_FILE "\tcurrent_set_low $capcurrentOff{$a};\n" if ($capType{$a} == 3 );
	print GLM_FILE "\tremote_sense $feederName-$temp_sec;\n" if ($capType{$a} == 2 );	
	print GLM_FILE "\tVAr_set_high $capvarOn{$a};\n" if ($capType{$a} == 2 );
	print GLM_FILE "\tVAr_set_low $capvarOff{$a};\n" if ($capType{$a} == 2 );
	
	if ($capPhase{$a}=~/A/i ) {
		if ( $capST{$a} == 1 ) {
			print GLM_FILE "\tswitchA OPEN;\n";
		} else {
			print GLM_FILE "\tswitchA CLOSED;\n";
		}	
	}	
	if ($capPhase{$a}=~/B/i ) {
		if ( $capST{$a} == 1 ) {
			print GLM_FILE "\tswitchB OPEN;\n";
		} else {
			print GLM_FILE "\tswitchB CLOSED;\n";
		}	
	}	
	if ($capPhase{$a}=~/C/i ) {
		if ( $capST{$a} == 1 ) {
			print GLM_FILE "\tswitchC OPEN;\n";
		} else {
			print GLM_FILE "\tswitchC CLOSED;\n";
		}	
	}	
	print GLM_FILE "\ttime_delay 2.0;\n";
	print GLM_FILE "\tdwell_time 3.0;\n";
	my $temp = $capEquRatedKVLL{$capEquID{$a}};
	print GLM_FILE "\tcap_nominal_voltage $temp;\n";
	print GLM_FILE "\tnominal_voltage $VLN;\n}\n\n";  	
}	

sub printOHCond() {
	my $temp_OH = shift;
	print GLM_FILE "object overhead_line_conductor {\n";
	print GLM_FILE "\tname $feederName-$temp_OH;\n";
	print GLM_FILE "\trating.summer.continuous $condRating{$temp_OH};\n";
	print GLM_FILE "\tgeometric_mean_radius $condGMR{$temp_OH} cm;\n";			
	print GLM_FILE "\tresistance $condR25{$temp_OH} ohm/km;\n}\n\n";
}	
 
sub	printUGCond() { 
	$a = shift;
	print GLM_FILE "object underground_line_conductor {\n";
	print GLM_FILE "\tname $feederName-$a;\n";
	print GLM_FILE "\trating.summer.continuous $UGRating{$a};\n";
	print GLM_FILE "\touter_diameter $UGOD{$a} in;\n";
	print GLM_FILE "\tconductor_gmr $UGCGMR{$a} in;\n";
	print GLM_FILE "\tconductor_diameter $UGCD{$a} in;\n";
	print GLM_FILE "\tconductor_resistance $UGCR{$a};\n";
	print GLM_FILE "\tneutral_gmr $UGNGMR{$a} in;\n";
	print GLM_FILE "\tneutral_resistance $UGNR{$a};\n";
	print GLM_FILE "\tneutral_diameter $UGND{$a} in;\n";
	print GLM_FILE "\tneutral_strands $UGStrands{$a};\n";
	print GLM_FILE "\tshield_gmr 0.00;\n";
	print GLM_FILE "\tshield_resistance 0.00;\n";
	print GLM_FILE "}\n\n";
}	

sub printTLCond() {
	# create triplex_line_conductor object
	print GLM_FILE "object triplex_line_conductor {\n";
	print GLM_FILE "\tname $feederName-1/0 AA triplex;\n";
	print GLM_FILE "\tresistance 0.97;\n";
	print GLM_FILE "\tgeometric_mean_radius 0.0111;\n}\n\n";
	
	# set triplex_line_configuration id = 1 for now
	print GLM_FILE "object triplex_line_configuration {\n";
	print GLM_FILE "\tname $feederName-TLCFG;\n";
	print GLM_FILE "\tconductor_1 $feederName-1/0 AA triplex;\n";
	print GLM_FILE "\tconductor_2 $feederName-1/0 AA triplex;\n";
	print GLM_FILE "\tconductor_N $feederName-1/0 AA triplex;\n";
	print GLM_FILE "\tinsulation_thickness 0.08;\n";
	print GLM_FILE "\tdiameter 0.368;\n}\n\n";
}	

sub printSubstation_Meter() {
	my $name = "$feederName-Substation_Meter"; 
	print GLM_FILE "object meter {\n";
	print GLM_FILE "\tname $name;\n";	
	print GLM_FILE "\tphases ABCN;\n";	
	print GLM_FILE "\tvoltage_A $VA;\n";
	print GLM_FILE "\tvoltage_B $VB;\n";
	print GLM_FILE "\tvoltage_C $VC;\n";
	print GLM_FILE "\tnominal_voltage $VLN;\n";	
	print GLM_FILE "}\n\n";	
}	

sub printUGSecs1() {
	my $a = shift;
	my $c = shift;	
	my $d = shift;
	my $name = $a."_UG";
	print GLM_FILE "object underground_line {\n";
	print GLM_FILE "\tname $feederName-$name-$d;\n";
	print GLM_FILE "\tphases $secPhase{$a};\n";
	print GLM_FILE "\tfrom $feederName-$c;\n";
	print GLM_FILE "\tto $feederName-$secTo{$a};\n";	
	print GLM_FILE "\tlength $UGLength{$a};\n";
	#print GLM_FILE "\tconfiguration $UGCFG{$a};\n";
	my $temp_cfg = $UGCFG{$a};
	$temp_cfg =~ tr/\./\-/;
	$temp_cfg =~ tr/\:/\-/;
	print GLM_FILE "\tconfiguration $feederName-$temp_cfg;\n";	
	print GLM_FILE "}\n\n";
}

sub printUGSecs2() {
	my $a = shift;
	my $c = shift;
	my $d = shift;
	my $name = $a."_UG";
	print GLM_FILE "object underground_line {\n";
	print GLM_FILE "\tname $feederName-$name-$d;\n";
	print GLM_FILE "\tphases $secPhase{$a};\n";
	print GLM_FILE "\tfrom $feederName-$secFrom{$a};\n";
	#print GLM_FILE "\tto $sectionDev{$a};\n";	
	print GLM_FILE "\tto $feederName-$c;\n";	
	print GLM_FILE "\tlength $UGLength{$a};\n";
	#print GLM_FILE "\tconfiguration $UGCFG{$a};\n";
	my $temp_cfg = $UGCFG{$a};
	$temp_cfg =~ tr/\./\-/;
	$temp_cfg =~ tr/\:/\-/;
	print GLM_FILE "\tconfiguration $feederName-$temp_cfg;\n";	
	print GLM_FILE "}\n\n";
}

sub printOHSecs1() {
	my $a = shift;
	my $c = shift;
	my $d = shift;
	my $name = $a."_OH";	
	print GLM_FILE "object overhead_line {\n";
	print GLM_FILE "\tname $feederName-$name-$d;\n";		
	print GLM_FILE "\tphases $secPhase{$a};\n";
	print GLM_FILE "\tfrom $feederName-$c;\n";
	print GLM_FILE "\tto $feederName-$secTo{$a};\n";
	print GLM_FILE "\tlength $OHLength{$a};\n";
	my $temp_cfg = $OHCFG{$a};
	$temp_cfg =~ tr/\./\-/;
	$temp_cfg =~ tr/\:/\-/;
	$temp_cfg =~ s/HORIZONTAL/H/g;
	$temp_cfg =~ s/PINTOP/P/g;
	$temp_cfg =~ s/VERTICAL/V/g;
	$temp_cfg =~ s/SPACERCABLE/S/g;
	print GLM_FILE "\tconfiguration $feederName-$temp_cfg;\n";
	print GLM_FILE "}\n\n";
}	

sub printOHSecs2() {
	my $a = shift;
	my $c = shift;
	my $d = shift;
	my $name = $a."_OH";	
	print GLM_FILE "object overhead_line {\n";
	print GLM_FILE "\tname $feederName-$name-$d;\n";		
	print GLM_FILE "\tphases $secPhase{$a};\n";
	print GLM_FILE "\tfrom $feederName-$secFrom{$a};\n";
	print GLM_FILE "\tto $feederName-$c;\n";
	print GLM_FILE "\tlength $OHLength{$a};\n";
	my $temp_cfg = $OHCFG{$a};
	$temp_cfg =~ tr/\./\-/;
	$temp_cfg =~ tr/\:/\-/;
	$temp_cfg =~ s/HORIZONTAL/H/g;
	$temp_cfg =~ s/PINTOP/P/g;
	$temp_cfg =~ s/VERTICAL/V/g;
	$temp_cfg =~ s/SPACERCABLE/S/g;	
	print GLM_FILE "\tconfiguration $feederName-$temp_cfg;\n";
	print GLM_FILE "}\n\n";
}	
