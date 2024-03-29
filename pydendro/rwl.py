"""PyDendro routines for manipulating RWL files."""

# Copyright (c) 2011, 2012, Matthew Emmett.  All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#   1. Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#   2. Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials provided
#      with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import os

from collections import namedtuple
from shutil import move
from tempfile import mkstemp

class Sample(object):
  """PyDendro (simple) Sample class."""

  def __str__(self):
    return str(self.name)

  def __repr__(self):
    return 'Sample(' + self.__str__() + ')'


  def __init__(self, name, fyog, widths):
    self.name = name
    self.fyog = fyog
    self.widths = widths

  def __iter__(self):
    return (self.name, self.fyog, self.widths).__iter__()


  @property
  def years(self):
    return range(self.fyog, self.fyog+self.nyears)

  @property
  def nyears(self):
    return len(self.widths)

  @property
  def lyog(self):
    return self.fyog + len(self.widths) - 1


def read_text(filename):
  """Read text of file."""
  lines = []
  with open(filename, 'r') as f:
    for line in f:
      lines.append(line.strip())
  return lines


def read(filename, digits=None, **kwargs):
  """Read RWL file and return list of samples."""

  samples      = []
  year         = None
  widths       = []

  lines = read_text(filename)
  last_lineno = len(lines) - 1

  for lineno, line in enumerate(lines):
    if len(line) == 0:
      continue

    if line[7] != ' ':
      line = line[:8] + ' ' + line[8:]

    row = line.split()

    try:
      if year is None:
        # only grab name and year first time around
        name    = str(row[0])
        year    = int(row[1])
    except:
      raise ValueError("Unable to parse file '%s' near line %d." % (filename, lineno+1))

    # append ring widths
    try:
      widths += map(int, row[2:])
    except:
      raise ValueError("Unable to parse file '%s' near line %d." % (filename, lineno+1))

    # are we at the last sample?
    last = widths[-1] < 0 or lineno == last_lineno
    if lineno < last_lineno:
      last = last or not lines[lineno+1].startswith(name)

    if last:

      # renormalize
      if digits:
        d = digits
      else:
        d = len(str(abs(widths[-1])))
      factor = 10.0**(d-1)
      widths = map(lambda x: float(x)/factor, widths[:-1])

      # append to list
      samples.append(Sample(name, year, widths))

      # reset
      year   = None
      widths = []

  return samples


def write(filename, samples, sort=True, key=None, digits=4):
  """Write samples..."""

  if sort:
    if key is None:
      samples = sorted(samples, key=lambda x: x.name)
    else:
      samples = sorted(samples, key=key)

  fd, tmp = mkstemp()

  with os.fdopen(fd, 'wb') as f:
    for sample in samples:
      name, fyog, rws = sample.name, sample.fyog, sample.widths

      # append marker year
      rws = rws + [ 9999.0/10.0**(digits-1) ]

      line = "%-6s  %4d" % (name, fyog)
      for i, year in enumerate(range(fyog, fyog+len(rws))):
        line += "%6d" % int(round(rws[i]*10**(digits-1)))
        if ((year+1) % 10 == 0) and (i < len(rws)-1):
          f.write((line + "\r\n").encode('ascii'))
          line = "%-6s  %4d" % (name, year+1)

      f.write((line + "\r\n").encode('ascii'))

  move(tmp, filename)
