"""PyDendro model/state class."""

import os, os.path, string

from pydendro import rwl
from pydendro.sample import Sample
from pydendro.stack import Stack

# special stacks: master, working
# flags: done, frozen



class PyDendroModel(object):

  def __init__(self):

    self.ui = None
    self._stacks = {}
    self._samples = {}

    self.normalization = None


  def add_stack(self, stack):
    """Add a new stack object."""
    
    self._stacks[stack.name] = stack


  def add_sample(self, sample):
    """Add a new sample object."""
    
    self._samples[sample.name] = stack


  @property
  def stacks(self):
    """Return list of stack names."""

    return self._stacks.keys()


  def get_stack(self, name):
    """Return stack object given stack name."""

    return self._stacks[name]


  @property
  def samples(self):
    """Return list of sample names."""

    return self._samples.keys()


  def get_sample(self, name):
    """Return sample object given sample name."""

    return self._samples[name]


  def samples_in_stack(self, stack):
    """Return list of samples in stack."""
    
    return list(self._stacks[stack].samples)
  

  def move_sample(self, source, sample, destination):
    """Move sample from source stack to destination stack."""

    try:
      src = self._stacks[source]
      dst = self._stacks[destination]
      dst.add_sample(sample)
      src.remove_sample(sample)
    except:
      pass


  def copy_sample(self, source, sample, destination):
    """Copy sample from source stack to destination stack."""
    
    try:
      src = self._stacks[source]
      dst = self._stacks[destination]
      dst.add_sample(sample)
    except:
      pass


  def add_stack_from_rwl(self, filename):
    """Create a new from an RWL file."""
    
    stack_name = string.split(os.path.basename(filename), '.')[0]

    # check stack name
    if stack_name in self._stacks:
      self.ui.warning("Duplicate stack",
                      "Stack %s already exists.  Skipping import." % stack_name)
      return

    # load samples
    samples = []
    for s in rwl.read(filename):
      sample = Sample()
      sample.from_tuple(s)
      samples.append(sample)

    # check samples
    for sample in samples:
      if str(sample) in self._samples:
        self.ui.warning("Duplicate sample",
                        "Sample %s already exists.  Skipping import." % str(sample))
        return

    # add samples
    for sample in samples:
      self._samples[str(sample)] = sample

    # add stack
    stack = Stack()
    stack.name = stack_name
    stack.add_samples(map(lambda x: str(x), samples))
    self.add_stack(stack)

    return stack


  
    
