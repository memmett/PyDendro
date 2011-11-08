"""PyDendro model/state class."""
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


import os, os.path, string

from pydendro import rwl
from pydendro.sample import Sample
from pydendro.stack import Stack


class PyDendroModel(object):

  def __init__(self):

    self.ui = None
    self._stacks = {}
    self._samples = {}

    self.normalization = None


  def add_stack(self, stack):
    """Add a new stack object."""
    
    if stack.name not in self._stacks and stack.name != 'TRASH':
      self._stacks[stack.name] = stack
    else:
      raise ValueError('stack already exists')


  def remove_stack(self, stack):
    """Remove a stack."""
    
    if stack != 'TRASH':
      try:
        del self._stacks[stack]
      except:
        pass


  def rename_stack(self, old, new):
    """Rename a stack."""
    
    if new not in self._stacks and new != 'TRASH':
      try:
        self._stacks[new] = self._stacks[old]
        del self._stacks[old]
      except:
        pass
    else:
      raise ValueError('stack already exists')


  def add_sample(self, sample):
    """Add a new sample object."""
    
    self._samples[sample.name] = sample


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

    if destination == 'TRASH':
      try:
        src = self._stacks[source]
        src.remove_sample(sample)
      except:
        pass

      return

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


  # def delete_sample(self, source, sample, destination):
  #   """Copy sample from source stack to destination stack."""
    
  #   try:
  #     src = self._stacks[source]
  #     src.remove_sample(sample)
  #   except:
  #     pass


  def add_stack_from_rwl(self, filename):
    """Create a new from an RWL file."""
    
    stack_name = string.split(os.path.basename(filename), '.')[0]

    # check stack name
    # XXX
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
    # XXX
    for sample in samples:
      if str(sample) in self._samples:
        self.ui.warning("Duplicate sample",
                        "Sample %s already exists, replacing." % str(sample))

    # add samples
    for sample in samples:
      self._samples[str(sample)] = sample

    # add stack
    stack = Stack()
    stack.name = stack_name
    stack.add_samples(map(lambda x: str(x), samples))
    self.add_stack(stack)

    return stack
