import random


def random_digital_numbers(count=2):
    """
    Return a user-requested amount of random Digital Number values for testing
    purposes ranging in 12-bit
    """
    digital_numbers = []

    for dn in range(0, count):
        digital_numbers.append(random.randint(1, 2**12))

    if count == 1:
        return digital_numbers[0]

    return digital_numbers


def random_column_water_vapor_subrange():
    """
    Helper function, while coding and testing, returning a random column water
    vapor key to assist in testing the module.
    """
    cwvkey = random.choice(COLUMN_WATER_VAPOUR.keys())
    # COLUMN_WATER_VAPOUR[cwvkey].subrange
    # COLUMN_WATER_VAPOUR[cwvkey].rmse
    return cwvkey


def random_column_water_vapor():
    """
    Return a rational number ranging in [0.0, 6.3] to assisst in selecting
    an atmospheric column water vapor subrange, as part of testing the
    Split-WindowLST class.
    """
    return random.uniform(0.0 - 1, 6.3 + 1)


def random_column_water_vapor_value():
    """
    Helper function, while coding and testing, returning a random value for
    column water vapor.
    """
    return random.uniform(0.0, 6.3)


def random_adjacent_pixel_values(pixel_modifiers):
    """
    Parameters
    ----------
    pixel_modifiers
        List of pixel modifiers as expected by GRASS GIS' r.mapcalc module

    Returns
    -------
    A list of random adjacent integer pixel values ranging in [250, 350) deg.
    Kelvin
    """
    import random

    return [random.randint(250, 350) for dummy_idx in range(len(pixel_modifiers))]


def random_window_size():
    """ """
    return random.randint(7, 21)


def random_adjacent_pixel_values(pixel_modifiers):
    """ """
    return [random.randint(250, 350) for dummy_idx in range(len(pixel_modifiers))]


def random_brightness_temperature_values(count=2):
    """
    Return a user-requested amount of random Brightness Temperature values for testing
    purposes ranging in [250, 330].
    """
    digital_numbers = []

    for dn in range(0, count):
        digital_numbers.append(random.randint(250, 330))

    if count == 1:
        return digital_numbers[0]

    return digital_numbers
