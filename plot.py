import json
import sys

import plotly.express as px
import pandas as pd


def load_data(file_name):
	with open(file_name) as json_file:
	    return json.load(json_file)


def validate_params():
	if len(sys.argv) < 2:
		print("como usar: python plot.py <termo>")
		quit()


##########

validate_params()

termo = sys.argv[1]
words = load_data('words.json')

df = pd.DataFrame.from_dict(words[termo], orient='index', columns=['count'])

fig = px.line(df[:-1], y="count", title=f"Occorências de {termo}")
fig.show()