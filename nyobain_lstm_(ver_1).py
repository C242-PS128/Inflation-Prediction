# -*- coding: utf-8 -*-
"""nyobain_lstm (ver 1).ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/github/syifafatma/Indonesia-inflation-rate-prediction/blob/main/nyobain_lstm%20(ver%201).ipynb
"""

import pandas as pd
import requests
import numpy as np
import tensorflow as tf
from tensorflow.keras.layers import LSTM
import matplotlib.pyplot as plt
# !pip install openpyxl

github_url = 'https://raw.githubusercontent.com/syifafatma/Dataset-Inflasi/main/data_inflasi.xlsx'

# load dataset from github
my_file = requests.get(github_url)

# save file to buffer and read as pandas
with open('data_inflasi.xlsx', 'wb') as file:
  file.write(my_file.content)
dataset = pd.read_excel(my_file.content, engine='openpyxl')
print(dataset)

# sort the data in descending order (bawah ke atas)
dataset = dataset[::-1].reset_index(drop=True)

time_step = np.arange(len(dataset))
inflation = dataset['Inflasi'].str.replace('%', '').astype(float)

time = np.array(time_step)
x = np.array(inflation)

print(time)
print(x)

def plot_series(x, y, format="-", start=0, end=None,
                title=None, xlabel=None, ylabel=None, legend=None ):
   # Setup dimensions of the graph figure
    plt.figure(figsize=(10, 6))

    # Check if there are more than two series to plot
    if type(y) is tuple:

      # Loop over the y elements
      for y_curr in y:

        # Plot the x and current y values
        plt.plot(x[start:end], y_curr[start:end], format)

    else:
      # Plot the x and y values
      plt.plot(x[start:end], y[start:end], format)

    # Label the x-axis
    plt.xlabel(xlabel)

    # Label the y-axis
    plt.ylabel(ylabel)

    # Set the legend
    if legend:
      plt.legend(legend)

    # Set the title
    plt.title(title)

    # Overlay a grid on the graph
    plt.grid(True)

    # Draw the graph on screen
    plt.show()

# preview the data
plot_series(time, x, xlabel='Month', ylabel='Monthly Inflation Rate', title='Indonesia Inflation Rate from Januari 2003 - Oktober 2024')

# split the dataset
split_time = 200

time_train = time[:split_time]
x_train = x[:split_time]

time_valid = time[split_time:]
x_valid = x[split_time:]

def windowed_dataset(series, window_size, batch_size, shuffle_buffer):
    """Generates dataset windows

    Args:
      series (array of float) - contains the values of the time series
      window_size (int) - the number of time steps to include in the feature
      batch_size (int) - the batch size
      shuffle_buffer(int) - buffer size to use for the shuffle method

    Returns:
      dataset (TF Dataset) - TF Dataset containing time windows
    """

    # Generate a TF Dataset from the series values
    dataset = tf.data.Dataset.from_tensor_slices(series)

    # Window the data but only take those with the specified size
    dataset = dataset.window(window_size + 1, shift=1, drop_remainder=True)

    # Flatten the windows by putting its elements in a single batch
    dataset = dataset.flat_map(lambda window: window.batch(window_size + 1))

    # Create tuples with features and labels
    dataset = dataset.map(lambda window: (window[:-1], window[-1]))

    # Shuffle the windows
    dataset = dataset.shuffle(shuffle_buffer)

    # Create batches of windows
    dataset = dataset.batch(batch_size)

    # Optimize the dataset for training
    dataset = dataset.cache().prefetch(1)

    return dataset

# Parameters
window_size = 20
batch_size = 16
shuffle_buffer_size = 200

# Generate the dataset windows
train_set = windowed_dataset(x_train, window_size, batch_size, shuffle_buffer_size)

model = tf.keras.models.Sequential([
    tf.keras.Input(shape=(window_size, 1)),
    tf.keras.layers.Conv1D(filters=64, kernel_size=5, strides=1,
                           padding="causal", activation="relu"),
    tf.keras.layers.Bidirectional(LSTM(64, return_sequences=True)),
    tf.keras.layers.LSTM(64),
    tf.keras.layers.Dense(32, activation="relu"),
    tf.keras.layers.Dense(16, activation="relu"),
    tf.keras.layers.Dense(1)
])

model.summary()

# build and train the dataset
model.compile(loss=tf.keras.losses.Huber(),
              optimizer=tf.keras.optimizers.Adam(),
              metrics=["mae"])

history = model.fit(train_set, epochs=100)

# model prediction

def model_forecast(model, series, window_size, batch_size):
    """Uses an input model to generate predictions on data windows

    Args:
      model (TF Keras Model) - model that accepts data windows
      series (array of float) - contains the values of the time series
      window_size (int) - the number of time steps to include in the window
      batch_size (int) - the batch size

    Returns:
      forecast (numpy array) - array containing predictions
    """

    # Generate a TF Dataset from the series values
    dataset = tf.data.Dataset.from_tensor_slices(series)

    # Window the data but only take those with the specified size
    dataset = dataset.window(window_size, shift=1, drop_remainder=True)

    # Flatten the windows by putting its elements in a single batch
    dataset = dataset.flat_map(lambda w: w.batch(window_size))

    # Create batches of windows
    dataset = dataset.batch(batch_size).prefetch(1)

    # Get predictions on the entire dataset
    forecast = model.predict(dataset, verbose=0)

    return forecast

# Reduce the original series
forecast_series = x[split_time-window_size:-1]

# Use helper function to generate predictions
forecast = model_forecast(model, forecast_series, window_size, batch_size)

# Drop single dimensional axis
results = forecast.squeeze()

# Plot the results
plot_series(time_valid, (x_valid, results))

# Compute the MAE
print(tf.keras.metrics.mae(x_valid, results).numpy())

# Save the entire model
model.save('my_model_1.keras')

# Save only the model's weights
model.save_weights('my_model_1.weights.h5')

