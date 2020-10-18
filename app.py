from flask import Flask, render_template

import plotly
import plotly.graph_objs as go
from plotly.subplots import make_subplots


import pandas as pd
import json

from os import getenv
from walrus import Database


RATES_GRABBER_CONNECTION_URI = getenv('RATES_GRABBER_CONNECTION_URI', 'redis://localhost:6379/2')
CURRENCY_CODE =     [  'USD',   'EUR',   'GBP',   'CHF', 'JPY']
CURRENCY_BASELINE = [79.4277, 88.8241, 97.0874, 85.0774, 0.6938]


app = Flask(__name__)


def create_plot():
    updated = None
    db = Database().from_url(RATES_GRABBER_CONNECTION_URI)

    fig = make_subplots(
        rows=len(CURRENCY_CODE), cols=1,
        subplot_titles=CURRENCY_CODE)

    fig.update_layout(
        showlegend=False,
        autosize=False,
        height=1500,
        width=1500,
        plot_bgcolor='#111'
    )

    fig.update_xaxes(gridcolor='#333')
    fig.update_yaxes(gridcolor='#333')
    fig.update_shapes()

    for i, currency in enumerate(CURRENCY_CODE):
        rates = []
        for m in db.Set(currency).members():
            rates.append(json.loads(m))

        df = pd.DataFrame(data=rates)
        df.sort_values(by='date', inplace=True)

        scatter = go.Scatter(
            x=df['date'],
            y=df['rate_buy'],
            name=currency
        )

        fig.add_trace(scatter, col=1, row=i+1)
        fig.add_shape(type='line',
                      xref='x1', yref='y1',
                      x0=df.min()['date'], y0=CURRENCY_BASELINE[i],
                      x1=df.max()['date'], y1=CURRENCY_BASELINE[i],
                      col=1, row=i+1,
                      line_color='#f00',
                      line_dash='dot', opacity=0.75)
        updated = df.max()['date']

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder), updated


@app.route('/')
def index():
    fig, updated = create_plot()
    return render_template('index.html', fig=fig, updated=updated)


if __name__ == '__main__':
    app.run(debug=True)
