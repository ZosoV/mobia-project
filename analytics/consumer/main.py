from kafka import KafkaConsumer
import json
from datetime import datetime
import pandas as pd
from bokeh.io import curdoc
from bokeh.plotting import figure
from bokeh.client import push_session
from bokeh.layouts import column, row

MAX_MSGS = 1000
WINDOW_SIZE = 300


# This is a callback function that gets called periodically:
# * fetches the next MAX_MSGS messages from the consumer
# * adds the new data to the dataframe
# * updates the data source for the plot
def update(consumer, df):
  for message in consumer.get_messages(count=MAX_MSGS):
    # parse the message
    result = json.loads(message.message.value)
    t = datetime.strptime(result['time'], "%H:%M:%S.%f")
    v = float(result['value'])
    print(f"Receiving: {t} {v}")

    # add to the dataframe
    df.loc[len(df)] = [t, v]

  # Sliding window of the WINDOW_SIZE most recent values
  if len(df['value']) > WINDOW_SIZE:
    r.data_source.data['y'] = list(df['value'])[-WINDOW_SIZE:]
    r.data_source.data['x'] = range(len(list(df['value'])))[-WINDOW_SIZE:]
    dots.data_source.data['y'] = list(df['value'])[-WINDOW_SIZE:]
    dots.data_source.data['x'] = range(len(list(df['value'])))[-WINDOW_SIZE:]
  else:
    r.data_source.data['y'] = list(df['value'])
    r.data_source.data['x'] = range(len(list(df['value'])))
    dots.data_source.data['y'] = list(df['value'])
    dots.data_source.data['x'] = range(len(list(df['value'])))


# A Kafka consumer listens for messages on the 'wave' topic and plots
# up-to-date results in a Bokeh plot
if __name__ == '__main__':
  # Initiate connection to Kafka (consumer) and Redis
  # client = SimpleClient('localhost:9092')
  # consumer = SimpleConsumer(client, None, 'wave')

  consumer = KafkaConsumer(
        'messages',
        bootstrap_servers='localhost:9092')

  # push this plotting session to Bokeh page
  # session = push_session(curdoc())

  # dataframe that is updated with all new data
  df = pd.DataFrame(columns=['time', 'value'])

  # data vars
  time, value = [0], [0]

  # figure that is updated with new data
  plot = figure()
  r = plot.line(time, value)
  dots = plot.circle(time, value, size=1, color='navy')

  # check for new kafka events every second
  curdoc().add_root(row(plot, width=800))
  curdoc().add_periodic_callback(lambda: update(consumer, df), 1000)
  # session.show(plot)  # open the document in a browser
