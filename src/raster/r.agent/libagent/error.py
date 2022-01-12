"""
MODULE:       r.agent.*
AUTHOR(S):    michael lustenberger inofix.ch
PURPOSE:      library file for the r.agent.* suite
COPYRIGHT:    (C) 2011 by Michael Lustenberger and the GRASS Development Team

              This program is free software under the GNU General Public
              License (>=v2). Read the file COPYING that comes with GRASS
              for details.
"""


class Error(Exception):
    """Base class for exceptions in this module.

    Attributes:
        expr -- Context expression in which the error occurred
        msg  -- explanation of the error
    """

    def __init__(self, expr, msg):
        self.expr = expr
        self.msg = msg

    def __str__(self):
        return self.expr + " '" + self.msg + "'"


class EnvError(Error):
    """Exception raised for missing GRASS environment.

    Attributes:
        expr -- Context expression in which the error occurred
        msg  -- explanation of the error
    """


class DataError(Error):
    """Exception raised for errors in the input.

    Attributes:
        expr -- Context expression in which the error occurred
        msg  -- explanation of the error
    """
