import json
import urllib.request
from dash import dcc
import plotly.graph_objects as go
import dash
import dash_html_components as html

# In[34]:


data = None

# In[35]:


stock_price = 169.96

# In[36]:


with urllib.request.urlopen(
        'https://api.polygon.io/v3/snapshot/options/ZS?expiration_date=2024-06-07&limit=250&sort=strike_price&apiKey=DRKH6jOPq7B552OAhTGXo_LXqzY8Jy27') as response:
    data = json.loads(response.read().decode('utf8'))

# In[37]:


data['results'][0]['day']

# In[38]:


data['results'][0]['details']

# In[39]:


call_strikes = []
put_strikes = []

# In[40]:


for rec in data['results']:
    if rec['details']['contract_type'] == 'call' and rec['details'][
        'strike_price'] > stock_price and 'previous_close' in rec['day']:
        call_strikes.append((rec['details']['strike_price'], rec['day']['previous_close'] + rec['day']['change']))
    elif rec['details']['contract_type'] == 'put' and rec['details'][
        'strike_price'] < stock_price and 'previous_close' in rec['day']:
        put_strikes.insert(0, (rec['details']['strike_price'], rec['day']['previous_close'] + rec['day']['change']))

# In[41]:


call_strikes

# In[42]:


put_strikes

# In[43]:


put_strikes[-1][0]

# In[44]:


belly_pct = [4, 6, 8, 10, 12, 14, 16, 18, 20, 22]

# In[45]:


call_belly_strikes = []
put_belly_strikes = []

# In[46]:


for pct in belly_pct:
    call_belly_strikes.append(stock_price + (stock_price * (pct / 100)))
    put_belly_strikes.append(stock_price - (stock_price * (pct / 100)))

# In[47]:


call_belly_strikes

# In[48]:


for cstrk in range(len(call_belly_strikes)):
    for ctup in range(len(call_strikes)):
        if call_belly_strikes[cstrk] < call_strikes[ctup][0]:
            if call_strikes[ctup - 1][0] not in call_belly_strikes:
                call_belly_strikes[cstrk] = call_strikes[ctup - 1][0]
                break

# In[49]:


call_belly_strikes

# In[50]:


for pstrk in range(len(put_belly_strikes)):
    for ptup in range(len(put_strikes)):
        if put_belly_strikes[pstrk] > put_strikes[ptup][0]:
            if put_strikes[ptup - 1][0] not in put_belly_strikes:
                put_belly_strikes[pstrk] = put_strikes[ptup - 1][0]
                break

# In[51]:


put_belly_strikes


# In[54]:


def generate_data(p_v, q_v, s_v, CorP):
    if CorP == 'C':
        last = int(round(float(s_v[0]) / 10, 0) * 10 + 10)
        first = int(last * 0.7)
        increment = int((last - first) / 18)
    else:
        first = int(round(float(s_v[0]) / 10, 0) * 10)
        last = int(first * 1.3)
        increment = int((last - first) / 18)

    xaxis = list(range(first, last, increment))

    yaxis_cr = []
    for cols in range(0, len(p_v)):
        nl = []
        for x in xaxis:
            if CorP == 'C':
                nl.append(0 if x >= s_v[cols] else (s_v[cols] - x) * q_v[cols])
            else:
                nl.append(0 if x <= s_v[cols] else (x - s_v[cols]) * q_v[cols])
        yaxis_cr.append(nl)

    p_q = [a * b for a, b in zip(p_v, q_v)]
    pq = sum(p_q)
    pq = -pq

    yaxis_cr.append([pq] * len(xaxis))

    yaxis_tr = zip(*yaxis_cr)

    yaxis = [sum(a) for a in yaxis_tr]

    out = list(zip(xaxis, yaxis))
    return out


def create_plot(x_plot, y_plot):
    fig = go.Figure(data=[go.Scatter(x=x_plot, y=y_plot, mode='lines+markers', line=dict(color='royalblue', width=3))])
    return fig


def generate_butterfly(input_data, CorP):
    tokens = input_data.split("/")
    total = len(tokens)
    print(total)
    div = int(total / 3)
    print(div)
    p_v = tokens[0:div]
    q_v = tokens[div:div * 2]
    s_v = tokens[div * 2:div * 3]

    p_v = [float(i) for i in p_v]
    q_v = [float(i) for i in q_v]
    s_v = [float(i) for i in s_v]

    print("p_v", p_v)
    print("q_v", q_v)
    print("s_v", s_v)

    xyaxis = generate_data(p_v, q_v, s_v, CorP)
    unzip_v = ([a for a, b in xyaxis], [b for a, b in xyaxis])
    line_plot = create_plot(unzip_v[0], unzip_v[1])
    return line_plot


# In[57]:

graphs_list = []

