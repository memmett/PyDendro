"""PyDendro Stack class."""

class Stack(object):

  def __init__(self, name='', immutable=True):

    self.name = name
    self.immutable = immutable
    self.samples = set()
    self.frozen = False


  def __str__(self):
    return str(self.name)


  def add_sample(self, sample):
    self.samples.add(sample)


  def remove_sample(self, sample):
    self.samples.remove(sample)
  

  def add_samples(self, samples):
    for sample in samples:
      self.samples.add(sample)

