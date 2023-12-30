# -*- coding: utf-8 -*-
"""
Unified class for DMSP-OLS Inter-Satellite Calibration Model
@author: nik | Created on Wed Mar 11 18:07:20 2015
"""

from intercalibration_coefficients import CITATIONS, COEFFICIENTS
import intercalibration_equations

# globals
DUMMY_MAPCALC_STRING = "Input"
EQUATIONS = intercalibration_equations.main()


class CalibrationModel:
    """
    Common attributes for all models:

    # author: Note, Elvidge's two models require a "version"
        to select which coefficients to use?

    # citation: based on author, hardcoded for each Sub-Class,
        use a _citation method

    # satellite year coefficients: a tuple (pair or triplet, so far) mapcalc
    """

    def __init__(self, author, satellite, year):
        """
        Create object for the calibration model
        """
        # set key for MODEL, MAPCALC, COEFFICIENTS, CITATIONS
        self.author = str(author)

        # get/set input
        self.satellite = satellite
        self.year = str(year)

        # set citation
        self.citation = CITATIONS[self.author]

        # check...
        self.verify_year(author=self.author, satellite=self.satellite, year=self.year)

        # load coefficients and R^2 in tuple, float
        self.set_coefficients()
        self.set_r2()

        # build euqations for model (string) and r.mapcalc
        self.build_model()
        self._mapcalc()

    def __str__(self):
        msg = "Calibration model by ... : "
        msg += "...mode...\n"
        return msg + "  " + self._model + "\n"

    def verify_year(self, author, satellite, year):
        """
        Check if coefficients exist for requested year, satellite, author
        """
        # retrieve years from COEFFICIENTS dictionary
        available_years = COEFFICIENTS[author][satellite].keys()

        # does the requested year exist?
        if year not in available_years:
            raise ValueError(
                "The selected model does not know about "
                "this combination of Satellite + Year!"
            )
        else:
            return True

    def set_coefficients(self):
        """
        Set the model's coefficients for the requested satellite and year
        """
        self.a = COEFFICIENTS[self.author][self.satellite][self.year][0]
        self.b = COEFFICIENTS[self.author][self.satellite][self.year][1]
        self.coefficients = (self.a, self.b)

    def get_coefficients(self):
        """
        Return the model's coefficients for the requested satellite and year
        """
        return (self.a, self.b)

    def set_r2(self):
        """
        Set the R^2 statistic for the requested coefficients
        """
        self.r2 = COEFFICIENTS[self.author][self.satellite][self.year][2]

    def report_r2(self):
        """
        Report the associated R^2 value for the coefficients in question
        """
        msg = "Associated R^2: "
        return msg + str(self.r2)

    def is_dn_valid(self, dn):
        """
        Control whether the given DN is valid
        """
        if not isinstance(dn, int):
            raise ValueError("The provided Digital Number value is NOT an " "integer!")

        if 0 > dn or dn > 63:
            raise ValueError(
                "The provided Digital Number value is out of the "
                "expected range [0,63]"
            )
        else:
            return True

    def build_model(self):
        pass

    # def calibrate(self, dn):
    #     """
    #     Calibrate a clean average visible band Digital Number value
    #     """
    #     model = EQUATIONS[self.author].model  # read equations.py

    # def _mapcalc(self):
    #     """
    #     Retrieve the model's formula for r.mapcalc
    #     """
    #     formula = EQUATIONS[self.author].formula  # read euqations.py

    def get_mapcalc(self):
        return self.mapcalc


class Elvidge(CalibrationModel):
    """
    Empirical second order, DMSP-OLS inter-satellite, calibration model
    proposed by Elvidge, 2009  or  Elvidge, 2014.
    DN adj. = C0 + C1×DN + C2×DN^2
    """

    def __init__(self, satellite, year, version):
        """
        Create object for the polynomial calibration model
        proposed by Elvidge 2009/2014
        """
        # set key for MODEL, MAPCALC, COEFFICIENTS, CITATIONS
        author = str("ELVIDGE")

        # which version of Elvidge's model?
        if not version:
            self.version = "2014"  # alternative coefficients: Elvidge 2009
        else:
            self.version = version

        # set key for COEFFICIENTS
        author += str(self.version)

        # initialise object attributes from the Super-Class
        CalibrationModel.__init__(self, author, satellite, year)

    def _citation(self):
        if self.version == "2014":
            self.citation = self._citation_2014
        elif self.version == "2009":
            self.citation = self._citation_2009

    def __str__(self):
        """
        Return a string representation of the calibration model
        """
        msg = "Calibration model proposed by Elvidge, "
        msg += str(self.version) + "\n  "
        msg += "[DN adj. = C0 + C1\u00D7DN + C2\u00D7DN^2]\n"
        return msg + "  " + self._model + "\n"

    def set_coefficients(self):
        """
        Set coefficients
        """
        self.c0 = COEFFICIENTS[self.author][self.satellite][self.year][0]
        self.c1 = COEFFICIENTS[self.author][self.satellite][self.year][1]
        self.c2 = COEFFICIENTS[self.author][self.satellite][self.year][2]
        self.coefficients = (self.c0, self.c1, self.c2)

    def get_coefficients(self):
        """
        Triplet tuple
        """
        return (self.c0, self.c1, self.c2)

    def set_r2(self):
        """
        set R^2
        """
        self.r2 = COEFFICIENTS[self.author][self.satellite][self.year][3]

    def build_model(self):
        """
        Build model equation, first to serve __str__
        """
        # model = 'DNadj. = ({c0}) + ({c1}) * DN + ({c2}) * DN^2'
        model = EQUATIONS[self.author].model
        self._model = model.format(c0=self.c0, c1=self.c1, c2=self.c2)

    def calibrate(self, dn):
        """
        Calibrate DMSP-OLS NightTime Lights average visible band Digital
        Number values based on Elvidge's calibration polynomial model and
        build a calibration equation for the requested satellite and year.
        """
        if self.is_dn_valid(dn):
            cdn = self.c0 + (self.c1 * dn) + (self.c2 * (dn**2))
        model = EQUATIONS[self.author].model  # look in equations.py
        self._model = model.format(dn=dn, cdn=cdn, c0=self.c0, c1=self.c1, c2=self.c2)
        return cdn

    def _mapcalc(self):
        """
        Return equation for GRASS GIS' mapcalc
        """
        # formula = '{c0} + {c1}*{dummy} + {c2}*{dummy}^2'
        formula = EQUATIONS[self.author].formula  # look in equations.py
        self.mapcalc = formula.format(
            c0=self.c0, c1=self.c1, dummy=DUMMY_MAPCALC_STRING, c2=self.c2
        )


