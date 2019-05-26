import numpy as np
import plotly.graph_objs as go
import json
import logging
import jinja2
import textwrap

N_QUESTIONS = 38

# for printing purposes
response2text = {
    1: 'pro',
    0: 'neutral',
    -1: 'contra'
}

# colors representing NEUTRAL, PRO and CONTRA color
colors = np.array([
    'lightgray',
    '#2ca02c', # cooked asparagus green
    '#d62728', # brick red
])

# convenience list for `positions` and `question_positions`
# which describe positions using indices of this array 
positions_list = np.array([None,
                           'bottom left', 'bottom center', 'bottom right',
                           'middle left','middle center', 'middle right',
                           'top left', 'top center', 'top right'])

# positions of captions for each party on the party and result plot
# each number corresponds to the position as defined in `positions_list`
positions = [6, 4, 9, 7, 9, 4, 3, 4, 2, 3, 9, 9, 6, 9, 9, 3, 2, 6, 1, 9, 9, 9, 3, 3, 2, 3, 9, 3,
             6, 3, 1, 3, 9, 6, 7, 1, 9, 9, 9, 9]

# positions of captions for each question on the question plot
# each number corresponds to the position as defined in `positions_list`
question_positions = [2, 7, 9, 9, 3, 7, 9, 2, 3, 9, 4, 7, 3, 9, 9, 8, 1, 9, 4,
                     9, 3, 3, 7, 1, 3, 9, 9, 1, 3, 9, 6, 4, 9, 6, 3, 3, 9, 9]


# custom colormap based on Red-Yellow-Green
rdylgn_rgb = json.load(open('res/rdylgn_custom_cm.json'))


def create_plot(data, data_2d, pca, answers, show_top_n_anwers=3):
    """Return plotly figure with all the parties and own position based on answers."""

    answers = np.array(answers)
    answers_2d = pca.transform(np.atleast_2d(answers))
    # for each party compute absolute difference
    results = data.T.sub(answers).abs().sum(axis=1)
    max_difference = N_QUESTIONS * 2
    results_relative = (np.clip(1 - results / max_difference, a_min=0, a_max=1) * 100).round()
    
    my_trace_hover = zip()

    trace = go.Scatter(
        x=list(data_2d[:,0]),
        y=list(data_2d[:,1]),
        hovertext = [f'<b>{int(val)} %</b>' for val in results_relative],
        mode='markers+text',
        hoverinfo='text',
        marker=dict(
            size=10,
            cmax=100,
            cmin=0,
            color=list(results_relative),
            colorscale=rdylgn_rgb
        ),
        
        text=list(data.columns),
        textposition=list(positions_list[positions]),
        hoverlabel = {'align':'left', 'bgcolor':'lightgray', 'font':{'family':'Courier New, monospace'}}
    )

    layout = go.Layout(
        autosize=True,
        width=900,
        height=900,
        hovermode='closest',
        hoverlabel={'font':{'size':16}},
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
        )
    )
    
    top_n = results_relative.sort_values(ascending=False)[:show_top_n_anwers]
    my_trace_hover = """\
Parties closest to your answers:<br />\
{% for party_name, val in top_n.items() %}{{ party_name.ljust(longest_party_name) }} : <b>{{ val }} %</b> <br />\
{% endfor %}\
"""

    my_trace = go.Scatter(
        x=list(answers_2d[:,0]),
        y=list(answers_2d[:,1]),
        hovertext=jinja2.Template(my_trace_hover).render(
            top_n=top_n.astype(int),
            longest_party_name=max([len(x) for x in top_n.index])
        ),
        mode='markers+text',
        hoverinfo='text',
        marker = {'color':'#d62728', 'size':14, 'symbol':'x'},
        text='<b>YOU</b>',
        textposition='middle right',
        hoverlabel = {'align':'left', 'bgcolor':'lightgray', 'font':{'family':'Courier New, monospace', 'size':14}}
    )

    fig = go.Figure(data=[trace, my_trace], layout=layout)
    return fig


