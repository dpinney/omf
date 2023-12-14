if __package__ in [None, '']:
    import MeterTransformerPairing
else:
    from . import MeterTransformerPairing

def _run_all_tests():
    pass #TODO: maybe add code to test each of the submodules here? I.e. just call some of the functions in the submodules on the existing sample data to make sure they don't crash.
