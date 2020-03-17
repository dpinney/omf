SynGrid
=======

Synthetic Grid Creation for MATPOWER
------------------------------------

[SynGrid][1] is a package of MATLAB/Octave M-files for creating completely
synthetic power system models for use with [MATPOWER][2]. SynGrid is based on
code written by Dr. Zhifang Wang and her group, including Seyyed Hamid Elyas
and Hamidreza Sadeghian at Virginia Commonwealth University, and further
developed as part of the ["Synthetic Data for Power Grid R & D" project][3]
under the [ARPA-E Grid Data][3b] program in conjunction with Ray Zimmerman
from Cornell University. SynGrid builds upon previous work [[1][11], [2][7]]
by Wang, Scaglione, and Thomas as well as more the more recent works listed
in the "Publications" section below.


System Requirements
-------------------

*   [MATPOWER][2] version 7 or later
    
    _See the [MATPOWER website][2] for the system requirements for
    MATPOWER. For use on Octave, SynGrid's variations mode requires
    Octave 4.2 or later._


Installation
------------

1.  There are 3 primary ways to install SynGrid.

    - **Option 1** - Install MATPOWER 7 or later by downloading a zip file
      from the [MATPOWER website][2] and running the MATPOWER installer.
      SynGrid is included and should also be installed.

    - **Option 2** - Install MATPOWER from the [MATPOWER GitHub][4] and then
       install the [MATPOWER Extras][5] (which include SynGrid) manually, as
       described on the [matpower-extras GitHub page][5].

    - **Option 3** - Install SynGrid manually.

        - Clone the repository or download and extract the zip file of
          the SynGrid distribution from the [SynGrid project page][1] to
          the location of your choice. The files in the resulting
          `mx-syngrid` or `mx-syngridXXX` directory, where `XXX` depends
          on the version of SynGrid, should not need to be modified, so it
          is recommended that they be kept separate from your own code.
          We will use `<SYNGRID>` to denote the path to this directory.

        - Add the following directories to your MATLAB or Octave path:
            *   `<SYNGRID>/lib`
            *   `<SYNGRID>/lib/t`

3.  At the MATLAB prompt, type `test_syngrid` to run the test suite and
    verify that SynGrid is properly installed and functioning. The result
    should resemble the following:

```matlab
    >> test_syngrid
    t_sg_options.........ok
    t_sgvm_add_shunts....ok
    t_sgvm_data2mpc......ok
    t_syngrid............ok
    t_syngrid_vm.........ok
    All tests successful (174 of 174)
    Elapsed time 173.16 seconds.
```


Usage
-----

To use SynGrid to create a synthetic 100-bus MATPOWER case and run a DC power
flow with it, simply type:

```matlab
    >> mpc = syngrid(100);
    >> results = rundcpf(mpc);
```

To specify options for SynGrid, such as progress output and loading level:

```matlab
    >> sgopt = sg_options('verbose', 1, 'bm.loading', 'H');
    >> mpc = syngrid(100, sgopt);
```

And to save the resulting MATPOWER case to a file named `'my_syn_case100.m'`:

```matlab
    >> mpc = syngrid(100, opt, 'my_syn_case100');
```


Documentation
-------------

