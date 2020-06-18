def check_t1x_range(number):
    """
    Check if Brigthness Temperature (Kelvin degrees) values for T10, T11, lie
    inside a reasonable range, eg [200, 330].

    Note, the Digital Number values in bands B10 and B11, are 16-bit. The
    actual data quantisation though is 12-bit.
    """
    if number < 200 or number > 330:
        raise ValueError('The input value {t1x} for T1x is out of a '
                         'reasonable range [200, 330]'.format(t1x=number))
    else:
        return True


def check_cwv(cwv):
    """
    Check whether a column water value lies within a "valid" range. Which is?

    - Questions to answer:

        - What should happen when the value is out of range?
        - Use subrange-6?
        - If yes, how much tolerance for outliers < 0.0 and > 6.3 ?  Testing
          for +-.5

    """
    if cwv < 0.0 - .5 or cwv > 6.3 + .5:
        raise ValueError('The column water vapor estimation is out of the '
                         'expected range [0.0, 6.3]')
    else:
        return True



