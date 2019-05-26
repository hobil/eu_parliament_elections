from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
from sklearn.decomposition import PCA
import json
import dash
from utils import create_plot, create_question_fig, create_party_fig
import logging
logging.getLogger().setLevel('INFO')

app = Flask(__name__)
app.secret_key = 'dljsaklqk24e21cjn!Ew@@dsa7'

data = pd.read_csv('res/data.csv')
pca = PCA(2)
data_2d = pca.fit_transform(data.T)
questions = json.load(open('res/questions.json'))
reasons = pd.read_csv('res/reason.csv')
fig_parties = json.dumps(create_party_fig(data, pca, questions).to_dict())
fig_questions = json.dumps(create_question_fig(data, data_2d, questions, reasons).to_dict())

N_QUESTIONS = 38


@app.route('/')
def form():

    if 'answers' in session:
        fig_result = json.dumps(create_plot(data, data_2d, pca, session['answers']).to_dict())
    else:
        fig_result = None
    
    return render_template(
        'index.html',
        questions=questions['full'],
        plot_party_overview=fig_parties,
        plot_question_overview=fig_questions,
        plot_results=fig_result,
        selected_tab="Results" if fig_result else "Questions"
    )


@app.route('/evaluate', methods=['POST'])
def evaluate():
    logging.debug(request.data)
    answers = request.get_json()
    answers = [int(val) if val is not None else 0 for val in answers]
    logging.info(answers)
    session['answers'] = answers
    return redirect(url_for('form'))


if __name__ == '__main__':
    app.run(host='0.0.0.0')