import numpy as np
from bs4 import BeautifulSoup
import plotly.graph_objs as go
import pickle
import requests
import logging

questions = pickle.load(open('res/questions.pkl','rb'))

pro_contra_dict = {
    "media/pix/icon/votum_pro.png" : 1,
    "media/pix/icon/votum_con.png" : -1,
    "media/pix/icon/votum_neutral.png" : 0,
}

response2text = {
    1 : 'pro',
    0: 'neutral',
    -1: 'contra'
}

N_QUESTIONS = 38

def has_double_weight(text):
    return 'Diese These wurde doppelt gewichtet' in text

def get_weighted_answers(file_name, URL, content):
    if content:
        soup = BeautifulSoup(content, 'html.parser')
    elif URL:
        soup = BeautifulSoup(requests.get(URL).content, 'html.parser')
    else:
        soup = BeautifulSoup(open(file_name).read(), 'html.parser')

    ul_answer_weighting = soup.find("ul", class_='wom_thesen_points')

    if ul_answer_weighting is None:
        logging.error(soup)
        raise ValueError('ul_answer_weighting is None')

    lis_answer_weighting = ul_answer_weighting.find_all('li')

    if not isinstance(lis_answer_weighting, list):
        logging.error(soup)
        logging.error(lis_answer_weighting)
        raise ValueError(f'lis_answer_weighting is not a list but {type(lis_answer_weighting)}')

    if len(lis_answer_weighting) != N_QUESTIONS:
        logging.error(soup)
        logging.error(lis_answer_weighting)
        raise ValueError(f'lis_answer_weighting has length {len(lis_answer_weighting)} ({N_QUESTIONS} expected)')

    weights = 1 + np.array([has_double_weight(li.find("span", class_="thesenavi_tooltip").text)
                  for li in lis_answer_weighting])
    ul_answers = soup.find("div", class_='wom_antworten_box').ul

    if ul_answers is None:
        logging.error(soup)
        raise ValueError('ul_answers is None')

    li_answers = ul_answers.find_all('li')

    if not isinstance(li_answers, list):
        logging.error(soup)
        logging.error(li_answers)
        raise ValueError(f'li_answers is not a list but {type(lis_answer_weighting)}')

    if len(li_answers) != N_QUESTIONS:
        logging.error(soup)
        logging.error(li_answers)
        raise ValueError(f'li_answers has length {len(li_answers)} ({N_QUESTIONS} expected)')
    
    my_answers = [pro_contra_dict[li.p.img['src']] for li in li_answers]
    return weights * np.array(my_answers)

def prepare_caption(data, coeffs, questions, partei, top_n=3):
    def find_fingerprint_questions(partei, top_n=3):
        return coeffs[partei].sort_values()[:top_n]

    top_questions = find_fingerprint_questions(partei, top_n)
    result = f'<b>{partei}</b><br />'
    for question_id, val in top_questions.items():
        question_full = questions['full'][question_id]
        question_answer_counts = data.loc[question_id].value_counts()
        partei_answer_int = data.loc[question_id, partei]
        partei_answer = response2text[partei_answer_int]
        result += f'{question_full}'
        result += f' ({partei_answer},'
        if partei_answer_int == 1:
            result += '<b>'
        result += f' {question_answer_counts.loc[1]}'
        if partei_answer_int == 1:
            result += '</b>'
        result += '/'
        if partei_answer_int == -1:
            result += '<b>'
        result += f'{question_answer_counts.loc[-1]}'
        if partei_answer_int == -1:
            result += '</b>'
        result += '/' 
        if partei_answer_int == 0:
            result += '<b>'
        result += f'{question_answer_counts.loc[0]}'
        if partei_answer_int == 0:
            result += '</b>'
        result += ')<br />'
    return result

def create_partei_trace(data_2d, data, coeffs):
    trace = go.Scatter(
        x=data_2d[:,0],
        y=data_2d[:,1],
        hovertext=[prepare_caption(data, coeffs, questions, partei) for partei in data.columns],
        mode='markers+text',
        hoverinfo='text',
        marker = {'size':9},
        text=data.columns,
        textposition='middle right',
        hoverlabel = {'align':'left', 'bgcolor':'lightgray'}
    )

    layout = go.Layout(
        autosize=True,
        width=800,
        height=660,
        hovermode='closest',
        title=go.layout.Title(
            text="Party overview",
            xref='paper',
            x=0.5,
            xanchor='center',
            font=dict(size=16, color='black'),
    ),
    showlegend=False,
    xaxis=dict(
        tickmode='linear',
        ticks='outside',
        dtick=1,
        ticklen=0,
        tickwidth=0,
        zeroline=False,
        showticklabels=False
    ),
    yaxis=dict(
        tickmode='linear',
        ticks='outside',
        dtick=1,
        ticklen=0,
        tickwidth=0,
        zeroline=False,
        scaleanchor="x",
        scaleratio=1,
        showticklabels=False
    ))
    return trace, layout

def show_parties(data_2d, data):
    coeffs = data / data.sum(axis=1)[:, np.newaxis]
    coeffs.where(coeffs == 0, 1/coeffs, inplace=True)

    trace, layout = create_partei_trace(data_2d, data, coeffs)

    fig = go.Figure(data=[trace], layout=layout)
    return fig

def show_your_position(pca, data_2d, data, file_name=None, URL=None, content=None):
    # raises ValueError when parsing of the html source file unsuccessful
    weighted_answers = get_weighted_answers(file_name, URL, content)    
    weighted_answers_2d = pca.transform(np.atleast_2d(weighted_answers))

    data_incl_YOU = data.copy()
    data_incl_YOU['YOU'] = weighted_answers

    coeffs = data_incl_YOU / data.sum(axis=1)[:, np.newaxis]
    coeffs.where(coeffs == 0, 1/coeffs, inplace=True)

    trace, layout = create_partei_trace(data_2d, data, coeffs)


    my_trace = go.Scatter(
            x=weighted_answers_2d[:,0],
            y=weighted_answers_2d[:,1],
            hovertext=prepare_caption(data_incl_YOU, coeffs, questions, 'YOU'),
            mode='markers+text',
            hoverinfo='text',
            marker = {'color':'red', 'size':15, 'symbol':'x'},
            text='YOU',
            textposition='middle right',
            hoverlabel = {'align':'left', 'bgcolor':'lightgray'}
        )

    #fig = go.Figure(data=[trace, my_trace], layout=layout)
    #return fig, weighted_answers, weighted_answers_2d
    return my_trace