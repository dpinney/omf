if __package__ in [None, '']:
    import TransformerPairing
    import TransformerPairingWithDist
else:
    from . import TransformerPairing
    from . import TransformerPairingWithDist