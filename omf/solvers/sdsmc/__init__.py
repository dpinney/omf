'''
Adapted from Sandia National Laboratory cade from https://github.com/sandialabs/distribution-system-model-calibration
Original code under a BSD 3-Clause at https://github.com/sandialabs/distribution-system-model-calibration/blob/main/LICENSE
'''

if __package__ in [None, '']:
    import MeterTransformerPairing
    import PhaseIdentification
else:
    from . import MeterTransformerPairing
    from . import PhaseIdentification

def _run_all_tests():
    pass #TODO: maybe add code to test each of the submodules here? I.e. just call some of the functions in the submodules on the existing sample data to make sure they don't crash.