for strk in range(len(call_belly_strikes)):
    belly_idx = 0
    for cidx in range(len(call_strikes)):
        if call_strikes[cidx][0] == call_belly_strikes[strk]:
            belly_idx = cidx
            break
    lwing = belly_idx - 1
    rwing = belly_idx + 1

    if lwing < 0 or rwing > len(call_strikes) or belly_idx == 0:
        continue

    print(
        'Generating legs for belly {}, Price {}   Pct {}'.format(call_strikes[belly_idx][0], call_strikes[belly_idx][1],
                                                                 belly_pct[strk]))

    # just to break is 2 loops -- remove later
    if call_strikes[belly_idx][0] == 182.5:
        break

    while lwing >= 0 and rwing <= len(call_strikes) - 1:
        if call_strikes[belly_idx][0] - call_strikes[lwing][0] > call_strikes[rwing][0] - call_strikes[belly_idx][0]:
            rwing += 1
            continue
        elif call_strikes[belly_idx][0] - call_strikes[lwing][0] < call_strikes[rwing][0] - call_strikes[belly_idx][0]:
            lwing -= 1
            continue
        else:
            bcost = call_strikes[lwing][1] + call_strikes[rwing][1] - (2 * call_strikes[belly_idx][1])
            left_wing = call_strikes[lwing][0]
            right_wing = call_strikes[rwing][0]
            left_price = call_strikes[lwing][1]
            right_price = call_strikes[rwing][1]
            left_pct = ((call_strikes[lwing][0] - stock_price) / stock_price) * 100
            right_pct = ((call_strikes[rwing][0] - stock_price) / stock_price) * 100
            print('Left Wing - {}, Left Pct - {}, Price {}, Right Wing - {}, Right Pct - {}, Price {}, Cost {}'.format(
                left_wing, left_pct, left_price, right_wing, right_pct, right_price, bcost))
        lwing -= 1
        rwing += 1

        inpt = f"{left_price}/{call_strikes[belly_idx][1]}/{right_price}/1/2/1/{left_wing}/{call_strikes[belly_idx][0]}/{right_wing}"
        print("Calling Graph for :", inpt)
        fig = generate_butterfly(inpt, "C")
        plot_title = f"Generated plot for Belly : {call_strikes[belly_idx][0]} and Price : {call_strikes[belly_idx][1]}"
        fig.update_layout(title=plot_title)
        print(fig)
        graphs_list.append(fig)


graphs=dash.Dash(__name__)
graphs.layout=html.Div(
    children=[
        #  First Graph horizontal bar
        dcc.Graph(figure=graphs_list[0]),
        dcc.Graph(figure=graphs_list[1]),
        dcc.Graph(figure=graphs_list[2]),
        dcc.Graph(figure=graphs_list[3])
    ])
graphs.run_server()

# for strk in range(len(put_belly_strikes)):
#     belly_idx = 0
#     for pidx in range(len(put_strikes)):
#         if put_strikes[pidx][0] == put_belly_strikes[strk]:
#             belly_idx = pidx
#             break
#     lwing = belly_idx - 1
#     rwing = belly_idx + 1
#
#     if lwing < 0 or rwing > len(put_strikes) or belly_idx == 0:
#         continue
#
#     print('Generating legs for Belly {}, Price {}   Pct {}'.format(put_strikes[belly_idx][0], put_strikes[belly_idx][1],
#                                                                    belly_pct[strk]))
#     while lwing >= 0 and rwing <= len(put_strikes) - 1:
#         if put_strikes[belly_idx][0] - put_strikes[lwing][0] > put_strikes[rwing][0] - put_strikes[belly_idx][0]:
#             rwing += 1
#             continue
#         elif put_strikes[belly_idx][0] - put_strikes[lwing][0] < put_strikes[rwing][0] - put_strikes[belly_idx][0]:
#             lwing -= 1
#             continue
#         else:
#             bcost = put_strikes[lwing][1] + put_strikes[rwing][1] - (2 * put_strikes[belly_idx][1])
#             left_wing = put_strikes[lwing][0]
#             right_wing = put_strikes[rwing][0]
#             left_price = put_strikes[lwing][1]
#             right_price = put_strikes[rwing][1]
#             left_pct = ((stock_price - put_strikes[lwing][0]) / stock_price) * 100
#             right_pct = ((stock_price - put_strikes[rwing][0]) / stock_price) * 100
#             print('Left Wing - {}, Left Pct - {}, Price {}, Right Wing - {}, Right Pct - {}, Price {}, Cost {}'.format(
#                 left_wing, left_pct, left_price, right_wing, right_pct, right_price, bcost))
#             # print('Left Wing - {}, Price {}, Right Wing - {}, Price {}, Cost {}'.format(put_strikes[lwing][0],put_strikes[lwing][1],put_strikes[rwing][0],put_strikes[rwing][1],bcost))
#         lwing -= 1
#         rwing += 1
#




