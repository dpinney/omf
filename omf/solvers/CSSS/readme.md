# Contextually Supervised Source Separation (CSSS)
This packages deploys contextually supervised source separation (CSSS) techniques in python. CSSS was originally described by Wytock and Kolter in [P1](http://www.aaai.org/ocs/index.php/AAAI/AAAI14/paper/download/8629/8460) and we follow their original notation in this documentation.  We also include updates and extensions of the original CSSS method as part of our applied work ([P2](https://www.sciencedirect.com/science/article/pii/S2352467717301169),[P3](http://delivery.acm.org/10.1145/3000000/2996419/p259-kara.pdf?ip=73.116.42.185&id=2996419&acc=CHORUS&key=4D4702B0C3E38B35%2E4D4702B0C3E38B35%2E4D4702B0C3E38B35%2E6D218144511F3437&__acm__=1521136405_682443df836c2c91d837ba9d2195493b)). 	

CSSS is the disaggregation of a time series of source signals from observations of their sum. For more detailed information on the methodology and the relevant equations see the ipython notebooks.

## Objects
The CSSS package is built upon the CSSS object class, which allows users to fully specify and fit a problem.

A CSSS object is initialized with only a source signal for disaggregation, in this case the numpy array, Y.
```python
import CSSSpy
CSSSobject = CSSSpy.CSSS(Y)
```

### Attributes
- `models` is a dictionary of models for each component sources.  Adding sources and their properties are addressed below.
- `constraints` is a list of additional constraints. Adding constraints is addressed below.
- `aggregateSignal` is the aggregate signal
- `N` is the number of observations in the aggregate signal.
- `modelcounter` is the total number of source models included.

### Adding Sources
The method CSSS.addSource adds a model for a source signal. By default, the model cost function is the sum of square errors, $\left|\left| y_i - X_i \theta_i \right|\right|_2^2$_, and there is no regularization of the source signal or the parameters. Alternate options for this form (i.e. other norms) will be included in future versions of this package.
```python
CSSSobject.addSource(X1, name = 'y1')  ## Add a model for source signal y1
CSSSobject.addSource(X2, name = 'y2')  ## Add a model for source signal y2
```
The optional parameter `alpha` is a scalar that weights the cost of the signal in the objective function. In the following example, costs associated with the errors in the model for `y1` will be weighted twice that of those for `y2`.

#### Parameter Regularization
The `regularizeTheta` input to `addSource` defines the $h_i()$ term for the source and takes either a string or a function. Strings define standard regularizations and can take "ss" for sum of squares, 'l1' for l1-norms, and 'l2' for l2-norms. `beta` is a parameter for linearly scaling the regularization term in the overall objective function. `beta` may take a scalar or a vector value, if a vector there must be one element for element of $theta_i$.
```python
CSSSobject.addSource(X1, name = 'y1', regularizeTheta='L2', beta = 2)  ## Add a model for source signal y1
```

If inputing a custom function to regularize theta, the function must input a vector of cvxpy variables, and output a scalar that goes into the objective function, and must be convex. The `beta` term can still be used to scale this function.
```python
import cvxpy

def customReg(x):
	cvxpy.sum_entries(cvxpy.power((x-2),2))

CSSSobject.addSource(X1, name = 'y1', regularizeTheta=customReg)  ## Add a model for source signal y1
```

#### Source Regularization
The `regularizeSource` input to `addSource` defines the $g_i()$ term for the source and takes either a string or a function. Strings define standard regularizations and currently only take "diff1_ss" for sum of the squared differenced source signal. `gamma` is a parameter for linearly scaling the regularization term in the overall objective function.
```python
CSSSobject.addSource(X1, name = 'y1', regularizeSource='diff1_ss', beta = .1)  ## Add a model for source signal y1
```

If inputing a custom function to regularize the source, the function must input a vector of cvxpy variables and output a scalar that goes into the objective function, and must be convex. The `gamma` term can still be used to scale this function.
```python
import cvxpy

def customReg(x):
	## Custom regularization function for a source signal with a biased increase
	cvxpy.norm(cvxpy.Diff(x)-.01,1)

CSSSobject.addSource(X1, name = 'y1', regularizeSource=customReg)  ## Add a model for source signal y1
```

#### Anatomy of a source model
The `model` attribute of the `CSSS` object, includes the following fields:
`name`: Name of the model, can be set, or defaults to the source count
`source`: The disaggregated source
`alpha`: Scaling parameter for the $\ell_i()$ function to weight the cost function of residuals.
`lb`: Signifies a lower bound for a box constraint on the source. Default is `None`
`ub`: Signifies an upper bound for a box constraint on the source. Default is `None`
`theta`: Model parameters for the individual source, constructed by `addSource`
`costFunction`: Model cost function as inputted to `addSource`. Currently supports `sse`, `l2` and `l1`
TODO.  Inlcude all attributes of a source, how to acceess the cvxpy variables to add constraints etc.

### Adding Constraints

### Fitting Models

### Distributed Optimization
