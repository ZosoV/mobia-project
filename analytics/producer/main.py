from kafka import KafkaProducer
from datetime import datetime
import time
import math
from random import random, randint
import json

# Constants
INTERVAL = .3
STEP = .1
MAX_AMP = 10


# Generates a noisy sin value given:
# * amp : amplitude
# * i   : x value (which does not exceed 2 * pi)
# * lim : max
def noisy_sin_val(amp, i):
  if i <= 2 * math.pi:
    i += STEP
  else:
    amp = randint(0, MAX_AMP)
    i = 0.0

  noise = (random() - .5)
  result = math.sin(i) * amp + noise

  return amp, i, result

# produce a noisy sin wave with changing amplitude and produce kafka events
if __name__ == '__main__':
  # create the producer
  producer = KafkaProducer(bootstrap_servers=['localhost:9092'],
                           value_serializer=lambda v: json.dumps(v).encode('utf-8'))

  # params for sample data
  amp, i = 1, 0.0

  # send events every INTERVAL
  while True:
    amp, i, val_to_send = noisy_sin_val(amp, i)

    message = {"time" : str(datetime.now().time()), "value" : val_to_send}
    
    print("Seding: ", message)

    # send on topic, 'wave'
    producer.send("wave", message)
    time.sleep(INTERVAL)