def create_question_fig(data, data_2d, questions, reasons):
    """Return plotly figure with a question slider with detailed answers of all parties."""

    def create_trace_question(question_id):
        if question_id is not None:
            marker_colors = list(colors[data.loc[question_id]])
        else:
            marker_colors = None
        return go.Scatter(
            x=list(data_2d[:,0]),
            y=list(data_2d[:,1]),
            hovertext=[f'<b>{partei} : {response2text[data.loc[question_id][partei]]}</b><br>' + \
                    '<br />'.join(textwrap.wrap(reasons.loc[question_id][partei]))
                    for partei in reasons.columns],
            mode='markers+text',
            hoverinfo='text',
            marker={'color':marker_colors, 'size':10},
            text=list(data.columns),
            textposition=list(positions_list[positions]),
            hoverlabel={'align':'left'},
            visible=False
    )

    traces = [create_trace_question(question_id) for question_id in data.index]
    traces[0]['visible'] = True

    steps=[]
    for i in range(len(traces)):
        step = dict(
            method = 'update',  
            args = [
                {'visible': [t == i for t in range(len(traces))]},
                {'title.text': '<b>Thesis</b><i>:<br />"{}"</i>'.format("<br />".join(textwrap.wrap(questions["full"][i], width=60)))}],
            label=questions['short'][i]
        )
        steps.append(step)

    layout = go.Layout(
        autosize=True,
        width=800,
        height=800,
        font={'size':13},
        hovermode='closest',
        title=go.layout.Title(
            text='<b>Thesis</b><i>:<br />"{}"</i>'.format("<br />".join(textwrap.wrap(questions["full"][i], width=60))),
            xref='paper',
            x=0.5,
            xanchor='center',
            font=dict(size=18, color='black'),
        ),
        sliders= [dict(
            active = 0,
            pad = {"t": 20},
            steps = steps)
        ],
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

    fig = go.Figure(data=traces, layout=layout)
    return fig

def create_party_fig(data, pca, questions):
    """Return plotly figure with a party slider and visualisation of questions."""

    def prepare_caption_partei(question_id, top_n=3):
        question_answer_counts = data.loc[question_id].value_counts()
        result = f'<b>{questions["full"][question_id]}</b><br />'
        result+= f'pro     : {question_answer_counts.loc[1]}<br />'
        result+= f'contra  : {question_answer_counts.loc[-1]}<br />'
        result+= f'neutral : {question_answer_counts.loc[0]}<br />'
        return result

    def create_trace_partei(partei):
        if partei is not None:
            marker_colors = list(colors[data[partei]])
        else:
            marker_colors = None
        return go.Scatter(
            x=list(pca.components_[0]),
            y=list(pca.components_[1]),
            hovertext=[prepare_caption_partei(question_id) for question_id in data.index],
            mode='markers+text',
            hoverinfo='text',
            marker = {'color':marker_colors, 'size':10},
            text=list(questions['short']),
            textposition=list(positions_list[question_positions]),
            hoverlabel = {'align':'left'},
            visible=False
        )
    
    traces = [create_trace_partei(partei) for partei in data.columns]
    traces[0]['visible'] = True

    steps=[]
    for i in range(len(traces)):
        step = dict(
            method = 'update',  
            args = [
                {'visible': [t == i for t in range(len(traces))]},
                {'title.text': f'<b>Party:</b><br /><i>{data.columns[i]}</i>'}],
            label=data.columns[i]
        )
        steps.append(step)

    layout = go.Layout(
        autosize=True,
        width=960,
        height=800,
        hovermode='closest',
        hoverlabel=dict(bgcolor='lightgray'),
        title=go.layout.Title(
            text=f'<b>Party:</b><br /><i>{data.columns[0]}</i>',
            xref='paper',
            x=0.5,
            xanchor='center',
            font=dict(size=20, color='black'),
        ),
        sliders= [dict(
            active = 0,
            pad = {"t": 50},
            steps = steps,
    )],
        font=dict(size=10),
        xaxis=dict(
            tickmode='linear',
            ticks='outside',
            dtick=0.1,
            ticklen=0,
            tickwidth=0,
            zeroline=False,
            showticklabels=False
        ),
        yaxis=dict(
            tickmode='linear',
            ticks='outside',
            dtick=0.1,
            ticklen=0,
            tickwidth=0,
            zeroline=False,
            scaleanchor="x",
            scaleratio=1,
            showticklabels=False
        )
    )

    fig = go.Figure(data=traces, layout=layout)
    return fig