There are two primary sources of documentation for SynGrid. The first is
the [SynGrid User's Manual][6], which gives an overview of the capabilities
and structure of SynGrid. It can be found in your SynGrid distribution at
`<SYNGRID>/docs/SynGrid-manual.pdf` and the latest version is always
available at:
<https://github.com/MATPOWER/mx-syngrid/blob/master/docs/SynGrid-manual.pdf>.

And second is the built-in `help` command. As with the built-in
functions and toolbox routines in MATLAB and Octave, you can type `help`
followed by the name of a command or M-file to get help on that particular
function. All of the M-files in SynGrid have such documentation and this
should be considered the main reference for the calling options for the
top-level function, namely: `syngrid`.


Publications
------------

1.  Z. Wang, R. J. Thomas and A. Scaglione, ["Generating Random Topology
    Power Grids,"][11] *Proceedings of the 41st Annual Hawaii International
    Conference on System Sciences (HICSS 2008)*, Waikoloa, HI, 2008,
    pp. 1-9.  
    doi: [10.1109/HICSS.2008.182][11]

2.  Z. Wang, A. Scaglione and R. J. Thomas, ["Generating Statistically
    Correct Random Topologies for Testing Smart Grid Communication and
    Control Networks,"][7] *Smart Grid, IEEE Transactions on*, vol. 1,
    no. 1, pp. 28-39, June 2010.  
    doi: [10.1109/TSG.2010.2044814][7]

3.  Z. Wang and R. J. Thomas, ["On Bus Type Assignments in Random Topology
    Power Grid Models,"][12] *2015 48th Hawaii International Conference on
    System Sciences*, Kauai, HI, 2015, pp. 2671-2679.  
    doi: [10.1109/HICSS.2015.322][12]

4.  Z. Wang, S. H. Elyas, ["On the Scaling Property of Power Grids,"][13]
    *Proceedings of the 50st Annual Hawaii International Conference on
    System Sciences (HICSS 2017)*, Waikoloa, HI, 2017, pp. 3148-3155.  
    doi: [10.24251/HICSS.2017.381][13]

5.  S. H. Elyas and Z. Wang, ["Improved Synthetic Power Grid Modeling
    With Correlated Bus Type Assignments,"][8] *Power Systems, IEEE
    Transactions on*, vol. 32, no. 5, pp. 3391-3402, Sept. 2017.  
    doi: [10.1109/TPWRS.2016.2634318][8].

6.  S. H. Elyas, Z. Wang, R. J. Thomas, ["On the Statistical Settings of
    Generation Capacities and Dispatch in a Synthetic Grid Modeling,"][14]
    *10th Bulk Power Systems Dynamics and Control Symposium (IREP'2017)*,
    Espinho, Portugal, Aug 27--Sep 1, 2017.

7.  H.~Sadeghian, S. H.~Elyas, Z.~Wang, ["A Novel Algorithm for Statistical
    Assignment of Transmission Capacities in Synthetic Grid Modeling,"][15]
    *2018 IEEE PES General Meeting*, Portland, OR, Aug 5-9, 2018.  
    doi: [10.1109/PESGM.2018.8585532][15]

8.  Z. Wang, M. H. Athari, S. H. Elyas, ["Statistically Analyzing Power
    System Network,"][16] *2018 IEEE PES General Meeting*, Portland, OR,
    Aug 5-9, 2018.  
    doi: [10.1109/PESGM.2018.8586110][16]

9.  E. Schweitzer, A. Scaglione, ["A Mathematical Programing Solution
    for Automatic Generation of Synthetic Power Flow Cases,"][17] *Power
    Systems, IEEE Transactions on*, 2018.  
    doi: [10.1109/TPWRS.2018.2863266][17]


[Citing SynGrid][18]
--------------------

We request that publications derived from the use of SynGrid explicitly
acknowledge that fact by citing one or more of the following references:

>   Z. Wang, A. Scaglione and R. J. Thomas, "Generating Statistically
    Correct Random Topologies for Testing Smart Grid Communication and
    Control Networks," *Smart Grid, IEEE Transactions on*, vol. 1,
    no. 1, pp. 28-39, June 2010.  
    doi: [10.1109/TSG.2010.2044814][7]

>   S. H. Elyas and Z. Wang, "Improved Synthetic Power Grid Modeling
    With Correlated Bus Type Assignments," *Power Systems, IEEE
    Transactions on*, vol. 32, no. 5, pp. 3391-3402, Sept. 2017.  
    doi: [10.1109/TPWRS.2016.2634318][8]

>   E. Schweitzer, A. Scaglione, "A Mathematical Programing Solution
    for Automatic Generation of Synthetic Power Flow Cases," *Power
    Systems, IEEE Transactions on*, 2018.  
    doi: [10.1109/TPWRS.2018.2863266][17]

The [SynGrid User's Manual][6] should also be cited explicitly in work that
refers to or is derived from its content. The citation and DOI can be
version-specific or general, as appropriate. For version 1.0.1, use:

>   Z. Wang, H. Sadeghian, S. H. Elyas, R. D. Zimmerman, E. Schweitzer,
    A. Scaglione. *SynGrid User's Manual, Version 1.0.1*. 2019. [Online].
    Available: https://matpower.org/docs/SynGrid-manual-1.0.1.pdf  
    doi: [10.5281/zenodo.3251099](https://doi.org/10.5281/zenodo.3251099)

For a version non-specific citation, use the following citation and DOI,
with *\<YEAR\>* replaced by the year of the most recent release:

>   Z. Wang, H. Sadeghian, S. H. Elyas, R. D. Zimmerman, E. Schweitzer,
    A. Scaglione. *SynGrid User's Manual*. *\<YEAR\>*. [Online].
    Available: https://matpower.org/docs/SynGrid-manual.pdf  
    doi: [10.5281/zenodo.3238679][19]

A list of versions of the User's Manual with release dates and
version-specific DOI's can be found via the general DOI at
https://doi.org/10.5281/zenodo.3238679.


Contributing
------------

Please see the [MATPOWER contributing guidelines][9] for details on how to
contribute to the project or report issues.

License
-------

SynGrid is distributed under the [3-clause BSD license][10].

----
[1]: https://github.com/MATPOWER/mx-syngrid
[2]: https://matpower.org
[3]: https://arpa-e.energy.gov/?q=slick-sheet-project/synthetic-data-power-grid-rd
[3b]: https://arpa-e.energy.gov/?q=arpa-e-programs/grid-data
[4]: https://github.com/MATPOWER/matpower
[5]: https://github.com/MATPOWER/matpower-extras
[6]: docs/SynGrid-manual.pdf
[7]: https://doi.org/10.1109/TSG.2010.2044814
[8]: https://doi.org/10.1109/TPWRS.2016.2634318
[9]: https://github.com/MATPOWER/matpower/blob/master/CONTRIBUTING.md
[10]: LICENSE
[11]: https://doi.org/10.1109/HICSS.2008.182
[12]: https://doi.org/10.1109/HICSS.2015.322
[13]: https://doi.org/10.24251/HICSS.2017.381
[14]: https://arxiv.org/abs/1706.09294
[15]: https://doi.org/10.1109/PESGM.2018.8585532
[16]: https://doi.org/10.1109/PESGM.2018.8586110
[17]: https://doi.org/10.1109/TPWRS.2018.2863266
[18]: CITING
[19]: https://doi.org/10.5281/zenodo.3238679
