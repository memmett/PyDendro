"""PyDendro Sample class."""

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


  def from_tuple(self, t):
    self.name = t[0]
    self.first_year = t[1]
    self.ring_widths += t[2]


  @property
  def years(self):
    return range(self.first_year, self.first_year+len(self.ring_widths))

  @property
  def nyears(self):
    return len(self.right_widths)
