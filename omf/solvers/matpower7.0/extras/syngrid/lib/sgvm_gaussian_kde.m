classdef sgvm_gaussian_kde < handle
%SGVM_GAUSSIAN_KDE multivariate gaussian kde object
%   G = SGVM_GAUSSIAN_KDE(DATASET) creates the kde object G from
%   DATASET. IF DATASET is size N x D, then it contains N observations
%   in D dimensions.
%
%   Essentially a minimal copy of the scipy implementation of a
%   multivariate gaussian just enabling sampling

%   SynGrid
%   Copyright (c) 2018, Power Systems Engineering Research Center (PSERC)
%   by Eran Schweitzer, Arizona State University
%
%   This file is part of SynGrid.
%   Covered by the 3-clause BSD License (see LICENSE file for details).

    properties
        dataset    %(#data, #dims) ie, observations are row vectors
        bw_method
        d          % number of dimentions
        n          % number of samples in data
        factor     % factor multipying the covariance matrix determined by bw_method
        covariance % covariance matrix of dataset scaled by factor
        invcov     % inverse of the covariance matrix
        norm_factor% normalization factor of all individual exponentials
    end
    methods
        function self = sgvm_gaussian_kde(dataset, varargin)
            self.bw_method = sgvm_varargin_parse(varargin,'bw_method', 'scott');

            self.dataset = dataset;
            [self.n, self.d] = size(dataset);
            self.set_bandwidth(self.bw_method)
        end

        function set_bandwidth(self, bw_method)
            if strcmp(bw_method,'scott')
                self.factor = self.n^(-1/(self.d + 4));
            elseif strcmp(bw_method,'silverman')
                self.factor = (self.n*(self.d + 2)/4)^(-1/(self.d + 4));
            elseif isscalar(bw_method)
                self.factor = bw_method;
            else
                error('bw_method should be ''scott'', ''silverman'', or a scalar')
            end
            self.covariance = cov(self.dataset)*self.factor^2;
            self.invcov = inv(cov(self.dataset))/self.factor^2;
            self.norm_factor = sqrt(det(2*pi*self.covariance))*self.n;
        end

        function z = resample(self, n)
            sigma = sgvm_mult_randn(n, self.covariance);
            idx   = randi(self.n, n, 1);
            means = self.dataset(idx,:);
            z = means + sigma;
        end

        function z = single_sample(self, actual_vals, subset)
            if nargin == 1
                actual_vals = false;
            elseif nargin == 2
                subset = 'all';
            end
            if actual_vals
                if strcmp('all', subset)
                    I = randi(self.n);
                else
                    I = subset(randi(length(subset)));
                end
                z = self.dataset(I,:);
            else
                z = self.resample(1);
            end
        end

        function result = evaluate(self, points)
            % evaluate the kde at each of the points given.
            [m, d] = size(points); %#ok<PROPLC>
            if d ~= self.d %#ok<PROPLC>
                error('sgvm_gaussian_kde/evaluate: points array must have as many columns as the kde dimensions')
            end
            
            result = zeros(m, 1);
            if m >= self.n
                % more points than data, loop over data
                for k = 1:self.n
                    df = repmat(self.dataset(k,:), m, 1) - points;
                    tdiff  = self.invcov*df.';
                    energy = sum(df'.*tdiff, 1).'/2;
                    result = result + exp(-energy);
                end
            else
                % loop over points
                for k = 1:m
                    df = self.dataset - repmat(points(k,:), self.n, 1);
                    tdiff = self.invcov*df.';
                    energy = sum(df'.*tdiff, 1).'/2;
                    result(k) = sum(exp(-energy), 1);
                end
            end
            result = result/self.norm_factor;
        end
    end
end
