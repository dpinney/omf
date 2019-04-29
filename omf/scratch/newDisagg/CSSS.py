import numpy as np
import cvxpy as cvp

class CSSS:
### Contextually Supervised Source Seperation Class

    def __init__(self, aggregateSignal):
        self.aggregateSignal  = aggregateSignal
        self.modelcounter     = 0   # Number of source signals
        self.models           = {}  # Model for each source signal, this is a list but could be a dict
        self.constraints      = []  # Additional constraints
        self.N                = len(aggregateSignal) # Length of aggregate signal


    def addSource(self, regressor, name = None,
                  costFunction='sse',alpha = 1,      # Cost function for fit to regressors, alpha is a scalar multiplier
                  regularizeTheta=None, beta = 1,  # Cost function for parameter regularization, beta is a scalar multiplier
                  regularizeSource=None, gamma = 1, # Cost function for signal smoothing, gamma is a scalar multiplier
                  lb=None, # Lower bound on source
                  ub=None, # Upper bound on source
                  idxScrReg=None, # indices used to break the source signal into smaller ones to apply regularization
                  numWind=1, # number of time windows (relevant for time-varying regressors)
                 ):
        ### This is a method to add a new source

        self.modelcounter += 1   # Increment model counter

        ## Write model name if it doesn't exist.
        if name is None:
            name = str(self.modelcounter)

        ## Instantiate a dictionary of model terms
        model = {}
        model['name'] = name
        model['alpha'] = alpha
        model['lb']=lb
        model['ub']=ub

        ## Check regressor shape
        regressor = np.array(regressor)
        if regressor.ndim == 0: ## If no regressors are included, set them an empty array
            regressor = np.zeros((self.N,0))
        if regressor.ndim == 1:
            regressor = np.expand_dims(regressor,1)
        if regressor.ndim > 2:
            raise NameError('Regressors cannot have more than 2 dimensions')


        ## Check that regressors have the correct shape (Nobs, Nregressors)
        if regressor.shape[0] != self.N:
            if regressor.shape[1] == self.N:
                regressor = regressor.transpose()
            else:
                raise NameError('Lengths of regressors and aggregate signal must match')

        ## Define model regressors and order
        model['regressor'] = regressor
        model['order']     = regressor.shape[1]

        ## Define decision variables and cost function style
        model['source']    = cvp.Variable(self.N,1)
        #model['source']    = cvp.Variable((self.N,1)) # required for cvxpy 1.0.1
        model['theta']     = cvp.Variable(model['order'],1)
        #model['theta']     = cvp.Variable((model['order'],1)) # required for cvxpy 1.0.1
        model['costFunction'] = costFunction

        ## Define objective function to fit model to regressors
        if costFunction.lower() == 'sse':
            residuals = (model['source'] - model['regressor'] * model['theta'])
            modelObj =  cvp.sum_squares(residuals) * model['alpha']
        elif costFunction.lower() == 'l1':
            residuals = (model['source'] - model['regressor'] * model['theta'])
            #residuals = (model['source'] - auxVec - model['regressor'] * model['theta'])
            modelObj =  cvp.norm(residuals,1) * model['alpha']
        elif costFunction.lower()=='l2':
            residuals = (model['source'] - model['regressor'] * model['theta'])
            modelObj =  cvp.norm(residuals,2) * model['alpha']
        else:
            raise ValueError('{} wrong option, use "sse","l2" or "l1"'.format(costFunction))
        ## Define cost function to regularize theta ****************
        # ***** ***** ***** ***** ***** ***** ***** ***** ***** ***** ***** *
        # Check that beta is scalar or of length of number of parameters.
        beta = np.array(beta)
        if beta.size not in [1, model['order']]:
            raise ValueError('Beta must be scalar or vector with one element for each regressor')

        if regularizeTheta is not None:
            if callable(regularizeTheta):
                ## User can input their own function to regularize theta.
                # Must input a cvxpy variable vector and output a scalar
                # or a vector with one element for each parameter.

                try:
                    regThetaObj = regularizeTheta(model['theta']) * beta
                except:
                    raise ValueError('Check custom regularizer for model {}'.format(model['name']))
                if regThetaObj.size[0]* regThetaObj.size[1] != 1:
                    raise ValueError('Check custom regularizer for model {}, make sure it returns a scalar'.format(model['name']))

            elif regularizeTheta.lower() == 'l2':
                ## Sum square errors.
                regThetaObj = cvp.norm(model['theta'] * beta)
            elif regularizeTheta.lower() == 'l1':
                regThetaObj = cvp.norm(model['theta'] * beta, 1)
            elif regularizeTheta.lower() == 'diff_l2':
                if numWind==1:
                    regThetaObj = 0
                else:
                    if regressor.shape[1] == numWind: # this actually corresponds to the solar model (no intercept)
                        thetaDiffVec = cvp.diff(model['theta'])
                    else:
                        thetaDiffVec = cvp.vstack(cvp.diff(model['theta'][0:numWind]),cvp.diff(model['theta'][numWind:2*numWind]))
                    regThetaObj = cvp.norm(thetaDiffVec,2) * beta
            elif regularizeTheta.lower() == 'diff_l1':
                if numWind==1:
                    regThetaObj = 0
                else:
                    if regressor.shape[1] == numWind: # this actually corresponds to the solar model (no intercept)
                        thetaDiffVec = cvp.diff(model['theta'])
                    else:
                        thetaDiffVec = cvp.vstack(cvp.diff(model['theta'][0:numWind]),cvp.diff(model['theta'][numWind:2*numWind]))
                    regThetaObj = cvp.norm(thetaDiffVec,1) * beta
        else:
            regThetaObj = 0

        ## Define cost function to regularize source signal ****************
        # ***** ***** ***** ***** ***** ***** ***** ***** ***** ***** ***** *
        # Check that gamma is scalar
        gamma = np.array(gamma)
        if gamma.size != 1:
            raise NameError('Gamma must be scalar')

        ## Calculate regularization.
        if regularizeSource is not None:
            if idxScrReg is not None:
                scrVec = model['source'][0:idxScrReg[0]]
                idxStart = idxScrReg[0]+1
                for idxEnd in idxScrReg[1:]:
                    scrCur = cvp.diff(model['source'][idxStart:idxEnd])
                    scrVec = cvp.vstack(scrVec,scrCur)
                    idxStart = idxEnd+1
                scrVec = cvp.vstack(scrVec,cvp.diff(model['source'][idxStart:]))
            else:
                scrVec = cvp.diff(model['source'])
                
            if callable(regularizeSource):
                ## User can input their own function to regularize the source signal.
                # Must input a cvxpy variable vector and output a scalar.
                regSourceObj = regularizeSource(scrVec) * gamma
            elif regularizeSource.lower() == 'diff1_ss':
                regSourceObj = cvp.sum_squares(scrVec) * gamma
            elif regularizeSource.lower() == 'diff_l1':
                regSourceObj = cvp.norm(scrVec,1) * gamma
            elif regularizeSource.lower() == 'diff_l2':
                regSourceObj = cvp.norm(scrVec,2) * gamma
        else:
            regSourceObj = 0


        ## Sum total model objective
        model['obj'] = modelObj + regThetaObj + regSourceObj

        ## Append model to models list
        self.models[name]= model

    def addConstraint(self, constraint):
        ### This is a method to add a new source
        self.constraints.append(constraint)

    def constructSolve(self, Solver='ECOS', Verbose=False, Max_iters=100):
        ## This method constructs and solves the optimization

        ## Initialize objective function and modeled aggregate signal as 0
        obj = 0
        sum_sources = np.zeros((self.N,1))

        ## Initialize constraints as those custom created
        con = self.constraints

        ## For each model
        #    - Add cost to objective function
        #    - Add source to sum of sources
        #    - (TODO) Add custom constraints for each source
        for name, model in self.models.items():
            obj = obj + model['obj']
            sum_sources = sum_sources + model['source']
            ### ADD lb and ub constraints on individual source signal.
            if model['lb'] is not None:
                con.append(model['source'] >= model['lb'])
            if model['ub'] is not None:
                con.append(model['source'] <= model['ub'])


        ## Append the constraint that the sum of sources must equal aggergate signal
        #self.aggregateSignal.shape=(len(self.aggregateSignal),1) # required for cvxpy 1.0.1
        con.append(self.aggregateSignal == sum_sources)

        ## Solve problem
        prob = cvp.Problem(cvp.Minimize(obj), con)
        if (Solver=='MOSEK'):
            prob.solve(solver=Solver, verbose=Verbose)
        else:
            prob.solve(solver=Solver, verbose=Verbose, max_iters=Max_iters)
        return prob