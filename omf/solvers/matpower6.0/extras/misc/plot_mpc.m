function [handle] = plot_mpc(mpc, varargin)
%PLOT_MPC  Plot an electrically meaningful drawing of a MATPOWER case.
%   HANDLE = PLOT_MPC(MPC)
%   HANDLE = PLOT_MPC(MPC, <option1_name>, <option1_value>, ...)
%
%   Examples:
%       plot_mpc('case118', 'MaxBusLabels', 40)
%
%   Plots an electrically meaningful drawing of a MATPOWER case.
%   Higher voltage branches will be drawn using thicker lines. Systems of
%   more than ~300 buses may be very slow to draw.
%
%   Inputs:
%       MPC: a MATPOWER case struct or string with the name of the case file
%       <options>: name, value pairs of options
%           Three optional name/value attribute pairs are available:
%
%           'MaxBusLabels' / integer : This integer sets how many bus numbers
%               to display. Labels are given to the highest voltage level
%               buses first, and progressing down as space permits.
%
%           'DoThevLayout' / boolean : This sets which electrical distance
%               metric to use as a basis for the layout. The default, 0, uses
%               a distance metric based on power transfer distances, which
%               tends to give attractive, legible layouts. Setting this to 1
%               will give a diagram which explicitly shows the effective
%               Thevenin impedance between all bus pairs
%
%           'FigSize' / scalar : The basic image size is 8.89cm by 6.27 cm,
%               which fits the column width of an IEEE journal. This can be
%               scaled up by setting a scaler here, for larger or higher
%               resolution images. The default is 3.
%
%   This function implements visualization techniques described in this paper:
%
%     P. Cuffe; A. Keane, "Visualizing the Electrical Structure of Power
%     Systems," in IEEE Systems Journal, vol.PP, no.99, pp.1-12.
%     DOI: 10.1109/JSYST.2015.2427994
%     http://dx.doi.org/10.1109/JSYST.2015.2427994
%
%   Figures produced using this script can be published freely, however a
%   citation of the above paper would be appreciated.
%
%   Contact:
%     Paul Cuffe, University College Dublin, March 2016
%     paul.cuffe@ucd.ie

%   MATPOWER
%   Copyright (c) 2016, Power Systems Engineering Research Center (PSERC)
%   by Paul Cuffe
%
%   This file is part of MATPOWER.
%   Covered by the 3-clause BSD License (see LICENSE file for details).
%   See http://www.pserc.cornell.edu/matpower/ for more info.


MaxBusLabels=[]; %Maximum number of bus labels to plot - need to limit this to stop clutter
DoThevLayout=[]; %Whether to use Thevenin impedance as the inter-node distance measure, or the power transfer distance measure
FigSize=[]; %The multipier on figure size. Setting = 1 gives a figure with width 8.89 cm, which is equal to the column width for an IEEE publication. Height is set to width / sqrt(2) to maintain pleasing proportions


i=1;
while i <= length(varargin);
  switch (varargin{i});
    case 'MaxBusLabels';
      MaxBusLabels=varargin{i+1}; i=i+2;
    case 'DoThevLayout';
      DoThevLayout = 1; i=i+2;
    case 'FigSize';
      FigSize=varargin{i+1}; i=i+2;
      otherwise;
      error('Unknown option: %s\n',varargin{i}); i=i+1;
  end
end

% If the variables remains empty after the above assignment give them
% defaults
if isempty(MaxBusLabels), MaxBusLabels = 50; end %50 seems a sensible default so things don't get too cluttered
if isempty(DoThevLayout), DoThevLayout =0; end %0 means do power transfer layout
if isempty(FigSize), FigSize=3; end

define_constants;

NumberedSystem = ext2int(runpf(mpc)); %Just in case bus numbers are all out of whack

NumBuses = size(NumberedSystem.bus,1);

        if(NumBuses > 300)
          warning('Large system: layout calculation may be quite slow')
        end
    
    if (DoThevLayout == 1) %Use internode effective impedances as the basis for the projection

        [Ybuspu, Yf, Yt] = makeYbus(NumberedSystem);

        Ybuspu = full(Ybuspu);
        Zbuspu = pinv(Ybuspu);

        ThevMatrix = repmat(diag(Zbuspu),1, NumBuses) + repmat(diag(Zbuspu),1, NumBuses).'  - 2*Zbuspu; %Klein resistance distance formula

        ThevMatrix = ThevMatrix - tril(ThevMatrix); %Force symmetry in case a little numerical noise is preventing us being a strict distance matrix
        ThevMatrix = ThevMatrix + ThevMatrix.';

        [Layout, stressThev] = mdscale(abs(ThevMatrix),2,'criterion','sammon','start','random'); %apply multidimensional scaling to project into two dimensions

    else %Use internode "power transfer distances" as the basis for the projection
    
            TransMatrixMW = zeros(NumBuses); %init with zeros

            for ThisBus = 1:NumBuses % loop through each bus

            CurPTDFMatrix = makePTDF(NumberedSystem.baseMVA, NumberedSystem.bus, NumberedSystem.branch, ThisBus); %calculate the bus-to-branch PTDFs for an injection at every bus absorbed at ThisBus

            TotalBusFlows = sum(abs(CurPTDFMatrix),1); %take ABS value as we're interested in total MW flow shift, regardless of direction

            TransMatrixMW(ThisBus,:) = TotalBusFlows;

            end

        TransMatrixMW = TransMatrixMW - tril(TransMatrixMW); %Force symmetry in case a little numerical noise is preventing us being a strict distance matrix
        TransMatrixMW = TransMatrixMW + TransMatrixMW';
        TransMatrixMW(isnan(TransMatrixMW)) = mean(TransMatrixMW(~isnan(TransMatrixMW))); %Just a hack in case some PTDF calculations haven't been succesful

        [Layout, stressMW] = mdscale(TransMatrixMW,2,'criterion','sammon','start','random');  %apply multidimensional scaling to project into two dimensions
    
    end

