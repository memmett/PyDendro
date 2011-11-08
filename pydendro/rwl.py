"""PyDendro routines for manipulating RWL files."""

from string import split

def _as_tuple(sample):

  if isinstance(sample, list):
    if len(sample) == 3:
      name = sample[0]
      if isinstance(sample[1], int):
        fyog = sample[1]
      else:
        fyog = sample[1][0]
      rws = list(sample[2])

      return (name, fyog, rws)


  raise ValueError('Unable to transform sample: format not understood.')


def _as_tuples(samples, sort=False):

  if isinstance(samples, list):
    if isinstance(samples[0], tuple):
      pass

  elif isinstance(samples, dict):
    key = samples.keys()[0]
    if isinstance(key, int):
      r = []
      for sample in samples.values():
        r.append(_as_tuple(sample))
      samples = r
    else:
      pass

  else:
    raise ValueError('Unable to tranform samples: format not understood.')

  if sort:
    return sorted(samples, key=lambda x: x[0])

  return samples


def _transform_sample(sample, pairing, years, ring_widths, include_name):
  name, fyog, rws = sample

  if years == 'fyog':
    years = fyog
  elif years == 'list':
    years = range(fyog, fyog+len(rws))
  elif years == 'array':
    import numpy as np
    years = np.array(range(fyog, fyog+len(rws)), dtype=np.int)
  else:
    raise ValueError('Unable to transform sample: year format "%s" not understood.' % years)

  if ring_widths == 'list':
    pass
  elif ring_widths == 'array':
    import numpy as np
    rws = np.array(rws)
  else:
    raise ValueError('Unable to transform sample: ring width format "%s" not understood.' % ring_widths)    

  if pairing == 'list':
    if include_name:
      return [name, years, rws]
    else:
      return [years, rws]
  else:
    raise ValueError('Unable to transform sample: pairing "%s" not understood.' % pairing)


def transform(samples,
              kind='dictionary',
              key='name',
              pairing='list', years='fyog', ring_widths='list'):
  """XXX"""

  if kind == 'dictionary':
    if key == 'enumerated':

      d = {}
      for i, sample in enumerate(_as_tuples(samples, sort=True)):
        d[i] = _transform_sample(sample, pairing, years, ring_widths, True)
      return d

    elif key == 'name':
      pass
    else:
      raise ValueError('Unable to transform samples: key "%s" not understood.' % key)
  else:
    raise ValueError('Unable to transform samples: kind "%s" not understood.' % kind)


def read(filename):
  """Read RWL file and return list of samples as tuples of (name, fyog, widths)."""

  samples      = []
  year         = None
  widths       = []

  with open(filename, 'r') as f:
    for l in f:
      if len(l.strip()) == 0:
        continue

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


def write(filename, samples, sort=True, digits=4):
  """Write samples..."""

  samples = _as_tuples(samples, sort=sort)

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
