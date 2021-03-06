import pandas as pd
from matplotlib import style
import numpy as np
from sklearn import preprocessing, cross_validation, svm
from sklearn.linear_model import LinearRegression
from sklearn import tree
from sklearn.externals import joblib
import sqlite3
import sys, argparse, os
import csv, re, datetime, time
import matplotlib.pyplot as plt
import zerodha_option_series as db

def main(argv):
    np.set_printoptions(threshold=np.inf)
    input_glob = ''
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--database", nargs='?', default='./db/zerodha_pi.sqlite', help="Database to store series")
#    parser.add_argument("-i", "--input_glob", nargs='+', help="Input glob for series files")
    args = parser.parse_args()

    conn = db.initDB(args.database)
    cur = conn.cursor()

    x = db.getDictForSeries(cur, 'NIFTY', datetime.datetime(2016,6,28, 15, 30), 0, 'FUT' )
    df = x['Data']
    #df['PCT_CHG'] = (df['Close'] - df['Open']) / df['Close'] * 100
    df['PCT_MVMT_1MIN'] = (df['Close'] - df['Close'].shift(+1)) / df['Close'].shift(+1) * 100
    #print df['Close'] - df['Close'].shift(+1)
    df['PCT_MVMT_5MIN_POST'] = (df['Close'].shift(-5) - df['Close']) / df['Close'] * 100
    df['PCT_MVMT_2MIN'] = (df['Close'] - df['Close'].shift(2)) / df['Close'].shift(2) * 100
    df['PCT_MVMT_5MIN'] = (df['Close'] - df['Close'].shift(5)) / df['Close'].shift(5) * 100
    df = df[['PCT_MVMT_5MIN_POST', 'PCT_MVMT_1MIN' ,'PCT_MVMT_2MIN', 'PCT_MVMT_5MIN']]
    forecast_col = 'PCT_MVMT_5MIN_POST'
    #df.fillna(-99999, inplace=True)
    df.dropna(inplace=True)
    forecast_out = 0
    df.to_csv('calc.csv')
    df['label'] = df[forecast_col].shift(-forecast_out)

    X = np.array(df.drop(['label'],1))
    #X = preprocessing.scale(X)
    if (forecast_out):
        X = X[:-forecast_out]
    df.dropna(inplace=True)
    y = np.array(df['label'])
    samples = len(X)

    X_train, X_test, y_train, y_test = cross_validation.train_test_split(X, y, test_size=0.2)
    
    train_filename = datetime.datetime.now().strftime('%Y-%m-d %H:%M:%S') + '.pkl'
    clf = LinearRegression()
    clf.fit(X_train, y_train)
#    joblib.dump(clf, train_filename)
    #clf = joblib.load(train_filename) 
    accuracy = clf.score(X_test, y_test)
    print(accuracy)
    y_forecast = clf.predict(X_test)
    X = x['Data'].tail(samples)
    y = X['Close']
    X_train, X_test, y_train, y_test = cross_validation.train_test_split(X, y, test_size=0.2)
    y_forecast = y_forecast/100 * y_test + y_test
    print sum(abs(y_forecast - y_test))/len(y_test)
    plt.plot(np.arange(len(y_forecast)),y_forecast, 'r-')
    plt.plot(np.arange(len(y_forecast)), y_test, 'b')
    plt.show()

#    plt.plot(x['Data']['2016-05-24']['Close'])
#    plt.show()
    db.closeDB(conn)
    return 1

if __name__ == '__main__':

    sys.exit(int(main(sys.argv[1:]) or 0))