BranchVoltages = ( NumberedSystem.bus(NumberedSystem.branch(:, F_BUS), BASE_KV) + NumberedSystem.bus(NumberedSystem.branch(:, T_BUS), BASE_KV) ) / 2; %Divide by two so transformers take on intermediate values

DistinctVoltageLevels = unique([BranchVoltages; NumberedSystem.bus(:, BASE_KV)]);

handle = figure;

cmap = colormap(winter(size(DistinctVoltageLevels,1) + 5));

AllHandles = [];

    for ThisVoltageLevel = 1:size(DistinctVoltageLevels,1) %Run through and draw all the branches first

        BranchesAtThisLevel = find(BranchVoltages == DistinctVoltageLevels(ThisVoltageLevel));
      
            if (~isempty(BranchesAtThisLevel))

            FromBuses = NumberedSystem.branch(BranchesAtThisLevel, F_BUS);
            ToBuses = NumberedSystem.branch(BranchesAtThisLevel, T_BUS);

            LineSegments = [Layout(FromBuses,:), Layout(ToBuses,:)];

            CurrentThickness = ThisVoltageLevel/size(DistinctVoltageLevels,1) * 3;
            
       ThisHandle = line([LineSegments(:,1),LineSegments(:,3)]' , [LineSegments(:,2), LineSegments(:,4)]', 'color', cmap(ThisVoltageLevel + 1, :), 'LineWidth', CurrentThickness*1.5, 'DisplayName', [int2str(DistinctVoltageLevels(ThisVoltageLevel)), ' kV'] );

       AllHandles = [AllHandles; ThisHandle(1)]; %Just take the first sample line from each
       
            hold on;
            end
        
    end


        for ThisVoltageLevel = 1:size(DistinctVoltageLevels,1) %Then draw in buses circles. Doing this in two steps stops unwanted overlaps

        BusesAtThisLevel = find(NumberedSystem.bus(:, BASE_KV) == DistinctVoltageLevels(ThisVoltageLevel));
        
        CurrentThickness = ThisVoltageLevel/size(DistinctVoltageLevels,1) * 3;
        
        hold on;

        scatter(Layout(BusesAtThisLevel,1), Layout(BusesAtThisLevel,2), CurrentThickness * 12, cmap((ThisVoltageLevel + 1),:),'fill','MarkerEdgeColor','w');

        end
    
        RemainingLabelSlots = MaxBusLabels;
        
        for ThisVoltageLevel = size(DistinctVoltageLevels,1):-1:1 %Now start at the highest voltage level and work our way down, labelling bus nodes until we are too cluttered.

        BusesAtThisLevel = find(NumberedSystem.bus(:, BASE_KV) == DistinctVoltageLevels(ThisVoltageLevel));
        
            if(size(BusesAtThisLevel,1) < RemainingLabelSlots)  %For consistency, we should label all buses at a voltage level together, or not at all

        text(Layout(BusesAtThisLevel,1), Layout(BusesAtThisLevel,2), int2str(NumberedSystem.order.bus.i2e(BusesAtThisLevel)), 'FontName', 'Times Roman', 'FontSize', 18, 'HorizontalAlignment','center','VerticalAlignment','top')

        RemainingLabelSlots = RemainingLabelSlots - size(BusesAtThisLevel,1);

            else
               break %Needs to be only the highest voltage buses we label
            end

    end

FigWidth = 8.89 * FigSize; %Size of a column in an IEEE paper
FigHeight = 6.27 * FigSize; %Height/sqrt(2) which is a classicaly nice proportion

set(gcf, 'Units','centimeters', 'Position',[0 0 FigWidth FigHeight])
set(gca, 'Units','centimeters')
set(gca, 'Position',[0 0 FigWidth FigHeight])

set(gcf, 'PaperUnits','centimeters', 'PaperPosition',[(FigWidth * 0.02) (FigHeight * 0.02) (FigWidth * 0.98) (FigHeight * 0.98)])

axis([min(Layout(:,1))*1.05 max(Layout(:,1))*1.05 min(Layout(:,2))*1.1 max(Layout(:,2))*1.02]) %Just give a little breathing room around the edges

axis equal; %it's an electrical map so need consistent scale

set(gca,'YTick',get(gca,'XTick')) %consistent tick interval
set(gca, 'XTickLabelMode', 'manual', 'XTickLabel', []); %no numbers just ticks
set(gca, 'YTickLabelMode', 'manual', 'YTickLabel', []); %no numbers just ticks


%Now put in a legend using the line handles we recorded earlier

    NumHandles = size(AllHandles,1); %Just in case we have too many voltage levels
    
    if(NumHandles > 5) %Limit it to five for clarity's sake
    
    TrimHandles = [AllHandles(1); AllHandles(floor(NumHandles*0.25));AllHandles(floor(NumHandles*0.5));AllHandles(floor(NumHandles*0.75))  ;AllHandles(end)]; %Top and bottom and a few intermediate
    
    else
        TrimHandles = AllHandles;
    end
    
    VoltageLegend = legend(flipud(TrimHandles));
    legend('boxoff');
    
    set(VoltageLegend, 'FontName', 'Times Roman', 'FontSize', 22); %To be consistent with node numbers
    set(VoltageLegend, 'Location', 'best'); %Locate it to not obscure data
