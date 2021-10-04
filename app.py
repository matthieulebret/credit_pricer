import streamlit as st
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots

from rw_irba import rw_irba
from rw_ssfa import rw_ssfa

import numpy as np
import pandas as pd
import datetime
import xlrd


st.title('Credit pricer application')


st.sidebar.title('Select filters')

pricerfilter = st.sidebar.multiselect('Want to see insurance and / or securitisation?',['Insurance','Securitisation'])


st.sidebar.header('Loan-level parameters')

upfront = st.sidebar.number_input('Upfront fees',0.00,5.00,1.00,0.05)/100
margin = st.sidebar.number_input('Loan margin',0.00,5.00,2.00,0.05)/100
funding = st.sidebar.number_input('Cost of funds',0.00,5.00,1.50,0.05)/100
operations = st.sidebar.number_input('Operations',0.00,0.50,0.20,0.05)/100

scale = st.sidebar.radio('Choose rating scale',['Nord','Moodys'],1)

if scale == 'Moodys':
    ratings = ['Aaa','Aa1','Aa2','Aa3','A1','A2','A3','Baa1','Baa2','Baa3','Ba1','Ba2','Ba3','B1','B2','B3','Caa1']
    defaultprob = [0.000001,0.000006,0.000014,0.000030,0.000058,0.000109,0.000389,0.0009,0.0017,0.0042,0.0087,0.0156,0.0281,0.0468,0.0716,0.1162,0.173816]
else:
    ratings = ['AAAA','AAA','AA+','AA','AA-','A+','A','A-','2','3','4','5','6','7','8','9','10','11','12','13','14','15']
    defaultprob = [0,0.0001,0.0002,0.0003,0.0004,0.0005,0.00065,0.00094,0.0011,0.0016,0.00246,0.0035,0.005,0.0075,0.0132,0.0198,0.0296,0.0444,0.0667,0.1,0.15,0.2]

moodyspd = pd.DataFrame(defaultprob,index=ratings,columns=['Pd'])


rating = st.sidebar.selectbox('Select obligor rating',ratings,index=10)
tenor = max(1,min(st.sidebar.slider('Select tenor',0,15,5,1),5))
LGD = st.sidebar.slider('Select LGD',0,100,30,5)/100
financial = st.sidebar.checkbox('Obligor is a financial institution')

if 'Insurance' in pricerfilter:
    st.sidebar.header('Insurance parameters')
    includeUFins = st.sidebar.checkbox('Include upfront fees in pricing')
    insrating = st.sidebar.selectbox('Select insurer rating',ratings,index=6)
    brokerfee = st.sidebar.number_input('Broker fee as % premium',0,20,15,5)


if 'Securitisation' in pricerfilter:
    st.sidebar.header('Securitisation parameters')
    includeUF = st.sidebar.checkbox('Include upfront fees in pricing',key='sec')
    granul = st.sidebar.slider('Select portfolio granularity',1,50,10,1)
    junior = st.sidebar.slider('Select junior tranche level',0,100,(0,25),1)

# Display calculation results



pd = defaultprob[ratings.index(rating)]
rw = rw_irba(pd,LGD,tenor,financial)

st.header('Loan-level results')

st.subheader('Risk parameters')

col1,col2,col3 = st.columns(3)
with col1:
    st.metric('Default probability', '{:.2%}'.format(pd))
with col2:
    st.metric('Risk weight', '{:.2%}'.format(rw))
with col3:
    st.metric('Expected loss', '{:.2%}'.format(pd*LGD))

st.subheader('Profitability')
RAROC = (margin + upfront / tenor - funding - pd * LGD - operations) / (0.1 * rw_irba(pd,LGD,tenor,financial))
st.metric(r"The deal's RAROC", '{:.2%}'.format(RAROC))


