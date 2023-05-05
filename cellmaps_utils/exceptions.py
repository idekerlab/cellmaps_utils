# -*- coding: utf-8 -*-


class CellMapsError(Exception):
    """
    Base exception for CellMapsUtils
    """
    pass


class CellMapsProvenanceError(CellMapsError):
    """
    Base exception for provenance errors
    """
    pass
