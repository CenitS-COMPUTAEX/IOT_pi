#!/bin/bash
# Generate random values
param1=$(shuf -i 20-30 -n 1)
param2=$(shuf -i 15-25 -n 1)
param3=$(shuf -i 800-900 -n 1)
param4=$(shuf -i 20-30 -n 1)
param5=$(shuf -i 10-20 -n 1)

# <ENDPOINT> should be replaced with the IP address and port of the remote server that will receive the data
# The value of the --data parameter should be replaced with whatever format the server needs to receive the data
curl --data "field1=$param1&field2=$param2&field3=$param3&field4=$param4&field5=$param5" <ENDPOINT>?