if 'Insurance' in pricerfilter:
    st.header('Credit insurance results')
    st.subheader('Risk parameters')
    pdins = defaultprob[ratings.index(insrating)]
    rwins = rw_irba(pdins,LGD,tenor,True)

    col4,col5,col6 = st.columns(3)
    with col4:
        st.metric('Default probability','{:.2%}'.format(pdins))
    with col5:
        st.metric('Risk weight after cover','{:.2%}'.format(rwins))
    with col6:
        st.metric('Expected loss after cover','{:.2%}'.format(pdins*LGD))

    st.subheader('Pricing parameters')
    if includeUFins:
        margin = margin + upfront / tenor
    insrisk = max((rw+10*pd*LGD-rwins-10*pdins*LGD)/(rw+10*pd*LGD),0)
    inspremium = insrisk * (margin - funding - operations)
    brokerage = inspremium * brokerfee / 100
    col7,col8 = st.columns(2)
    with col7:
        st.metric('Insurer share of the risk', '{:.2%}'.format(insrisk))
    with col8:
        st.metric('Bank share of the risk', '{:.2%}'.format(1-insrisk))
    col9,col10,col11 = st.columns(3)
    with col9:
        st.metric('Insurance premium','{:.2%}'.format(inspremium))
    with col10:
        st.metric('Brokerage fee','{:.2%}'.format(brokerage))
    with col11:
        st.metric('Total cost of cover','{:.2%}'.format(inspremium+brokerage))

    st.subheader('Profitability comparison')
    RAROCafter = (margin + upfront / tenor - inspremium - brokerage - funding - pdins * LGD - operations) / (0.1 * rw_irba(pdins,LGD,tenor,True))
    netmarginafter = margin - inspremium - brokerage - funding - operations
    col12,col13,col14 = st.columns(3)
    with col12:
        st.metric('RAROC before','{:.2%}'.format(RAROC))
    with col13:
        st.metric('RAROC after','{:.2%}'.format(RAROCafter))
    with col14:
        st.metric('Net margin after insurance', '{:.2%}'.format(netmarginafter))

if 'Securitisation' in pricerfilter:
    st.header('Securitisation results')

    st.subheader('Risk parameters')

    kirb = 0.1*rw + pd*LGD
    rwsenior = min(max(0.15,rw_ssfa(junior[1]/100,1,kirb,LGD,granul,tenor,True)),kirb*10)
    seniorrisk = rwsenior*(1-junior[1]/100)/(10*kirb)
    juniorrisk = 1-rwsenior*(1-junior[1]/100)/(10*kirb)

    col15,col16,col17,col18 = st.columns(4)
    with col15:
        st.metric('Kirb', '{:.2%}'.format(kirb))
    with col16:
        st.metric('Risk weight senior', '{:.2%}'.format(rwsenior))
    with col17:
        st.metric('Senior tranche % total risk','{:.2%}'.format(seniorrisk))
    with col18:
        st.metric('Junior tranche % total risk','{:.2%}'.format(juniorrisk))


    # fig = go.Figure(go.Bar(
    #             x = [juniorrisk,seniorrisk],
    #             y = ['Junior risk','Senior risk'],
    #             orientation = 'h'))
    # fig.update_layout(barmode='stack')
    # st.plotly_chart(fig,use_container_width=True)

    labels = ['Senior tranche','Junior tranche']
    values = [seniorrisk,juniorrisk]

    fig = make_subplots(rows=1,cols=2,specs=[[{'type':'domain'},{'type':'domain'}]])
    fig.add_trace(go.Pie(labels=labels,values=values,name='Risk split'),1,1)
    fig.add_trace(go.Pie(labels=labels,values=[1-junior[1]/100,junior[1]/100],name='Notional split'),1,2)
    fig.update_traces(hole=0.6,pull=[.2,0])
    fig.update_layout(
        title_text = 'Comparison between risk and notional split',
        annotations=[dict(text='Risk split',x=0.17,y=0.47,font_size=12,showarrow=False),
                    dict(text='Notional split',x=0.87,y=0.47,font_size=12,showarrow=False)],
        legend=dict(orientation='h'),
        template='ggplot2')


    st.plotly_chart(fig,use_container_width=True)

    st.subheader('Pricing parameters')

    if includeUF:
        margin = margin + upfront / tenor

    seniormargin = seniorrisk * (margin - funding - operations) / (1-junior[1]/100) + funding
    juniormargin = juniorrisk * (margin - funding - operations) / (junior[1]/100) + funding

    col19,col20,col21 = st.columns(3)
    with col19:
        st.metric('Margin portfolio','{:.2%}'.format(margin))
    with col20:
        st.metric('Margin for senior','{:.2%}'.format(seniormargin))
    with col21:
        st.metric('Margin for junior','{:.2%}'.format(juniormargin))

    fig = go.Figure([go.Bar(x=['Portfolio'],y=[margin],name='Portfolio'),
                    go.Bar(x=['Senior'],y=[seniormargin],name='Senior'),
                    go.Bar(x=['Junior'],y=[juniormargin],name='Junior')])
    fig.update_yaxes(tickformat=',.02%')
    fig.update_layout(
        title_text= 'Comparison of margin per tranche',
        template='ggplot2'
    )

    st.plotly_chart(fig,use_container_width=True)
