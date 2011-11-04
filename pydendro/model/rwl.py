"""PyDendro routines for manipulating RWL files."""

from string import split

def read(filename):
  """Read RWL file and return list of samples as tuples of (name, fyog, widths)."""

  samples      = []
  year         = None
  widths       = []

  with open(filename, 'r') as f:
    for l in f:
      row = split(l)

      if year is None:
        # only grab name and year firt time around
        name    = str(row[0])
        year    = int(row[1])

      widths += map(int, row[2:])       # ring widths

      if int(widths[-1]) < 0:           # last line for this sample

        # renormalize
        digits = len(str(abs(widths[-1])))
        factor = 10.0**(digits-1)
        widths = map(lambda x: float(x)/factor, widths[:-1])

        # append to list
        samples.append((name, year, widths))

        # reset
        year   = None
        widths = []

  return samples


def write(filename, samples, digits=4):
  """Write samples..."""

  # XXX: sorting

  with open(filename, 'w') as f:
    for name, fyog, rws in samples:

      # append marker year
      rws = rws + [ -9999.0/10.0**(digits-1) ]

      line = "%-6s  %4d" % (name, fyog)
      for i, year in enumerate(range(fyog, fyog+len(rws))):
        line += "%6d" % int(round(rws[i]*10**(digits-1)))
        if ((year+1) % 10 == 0) and (i < len(rws)-1):
          f.write(line + "\r\n")
          line = "%-6s  %4d" % (name, year+1)

      f.write(line + "\r\n")
