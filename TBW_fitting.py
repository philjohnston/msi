# -*- coding: utf-8 -*-
"""
TBW model fitting and SOA calculation
Created on Mon Jan  7 16:15:45 2019

@author: Phil
"""

#%%
import pandas as pd
import numpy as np
import os, sys
import matplotlib.pyplot as plt
from lmfit import Minimizer, Parameters, report_fit
from sympy.solvers import solve
from sympy import Symbol
from pylab import savefig
import pickle

#wd
os.chdir('C:/data/pjohnston/msi/')

#get subj number from command line
subj = str(sys.argv[1])

#check for existing output filename
output_filename = "data" + os.sep + "SOAs" + os.sep + "msi_a_sub" + subj + "_SOAs.csv"
if os.path.isfile(output_filename):
    sys.exit("Data for this subject already exists")

#load data
df = pd.read_csv('data' + os.sep + 'msi_a' + os.sep + 'msi_a_sub' + subj + '.csv')

#%% calculate synchrony rate
df_rate = pd.crosstab(index=df['SOA'], columns=df['resp_recode'], margins = True, margins_name = 'total')
df_rate['SOA'] = df_rate.index
df_rate['sync_rate'] = df_rate['sync']/df_rate['total']
df_rate = df_rate.drop(['total'], axis = 0)

#convert df_rate to float
df_rate = df_rate.astype('float')

#%%fit curves

#residual function (sigmoid)    
def residual(params, x, data):
    a = params['a']
    b = params['b']
    c = params['c']
    
    model = a / (1 + np.exp(-b * (x - c))) #sigmoid
    
    return model - data

#fit left curve
left_data_x = df_rate.SOA[df_rate.SOA <= 0]
left_data_y = df_rate.sync_rate[df_rate.SOA <= 0]

params = Parameters()
params.add('a', value = 1)
params.add('b', value = 0.01)
params.add('c', value = -150)

l_minner = Minimizer(residual, params, fcn_args=(left_data_x, left_data_y))
l_result = l_minner.minimize()

report_fit(l_result)

###extract left parameters from model
left_a = l_result.params['a'].value
left_b = l_result.params['b'].value
left_c = l_result.params['c'].value

###solve for left SOAs
x = Symbol('x')
ASOA50 = solve(left_a / (1 + 2.71828 ** (-left_b * (x - left_c))) - 0.5, x, rational = False)[0] #unclear why np.exp() doesn't work
ASOA95 = solve(left_a / (1 + 2.71828 ** (-left_b * (x - left_c))) - 0.05, x, rational = False)[0]

###generate left sigmoid line data
x_l_fun = np.linspace(-300, 0, 500)
y_l_fun = left_a / (1 + np.exp(-left_b * (x_l_fun - left_c)))

#fit right curve
right_data_x = df_rate.SOA[df_rate.SOA >= 0]
right_data_y = df_rate.sync_rate[df_rate.SOA >= 0]

params = Parameters()
params.add('a', value = 1)
params.add('b', value = -0.01)
params.add('c', value = 150)

r_minner = Minimizer(residual, params, fcn_args=(right_data_x, right_data_y))
r_result = r_minner.minimize()

report_fit(r_result)

###extract right parameters from model
right_a = r_result.params['a'].value
right_b = r_result.params['b'].value
right_c = r_result.params['c'].value

###solve for SOAs
x = Symbol('x')
VSOA50 = solve(right_a / (1 + 2.71828 ** (-right_b * (x - right_c))) - 0.5, x, rational = False)[0] #unclear why np.exp() doesn't work
VSOA95 = solve(right_a / (1 + 2.71828 ** (-right_b * (x - right_c))) - 0.05, x, rational = False)[0]

###generate right sigmoid line data
x_r_fun = np.linspace(0, 300, 500)
y_r_fun = right_a / (1 + np.exp(-right_b * (x_r_fun - right_c)))


# try to plot results
try:
    #original data
    plt.plot(left_data_x, left_data_y, 'ko')
    plt.plot(right_data_x, right_data_y, 'ko')
    
    #plot sigmoid
    plt.plot(x_l_fun, y_l_fun, 'b')
    plt.plot(x_r_fun, y_r_fun, 'b')
    
    #plot SOAs and annotate
    plt.plot(ASOA50, 0.5, 'k+')
    plt.annotate(str(round(ASOA50,2)), (ASOA50, 0.5))
    plt.plot(ASOA95, 0.05, 'k+')
    plt.annotate(str(round(ASOA95,2)), (ASOA95, 0.05))
    plt.plot(VSOA50, 0.5, 'k+')
    plt.annotate(str(round(VSOA50,2)), (VSOA50, 0.5))
    plt.plot(VSOA95, 0.05, 'k+')
    plt.annotate(str(round(VSOA95,2)), (VSOA95, 0.05))
    
    #format plot
    plt.title('msi_a_sub' + subj)
    plt.ylabel('Rate of synchrony perception')
    plt.xlabel('SOA (ms)')
    plt.draw()
    
    #save plot
    savefig('data' + os.sep + 'plots' + os.sep + 'msi_a_sub' + subj + '_TBW.png', bbox_inches='tight')
except ImportError:
    pass

#save SOAs and rounded SOAs (nearest multiple of 10) to csv
SOA_out = pd.DataFrame({'ASOA95':[ASOA95], 'ASOA50':[ASOA50], 'VSOA50':[VSOA50], 'VSOA95':[VSOA95], 
                        'ASOA95r':[round(ASOA95, -1)], 'ASOA50r':[round(ASOA50, -1)], 'VSOA50r':[round(VSOA50, -1)], 'VSOA95r':[round(VSOA95, -1)]})
SOA_out.to_csv(output_filename)

#pickle fit results objects
with open('data' + os.sep + "fit_results" + os.sep + "msi_a_sub" + subj + "_left_fit.pickle", "wb") as output_file:
    pickle.dump(l_result, output_file)

with open('data' + os.sep + "fit_results" + os.sep + "msi_a_sub" + subj + "_right_fit.pickle", "wb") as output_file:
    pickle.dump(r_result, output_file)

#print SOAs and show plot
print(SOA_out)
plt.show()


