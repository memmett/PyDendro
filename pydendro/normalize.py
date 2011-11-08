"""Ring width normalization routines."""


import numpy as np

def proportion_of_last_two_years(rws):
  """\
  Normalize ring widths using the proportion of the last two years
  of growth.

  For example:

    rw[2010] = rw[2010]/(rw[2010] + rw[2009])

  """

  rws = np.array(rws)

  return rws[1:]/(rws[1:] + rws[:-1])


def average(rws):
  """\
  Normalize ring widths by their average.
  """

  rws = np.array(rws)

  return rws/np.mean(rws)
