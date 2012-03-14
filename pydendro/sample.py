"""PyDendro Sample class."""
# Copyright (c) 2011, Matthew Emmett.  All rights reserved.
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


class Sample(object):
  """PyDendro Sample class.

  A sample is a collection of ring widths.
  """

  def __str__(self):
    return str(self.name)
    

  def __init__(self):
    self.name = None
    self.first_year = None
    self.ring_widths = []
    self.oiginal_first_year = None


  def from_plain(self, sample):
    self.name = sample.name
    self.first_year = sample.fyog
    self.ring_widths += sample.widths
    self.original_first_year = self.first_year

  def to_plain(self):
    from rwl import Sample as PlainSample
    sample = PlainSample
    sample.name = self.name
    sample.fyog = self.first_year
    sample.widths = self.ring_widths
    return sample

  @property
  def years(self):
    return range(self.first_year, self.first_year+len(self.ring_widths))

  @property
  def nyears(self):
    return len(self.right_widths)
