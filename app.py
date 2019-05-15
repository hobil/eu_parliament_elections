from flask import Flask, render_template, request, flash, redirect, url_for, session
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
import json

import plotly as py
import plotly.graph_objs as go
import dash
import dash_core_components as dcc
import dash_html_components as html

from utils import show_your_position, show_parties
import logging
logging.getLogger().setLevel('INFO')

app = Flask(__name__)
app.secret_key = 'dljsaklqk24e21cjn!Ew@@dsa7'

data = pd.read_csv('res/data.csv')
pca = PCA(2)
data_2d = pca.fit_transform(data.T)
fig = show_parties(data_2d, data)
logging.info(data_2d.shape)
logging.info(pca.components_.shape)
#session['all_data'] = (data, pca, data_2d)
#session['fig'] = fig

@app.route('/')
def form():
    app = dash.Dash()
    #server = app.server
    #fig = session['fig']

    app.layout = html.Div(children=[
        html.H1('Party Overview'),
        dcc.Graph(
            id='party overview',
            figure=fig
        )]
    )
    print("Rendering")
    graphJSON = json.dumps(fig, cls=py.utils.PlotlyJSONEncoder)
    return render_template('index.html', plot=graphJSON)    

@app.route('/show', methods=['POST'])
def show():
    #data, pca, data_2d = session['all_data']
    text = request.form['view_source']

    #fig, weighted_answers, weighted_answers_2d = show_your_position(pca, data_2d, data, content=text)
    try:
        my_trace = show_your_position(pca, data_2d, data, content=text)
    except Exception as e:
        logging.exception(e)
        alert_message = "Sorry, we were not able to parse your data."
        flash(alert_message)
        return redirect(url_for('form'))

    fig.add_traces([my_trace])

    graphJSON = json.dumps(fig, cls=py.utils.PlotlyJSONEncoder)

    return render_template('index.html', plot=graphJSON)

if __name__ == '__main__':
    print("alive")
    logging.info("alive")
    app.run(host='0.0.0.0')
