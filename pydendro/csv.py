
import pandas as pd
import numpy as np

from pydendro.rwl import Sample

def read(filename):
  """Read CSV file, with headers core, year, and measurement; and return list of samples."""

  samples = []
  df = pd.read_csv(filename)
  for name, data in df.groupby('core'):
    srtd = data.sort_values('year')
    fyog = srtd['year'].min()
    deltas = np.asarray(srtd['year'][1:]) - np.asarray(srtd['year'][:-1])
    if not all(deltas == 1):
      print("WARNING: invalid years in sample:", name)
      continue
    samples.append(Sample(name, fyog, list(srtd['width'])))

  return samples