class Liu2012(CalibrationModel):
    """
    Empirical second order calibration model (& optimal threshold method)
    proposed by Liu, 2012.  DNc = a × DN^2 + b × DN + c, where:
    - DNc:
    - DN:
    - a:
    - b:
    - c:
    """

    def __init__(self, satellite, year):
        """
        Create object for the polynomial calibration model
        proposed by Elvidge 2009/2014
        """
        # set key for MODEL, MAPCALC, COEFFICIENTS, CITATIONS
        author = str("LIU2012")

        # initialise object attributes from the Super-Class
        CalibrationModel.__init__(self, author, satellite, year)

    def __str__(self):
        """
        Return a string representation of the calibration model
        """
        msg = "Calibration model by Liu, 2012: "
        msg += "DNc = a \u00D7 DN^2 + b \u00D7 DN + c\n"
        return msg + "  " + self._model + "\n"

    def set_coefficients(self):
        """
        set coefficients
        """
        self.c0 = COEFFICIENTS[self.author][self.satellite][self.year][0]
        self.c1 = COEFFICIENTS[self.author][self.satellite][self.year][1]
        self.c2 = COEFFICIENTS[self.author][self.satellite][self.year][2]
        self.coefficients = (self.c0, self.c1, self.c2)

    def get_coefficients(self):
        """
        # triplet tuple
        """
        return (self.c0, self.c1, self.c2)

    def set_r2(self):
        """
        set R^2
        """
        self.r2 = COEFFICIENTS[self.author][self.satellite][self.year][3]

    def build_model(self):
        # model = 'DNadj. = {c0} + {c1} * DN + {c2} * DN^2'
        model = EQUATIONS[self.author].model
        self._model = model.format(c0=self.c0, c1=self.c1, c2=self.c2)

    def calibrate(self, dn):
        """
        Calibrate DMSP-OLS NightTime Lights average visible band Digital
        Number values based on Elvidge's calibration polynomial model and
        build a calibration equation for the requested satellite and year.
        """
        if self.is_dn_valid(dn):
            cdn = self.c0 + (self.c1 * dn) + (self.c2 * (dn**2))

        # Update _model as well!
        model = "{cdn} = ({c0}) + ({c1}) * {dn} + ({c2}) * {dn}^2"
        self._model = model.format(dn=dn, cdn=cdn, c0=self.c0, c1=self.c1, c2=self.c2)
        return cdn

    def _mapcalc(self):
        """
        Return equation for GRASS GIS' mapcalc
        """
        formula = EQUATIONS[self.author].formula
        print("FORMULA: ", formula)
        self.mapcalc = formula.format(
            c0=self.c0, c1=self.c1, dummy=DUMMY_MAPCALC_STRING, c2=self.c2
        )


class Wu2013(CalibrationModel):
    """
    Power calibration model proposed by Wu 2013.
    DNc + 1 = a × (DN + 1)^b
    Subclass, inheriting from CalibrationModel
    """

    def __init__(self, satellite, year):
        """
        Create object for the power calibration model
        proposed by Wu, 2013
        """
        author = str("WU2013")

        # initialise object attributes from the Super-Class
        CalibrationModel.__init__(self, author, satellite, year)

    def __str__(self):
        """ """
        msg = "Calibration model by Wu, 2013: "
        msg += "DNc + 1 = a \u00D7 (DN + 1)^b\n"
        return msg + "  " + self._model + "\n"

    def build_model(self):
        """ """
        model = EQUATIONS[self.author].model
        self._model = model.format(a=self.a, b=self.b)

    def calibrate(self, dn):
        """
        Calibrate a clean average visible band Digital Number value
        """
        cdn = self.a * (dn + 1) ** self.b

        # Update _model as well!
        model = "{cdn} = {a} * ({dn} + 1)^{b})"
        self._model = model.format(dn=dn, cdn=cdn, a=self.a, b=self.b)
        return cdn

    def _mapcalc(self):
        """ """
        formula = EQUATIONS[self.author].formula
        self.mapcalc = formula.format(a=self.a, dummy=DUMMY_MAPCALC_STRING, b=self.b)


# reusable & stand-alone
if __name__ == "__main__":
    print(
        "Calibration models for DMSP-OLS NightTime Lights Time Series"
        " (Running as stand-alone tool?)\n"
    )
