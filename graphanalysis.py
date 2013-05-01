from pylab import *
from datetime import datetime, date
import time
import json
import zmq
import sys
import pprint
import numpy as np
from scipy import interpolate
import pylab
import string as st
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.finance import candlestick
from matplotlib.dates import num2date

class graphanalysis:
  def __init__(self, rcvd, rcvd_type):
    # initialize variable
    self.rcvd_type = rcvd_type
    
    # process json packet into usable data
    if rcvd_type == 'stock':
      self.process_json_stock(rcvd)
    elif rcvd_type == 'tweet':
      self.process_json_tweet(rcvd)
    else:
      raise Exception("Invalid graph type created")
  
    self.xs = pylab.arange(0, len(self.dtarr), 1)
    self.ys = None

  def process_json_stock(self, rcvd):
    # processes json packet of information
    # add a zero element so we can perform array operations
    self.arr = np.array([0])
    self.dtarr = np.array([0])
    # include just the averages
    for row in rcvd:  
      if st.find(row[1], "avg")>0:
        self.dt     = datetime.strptime(row[1][:10],'%Y-%m-%d')
        self.dtarr  = np.vstack((self.dtarr, [self.dt]))
        self.arr    = np.vstack((self.arr, [row[3]]))   # [row[0], row[1], row[2], row[3]]))
      else:
        pass
    
    self.arr = np.delete(self.arr, 0)
    self.dtarr = np.delete(self.dtarr, 0)

  def process_json_tweet(self, rcvd):
    # process json packet of daily tweet sentiment data
    self.arr = np.array([0])
    self.dtarr = np.array([0])
    #process each row
    for row in rcvd:
      pprint.pprint(row)
      avg = float(row[4] - row[5])/row[7] # compute average value
      self.dt     = datetime.strptime(row[1][:10],'%Y-%m-%d')
      self.dtarr  = np.vstack((self.dtarr, [self.dt]))
      self.arr    = np.vstack((self.arr, avg))   # [row[0], row[1], row[2], row[3]]))
      #pprint.pprint(row)

    self.arr = np.delete(self.arr, 0)
    self.dtarr = np.delete(self.dtarr, 0)


  def interpolate(self, coeffs):
    # run graph anaylsis

    # make iterator values over length of date array
    self.xs = pylab.arange(0, len(self.dtarr), 1)

    # polynomial fit of the graph we have (this time just use 10)
    self.coeff    = np.polyfit(self.xs, self.arr, coeffs)
    self.polynom  = np.poly1d(self.coeff)
    self.ys       = self.polynom(self.xs)

  def run_plot(self):
    print "debug output first:"
    print "*** dtarr: "
    print self.dtarr
    print "*** arr: "
    print self.arr
    
    print "plotting raw datapoints"
    pylab.plot_date(self.dtarr, self.arr, 'o')

    # have we interpolated recently?
    if self.ys is None:
      pass
    else:
      print "plotting interpolated datapoints"
      pylab.plot_date(self.dtarr, self.ys, '-')

    pylab.ylabel('y')
    pylab.xlabel('x')


    pylab.show()

if __name__ == "__main__":
  if len(sys.argv) < 3:
    print "usage: graphanalysis ADDR TICKER BIZNAME"

    pprint.pprint(sys.argv)
    exit()

  tickers = [sys.argv[2]]
  biznames = [sys.argv[3]]

  context = zmq.Context()

  socket = context.socket(zmq.REQ)
  addr = ("tcp://%s:5555" % sys.argv[1])
  print "connecting to server %s" % addr
  socket.connect( addr )

  for stock in tickers:
    #### bring in stock info
    # format data package
    dataset = {'type' : 'stock_pull', 'symbol' : stock, 'clientname' : 'graphanalysis_test'}
    message = json.dumps(dataset)
    pprint.pprint(dataset)

    # send data package
    print "Requesting data for ticker ", stock, "..."
    socket.send(message)

    # wait for reply
    message = socket.recv()
    print "Received reply for ticker ", stock

    # decode reply
    rcvd = json.loads(message)

    stk = graphanalysis(rcvd, 'stock')
    stk.interpolate(10)
    stk.run_plot()

  for bizname in biznames:
    #### bring in tweet info
    # format data package
    dataset = {'type' : 'avgSentiment_pull', 'symbol' : bizname, 'dateRange' : '', 'clientname' : 'graphanalysis_test'}
    message = json.dumps(dataset)
    pprint.pprint(dataset)

    # send data package
    print "Requesting data for ticker ", bizname, "..."
    socket.send(message)

    # wait for reply
    message = socket.recv()
    print "Received reply for ticker ", bizname

    # decode reply
    rcvd = json.loads(message)

    print "new graphanalysis class for tweet"
    twt = graphanalysis(rcvd, 'tweet')
    print "interpolate the graph"
    #twt.interpolate(4)
    print "plot it!"
    twt.run_plot()
