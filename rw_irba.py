import numpy as np
from scipy import stats
import pandas as pd


def rw_irba(pd,lgd,mat,avc):

    if mat <1:
        mat = 1
    elif mat > 5:
        mat = 5

#AVC multiplier
    if avc==True:
        avcmult = 1.25
    else:
        avcmult = 1

#Correlation
    correl = avcmult * (0.12*(1-np.exp(-50*pd))/(1-np.exp(-50))+0.24*(1-np.exp(-50*pd))/ (1-np.exp(-50)))

#Maturity adjustment
    b = (0.11852 - 0.05478*np.log(pd))**2

    matadj = (1+(mat-2.5)*b)/(1-1.5*b)

idiosyncratic = stats.norm.ppf(pd)*((1-correl)**(-0.5))
systemic = stats.norm.ppf(0.999)*(correl / (1-correl))**0.5

#Capital requirement
    K = lgd * (stats.norm.cdf(idiosyncratic+systemic)-pd)*matadj

    return K * 12.5

# Loan pricing

roe = 0.1
funding = 0.015
ops = 0.003
rating,loss,tenor,financial=0.01,0.3,5,False

def grossmar(pd,lgd,mat,cof):
    return rw_irba(pd,lgd,mat,False)*0.1*roe + pd*lgd+cof+ops

#print('The risk weight for the loan is'+str(rw_irba(rating,loss,tenor,financial)))
#print('The gross margin required is '+str(grossmar(rating,loss,tenor,funding)))
