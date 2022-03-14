from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User, auth
from django.http import JsonResponse
from .models import Holdings, Graphs
from nsetools import Nse
# from nsepython import *
# import plotly.graph_objects as go
# import plotly.offline as opy
import matplotlib.pyplot as plt
from io import StringIO, BytesIO
import numpy as np
import pandas as pd
import pandas_datareader as web
import datetime as dt
import tensorflow as tf
from tensorflow import keras
from sklearn.preprocessing import MinMaxScaler
import os
import requests
from mftool import Mftool


def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = auth.authenticate(username=email, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('index')
        else:
            messages.info(request, 'Invalid Credentials')
            return redirect('login')
    else:
        return render(request, 'login.html', {})


def index(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user = request.user
    h = Holdings.objects.get(usid=user.id)

    if request.method == 'POST':
        # if 'AddFile' in request.POST:
        if request.FILES.get('stockFile', False):
            try:
                file1 = request.FILES['stockFile']
            except Exception as e:
                messages.warning(request, 'No file selected! Upload again')
                return redirect('index')
            if(file1.name[-3:] != 'csv'):
                messages.warning(
                    request, 'File extension error! Upload .csv file')
            elif(file1.size > 2500000):
                messages.warning(
                    request, 'File size error! Size should be less than 2.5Mb')
            else:
                # file1r = file1.read()
                filecsv = pd.read_csv(file1)
                fsyml = []
                fqtyl = []
                fabpl = []
                fsecl = []
                fltpl = []
                Nseo = Nse()
                for index, row in filecsv.iterrows():
                    try:
                        fsym = filecsv.iloc[index, 0]
                        fsym = fsym.upper()
                        if Nseo.is_valid_code(fsym) == False:
                            continue
                    except:
                        continue
                    try:
                        fqty = int(filecsv.iloc[index, 1])
                        if(pd.isnull(fqty)):
                            continue
                    except:
                        continue
                    try:
                        fabp = float(filecsv.iloc[index, 2])
                        if(pd.isnull(fabp)):
                            continue
                    except:
                        continue
                    try:
                        fsec = filecsv.iloc[index, 3]
                        fsec = fsec.capitalize()
                        sectors = ["Finance", "IT & Digital", "Pharma", "Consumer",
                                   "Infra", "Auto", "Power", "Chemical", "Other"]
                        if(pd.isnull(fsec) or fsec == '' or (fsec not in sectors)):
                            if fsym in h.data.get('symbol', []):
                                index = h.data.get('symbol', []).index(fsym)
                                fsec = h.data['sector'][index]
                            else:
                                fsec = 9
                        else:
                            fsec = int(sectors.index(fsec)) + 1
                    except:
                        if fsym in h.data.get('symbol', []):
                            index = h.data.get('symbol', []).index(fsym)
                            fsec = h.data['sector'][index]
                        else:
                            fsec = 9
                    URLst = 'https://groww.in/v1/api/stocks_data/v1/accord_points/exchange/NSE/segment/CASH/latest_prices_ohlc/' + fsym
                    try:
                        rf = requests.get(URLst, timeout=10)
                        if rf.ok:
                            fltp = rf.json()['ltp']
                        else:
                            fltp = 0
                    except Exception as e:
                        fltp = 0
                    fsyml.append(fsym)
                    fqtyl.append(fqty)
                    fabpl.append(fabp)
                    fsecl.append(fsec)
                    fltpl.append(fltp)
                    # print(fsym, fqty, fabp, fsec)
                h.data['symbol'] = fsyml
                h.data['net_qty'] = fqtyl
                h.data['avg_price'] = fabpl
                h.data['sector'] = fsecl
                h.data['ltp'] = fltpl
                h.save()
                messages.success(request, 'Data Updated!')
            return redirect('index')
        else:
            messages.warning(request, 'No file selected! Upload again')
            return redirect('index')

    # Nseo = Nse()
    holdings_size = int(len(h.data.get('symbol', [])))
    h_sym = h.data.get('symbol', [])
    h_qty = h.data.get('net_qty', [])
    h_price = h.data.get('avg_price', [])
    h_ov = [float('{:.2f}'.format(a * b)) for a, b in zip(h_qty, h_price)]
    h_ltp = h.data.get('ltp', [])
    h_sect = h.data.get('sector', [])
    sectors = ["Finance", "IT & Digital", "Pharma", "Consumer",
               "Infra", "Auto", "Power", "Chemical", "Other"]
    h_sector = []
    for i in range(0, holdings_size):
        h_sector.append(sectors[h_sect[i] - 1])
    h_cv = [float("{:.2f}".format(a * b)) for a, b in zip(h_qty, h_ltp)]
    h_pl = [float("{:.2f}".format(a - b)) for a, b in zip(h_cv, h_ov)]
    h_plp = [float("{:.2f}".format(a * 100 / b)) for a, b in zip(h_pl, h_ov)]
    pl_total = float("{:.2f}".format(sum(h_pl)))
    if sum(h_ov) == 0:
        pl_prcnt = 0
    else:
        pl_prcnt = float("{:.2f}".format(pl_total * 100.0 / sum(h_ov)))

    URL_sen = 'https://groww.in/v1/api/stocks_data/v1/accord_points/exchange/BSE/segment/CASH/latest_indices_ohlc/SENSEX'
    URL_nif = 'https://groww.in/v1/api/stocks_data/v1/accord_points/exchange/NSE/segment/CASH/latest_indices_ohlc/NIFTY'

    try:
        rsen = requests.get(URL_sen, timeout=10)
        if rsen.ok:
            sensex_lp = rsen.json()['value']
        else:
            sensex_lp = 0
    except Exception as e:
        sensex_lp = 0

    try:
        rnif = requests.get(URL_nif, timeout=10)
        if rnif.ok:
            nifty_lp = rnif.json()['value']
        else:
            nifty_lp = 0
    except Exception as e:
        nifty_lp = 0

    # rsen = requests.get(URL_sen, timeout=10)
    # rnif = requests.get(URL_nif, timeout=10)
    # if rsen.ok:
    #    sensex_lp = rsen.json()['value']
    # else:
    #    sensex_lp = 60000
    # if rnif.ok:
    #    nifty_lp = rnif.json()['value']
    # else:
    #    nifty_lp = 18000

    # URL_ind = "https://www1.nseindia.com/homepage/Indices1.json"
    # rind = requests.get(URL_ind)
    # if rind.ok:
    #    data_ind = rind['data']
    #    nifty_lp = data_ind[1]['lastPrice']
    #    niftybank_lp = data_ind[5]['lastPrice']
    # else:
    #    nifty_lp = 18200  # Nseo.get_index_quote("nifty 50")['lastPrice']
    #    niftybank_lp = 39000  # Nseo.get_index_quote("nifty bank")['lastPrice']
    g = Graphs.objects.get(usid=user.id)
    graph1 = g.g1
    graph2 = g.g2
    return render(request, 'index.html', {'graph1': graph1, 'graph2': graph2, 'nifty_lp': nifty_lp, 'sensex_lp': sensex_lp, 'pl_total': pl_total, 'pl_prcnt': pl_prcnt, 'h_sym': h_sym, 'h_qty': h_qty, 'h_price': h_price, 'h_ov': h_ov, 'h_ltp': h_ltp, 'h_cv': h_cv, 'h_pl': h_pl, 'h_plp': h_plp, 'h_sector': h_sector, 'range': list(range(holdings_size))})


def save_data(request):
    user = request.user
    h = Holdings.objects.get(usid=user.id)

    if request.method == 'POST':
        sym = str(request.POST['symbol'])
        sym = sym.upper()
        rp_qty = str(request.POST['qty'])
        rp_price = str(request.POST['price'])
        rp_sector = str(request.POST['sector'])
        if sym == '' or rp_qty == '' or rp_price == '' or rp_sector == '':
            messages.info(request, 'Fill all fields!')
            return JsonResponse({'status': 0})
        Nseo = Nse()
        if Nseo.is_valid_code(sym):
            if sym in h.data.get('symbol', []):
                index = h.data.get('symbol', []).index(sym)
                if (h.data['net_qty'][index] + int(request.POST['qty'])) != 0:
                    if (int(request.POST['qty']) > 0):
                        h.data['avg_price'][index] = (h.data['avg_price'][index] * h.data['net_qty'][index] + int(
                            request.POST['price']) * int(request.POST['qty'])) / (h.data['net_qty'][index] + int(request.POST['qty']))
                    h.data['net_qty'][index] = h.data['net_qty'][index] + \
                        int(request.POST['qty'])
                    h.data['sector'][index] = int(request.POST['sector'])
                    h.save()
                else:
                    h.data['symbol'].pop(index)
                    h.data['net_qty'].pop(index)
                    h.data['avg_price'].pop(index)
                    h.data['sector'].pop(index)
                    h.data['ltp'].pop(index)
                    h.save()
            else:
                h.data['symbol'] = h.data.get('symbol', []) + [sym]
                h.data['net_qty'] = h.data.get(
                    'net_qty', []) + [int(request.POST['qty'])]
                h.data['avg_price'] = h.data.get(
                    'avg_price', []) + [int(request.POST['price'])]
                h.data['sector'] = h.data.get(
                    'sector', []) + [int(request.POST['sector'])]
                URLst = 'https://groww.in/v1/api/stocks_data/v1/accord_points/exchange/NSE/segment/CASH/latest_prices_ohlc/' + sym

                try:
                    r3 = requests.get(URLst, timeout=10)
                    if r3.ok:
                        stltp = r3.json()['ltp']
                    else:
                        stltp = 0
                except Exception as e:
                    stltp = 0

                # r3 = requests.get(URLst)
                # if r3.ok:
                #    stltp = r3.json()['ltp']
                # else:
                #    stltp = 0

                h.data['ltp'] = h.data.get(
                    'ltp', []) + [float(stltp)]
                h.save()

            nhd = h.data
            return JsonResponse({'status': 1, 'nhd': nhd})

        messages.info(request, 'Invalid Symbol!')
        return JsonResponse({'status': 0})

    return JsonResponse({'status': 0})


def save_data2(request):
    user = request.user
    h = Holdings.objects.get(usid=user.id)

    if request.method == 'POST':
        sch = str(request.POST['schemeId'])
        amt = str(request.POST['invAmt'])
        unt = str(request.POST['units'])
        if sch == '' or amt == '' or unt == '':
            messages.info(request, 'Fill all fields!')
            return JsonResponse({'status': 0})
        mf = Mftool()
        if mf.is_valid_code(sch):
            schn = mf.get_scheme_quote(sch)['scheme_name']
            if schn in h.data2.get('schemeId', []):
                index = h.data2.get('schemeId', []).index(schn)
                if (h.data2['units'][index] + float(request.POST['units'])) != 0:
                    h.data2['units'][index] = (
                        h.data2['units'][index] + float(request.POST['units']))
                    h.data2['invAmt'][index] = (
                        h.data2['invAmt'][index] + float(request.POST['invAmt']))
                    h.save()
                else:
                    h.data2['schemeId'].pop(index)
                    h.data2['invAmt'].pop(index)
                    h.data2['units'].pop(index)
                    h.data2['nav'].pop(index)
                    h.data2['schemeCd'].pop(index)
                    h.save()
            else:
                h.data2['schemeId'] = h.data2.get('schemeId', []) + [schn]
                h.data2['invAmt'] = h.data2.get(
                    'invAmt', []) + [float(request.POST['invAmt'])]
                h.data2['units'] = h.data2.get(
                    'units', []) + [float(request.POST['units'])]
                h.data2['nav'] = h.data2.get(
                    'nav', []) + [float(mf.get_scheme_quote(sch)['nav'])]
                h.data2['schemeCd'] = h.data2.get('schemeCd', []) + [sch]
                h.save()

            nhd = h.data2
            return JsonResponse({'status': 1, 'nhd': nhd})

        messages.info(request, 'Invalid Scheme Id !')
        return JsonResponse({'status': 0})

    return JsonResponse({'status': 0})


def register(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 == password2:
            if User.objects.filter(email=email).exists():
                messages.info(
                    request, 'Email Already Registered! Proceed to Login!')
                return redirect('register')
            else:
                user = User.objects.create_user(
                    username=email, password=password1, email=email, first_name=first_name, last_name=last_name)
                user.save()
                holding = Holdings()
                holding.usid = user.id
                holding.save()
                graph = Graphs()
                graph.usid = user.id
                graph.save()
                return redirect('/')
        else:
            messages.info(request, 'Passwords not matching')
            return redirect('register')

    else:
        return render(request, 'register.html', {})


def logout(request):
    auth.logout(request)
    return redirect('login')


def password(request):
    return render(request, 'password.html', {})


def refresh_charts(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user = request.user
    h = Holdings.objects.get(usid=user.id)
    # Nseo = Nse()
    holdings_size = int(len(h.data.get('symbol', [])))
    h_sym = h.data.get('symbol', [])
    h_qty = h.data.get('net_qty', [])
    h_price = h.data.get('avg_price', [])
    h_sector = h.data.get('sector', [])
    h_ltp = []
    for i in range(holdings_size):
        URLst = 'https://groww.in/v1/api/stocks_data/v1/accord_points/exchange/NSE/segment/CASH/latest_prices_ohlc/' + \
            h_sym[i]

        try:
            r3 = requests.get(URLst, timeout=10)
            if r3.ok:
                stltp = r3.json()['ltp']
            else:
                stltp = 0
        except Exception as e:
            stltp = 0

        # r3 = requests.get(URLst)
        # if r3.ok:
        #    stltp = r3.json()['ltp']
        # else:
        #    stltp = 0

        h_ltp.append(stltp)
        # h_ltp.append(Nseo.get_quote(h_sym[i])['lastPrice'])
    h.data['ltp'] = h_ltp
    h.save()

    h_ov = [a * b for a, b in zip(h_qty, h_price)]
    h_cv = [a * b for a, b in zip(h_qty, h_ltp)]
    h_pl = [a - b for a, b in zip(h_cv, h_ov)]

    sectors = ["Finance", "IT & Digital", "Pharma", "Consumer",
               "Infra", "Auto", "Power", "Chemical", "Other"]
    sector_ov = [0] * 9
    sector_cv = [0] * 9
    sector_pl = [0] * 9
    for i in range(holdings_size):
        sector_ov[h_sector[i] - 1] += h_ov[i]
        sector_cv[h_sector[i] - 1] += h_cv[i]
    for i in range(9):
        sector_pl[i] = sector_cv[i] - sector_ov[i]

    nz_sec = []
    nz_ov = []
    nz_cv = []
    nz_pl = []
    for i in range(9):
        if sector_ov[i] != 0:
            nz_sec.append(sectors[i])
            nz_ov.append(sector_ov[i])
            nz_cv.append(sector_cv[i])
            nz_pl.append(nz_cv[-1] - nz_ov[-1])

    fig1, ax = plt.subplots(figsize=(6, 3), subplot_kw=dict(aspect="equal"))
    circ = plt.Circle((0, 0), 0.45, color='white')
    ex = [0.01] * len(nz_sec)
    wedges, texts, autotexts = ax.pie(nz_ov, startangle=0, autopct='%1.0f%%',
                                      wedgeprops={'linewidth': 1.5, 'edgecolor': 'white'}, pctdistance=0.65, explode=ex)
    plt.gcf().gca().add_artist(circ)
    ax.legend(wedges, nz_sec, title="Sectors",
              loc="center left", bbox_to_anchor=(1, 0, 0, 1))
    plt.setp(autotexts, size=9, weight="bold")
    fig1.set_size_inches(6.5, 2.8)
    img1data = StringIO()
    fig1.savefig(img1data, transparent=True,
                 bbox_inches='tight', pad_inches=0, format='svg')
    img1data.seek(0)
    data1 = img1data.getvalue()

    fig2 = plt.figure()
    plt.bar(nz_sec, nz_pl)
    fig2.set_size_inches(6.5, 2.5)
    img2data = StringIO()
    fig2.savefig(img2data, transparent=True,
                 bbox_inches='tight', pad_inches=0, format='svg')
    img2data.seek(0)
    data2 = img2data.getvalue()

    # fig2 = go.Figure(
    # data=[go.Pie(labels=nz_sec, values=nz_ov, hole=.3, pull=[0.03] * len(nz_sec))])
    # fig2.update_traces(textfont={'size': 13, 'family': 'Verdana'})
    # data2 = opy.plot(fig2, auto_open=False, output_type='div')

    g = Graphs.objects.get(usid=user.id)
    g.g1 = data1
    g.g2 = data2
    g.save()
    return redirect('index')


def predictor(request):
    if not request.user.is_authenticated:
        return redirect('login')
    data = ""
    if request.method == "POST":
        sym = str(request.POST.get('symbol'))
        sym = sym.upper()
        Nseo = Nse()
        end = dt.date.today()
        start = end - dt.timedelta(days=300)
        if Nseo.is_valid_code(sym):
            sym = sym + ".BSE"
        else:
            messages.info(request, 'Invalid Symbol!')
            return render(request, 'predictor.html', {'graph': data})
        # df = web.DataReader(sym, 'yahoo', start, end)
        # df = web.DataReader(sym, "av-daily", start=start,
        #                end=end, api_key='CT48RJJ2SKTGSNT4')
        try:
            df = web.DataReader(sym, "av-daily", start=start,
                                end=end, api_key='CT48RJJ2SKTGSNT4')
        except Exception as e:
            messages.info(request, 'Cannot Fetch Data!')
            return render(request, 'predictor.html', {'graph': data})

        df1 = df.reset_index()['close']

        df1 = df1.tail(200)
        reconstructed_model = tf.keras.models.load_model(
            'stockapp/my_model.h5')
        test_df_ns = np.array(df1).reshape(200, 1)
        scaler3 = MinMaxScaler(feature_range=(0, 1))
        test_df_s = scaler3.fit_transform(test_df_ns)
        x_input = test_df_s.reshape(1, -1)
        temp_input = list(x_input)
        temp_input = temp_input[0].tolist()
        lst_output = []
        n_steps = 200
        i = 0
        while(i < 60):
            if len(temp_input) > 200:
                x_input = np.array(temp_input[1:])
                x_input = x_input.reshape(1, -1)
                x_input = x_input.reshape((1, n_steps, 1))
                yhat = reconstructed_model.predict(x_input, verbose=0)
                temp_input.extend(yhat[0].tolist())
                temp_input = temp_input[1:]
                lst_output.extend(yhat.tolist())
                i = i + 1
            else:
                x_input = x_input.reshape((1, n_steps, 1))
                yhat = reconstructed_model.predict(x_input, verbose=0)
                temp_input.extend(yhat[0].tolist())
                lst_output.extend(yhat.tolist())
                i = i + 1
        df3 = df1.values.tolist()
        df3.extend(scaler3.inverse_transform(lst_output))
        x1 = list(range(200))
        x2 = [201 + ele for ele in list(range(60))]
        # plt.plot(df3)

        # figp = plt.figure()
        # plt.plot(df1)
        figp = plt.figure()
        plt.plot(x1, df3[:200])
        plt.plot(x2, df3[200:], 'green')
        imgdata = StringIO()
        figp.savefig(imgdata, transparent=True,
                     bbox_inches='tight', pad_inches=0, format='svg')
        imgdata.seek(0)
        data = imgdata.getvalue()
        # print(reconstructed_model)
    return render(request, 'predictor.html', {'graph': data})


def refresh_funds(request):
    user = request.user
    h = Holdings.objects.get(usid=user.id)
    holdings_size = int(len(h.data2.get('schemeId', [])))
    h_schC = h.data2.get('schemeCd', [])
    h_nav = h.data2.get('nav', [])
    mf = Mftool()
    for i in range(holdings_size):
        h_nav[i] = float(mf.get_scheme_quote(h_schC[i])['nav'])
    h.save()
    return redirect('mfunds')


def mfunds(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user = request.user
    h = Holdings.objects.get(usid=user.id)
    # Nseo = Nse()
    holdings_size = int(len(h.data2.get('schemeId', [])))
    h_sch = h.data2.get('schemeId', [])
    h_schC = h.data2.get('schemeCd', [])
    h_amt = h.data2.get('invAmt', [])
    h_unt = h.data2.get('units', [])
    h_nav = h.data2.get('nav', [])
    # mf = Mftool()
    # for i in range(holdings_size):
    # h_nav[i] = float(mf.get_scheme_quote(h_schC[i])['nav'])
    h_cv = [float("{:.2f}".format(a * b)) for a, b in zip(h_unt, h_nav)]
    h_pl = [float("{:.2f}".format(a - b)) for a, b in zip(h_cv, h_amt)]
    h_plp = [float("{:.2f}".format(a * 100 / b)) for a, b in zip(h_pl, h_amt)]
    pl_total = sum(h_pl)
    if sum(h_amt) == 0:
        pl_prcnt = 0
    else:
        pl_prcnt = float("{:.2f}".format(pl_total * 100.0 / sum(h_amt)))
    # nifty_lp = Nseo.get_index_quote("nifty 50")['lastPrice']
    # niftybank_lp = Nseo.get_index_quote("nifty bank")['lastPrice']
    t_amt = sum(h_amt)
    t_cv = t_amt + pl_total
    # g = Graphs.objects.get(usid=user.id)
    # graph1 = g.g1
    # graph2 = g.g2
    return render(request, 'mfunds.html', {'t_amt': t_amt, 't_cv': t_cv, 'pl_total': pl_total, 'pl_prcnt': pl_prcnt, 'h_schC': h_schC, 'h_sch': h_sch, 'h_amt': h_amt, 'h_unt': h_unt, 'h_nav': h_nav, 'h_cv': h_cv, 'h_pl': h_pl, 'h_plp': h_plp, 'range': list(range(holdings_size))})


def mfholding(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user = request.user
    h = Holdings.objects.get(usid=user.id)
    holdings_size = int(len(h.data2.get('schemeId', [])))
    h_sch = h.data2.get('schemeCd', [])
    h_unt = h.data2.get('units', [])
    h_nav = h.data2.get('nav', [])
    h_cv = [float("{:.2f}".format(a * b)) for a, b in zip(h_unt, h_nav)]
    
    if(len(h_sch) == 0):
        hldgs = {}
        data1 = "No Data! Add Mutual Funds in your portfolio for analysis!"
        return render(request, 'mfholding.html', {'hdata': hldgs, 'graph1': data1})
    
    URL2 = "https://www.amfiindia.com/spages/NAVOpen.txt"
    try:
        r2 = requests.get(URL2, timeout=10).text
    except Exception as e:
        hldgs = {}
        data1 = "Cannot Fetch Data!"
        return render(request, 'mfholding.html', {'hdata': hldgs, 'graph1': data1})

    # print(r2)
    dat2 = r2
    isin_list = []
    for amficd in h_sch:
        fi = dat2.find(amficd)
        # print(dat2[fi + 7:fi + 19])
        isin_list.append(dat2[fi + 7:fi + 19])

    sec_amt = {}
    hldgs = {}
    inv_amt = h_cv
    data_list = []
    for i in range(len(isin_list)):
        isin_it = isin_list[i]
        # print(isin_it)
        try:
            data_list.append(requests.get(
                'https://staticassets.zerodha.com/coin/scheme-portfolio/' + isin_it + '.json', timeout=10).json())
        except Exception as e:
            hldgs = {}
            data1 = "Cannot Fetch Data!"
            return render(request, 'mfholding.html', {'hdata': hldgs, 'graph1': data1})
    for i in range(len(data_list)):
        data_it = data_list[i]
        for stck in data_it['data']:
            stck_name = stck[1]
            if(stck_name[-4:] == 'Ltd.' or stck_name[-3:] == 'Ltd'):
                stck_name = stck_name[:-4] + 'Limited'
            stck_pr = stck[5]
            stck_sec = stck[2]
            if(stck_sec == ''):
                stck_sec = 'Other'
            if(stck_pr >= 0.1 and stck_sec in sec_amt):
                sec_amt[stck_sec] = sec_amt[stck_sec] + \
                    inv_amt[i] * stck_pr / 100
            elif(stck_pr >= 0.1):
                sec_amt[stck_sec] = inv_amt[i] * stck_pr / 100
            stck_name = stck_name.upper()
            if(stck_pr >= 0.1 and stck_name in hldgs):
                hldgs[stck_name] = hldgs[stck_name] + \
                    float("{:.2f}".format(inv_amt[i] * stck_pr / 100))
            elif(stck_pr >= 0.1):
                hldgs[stck_name] = float(
                    "{:.2f}".format(inv_amt[i] * stck_pr / 100))

    sects = []
    amts = []
    for x, y in sec_amt.items():
        sects.append(x)
        amts.append(y)
    tamts = sum(amts)
    if tamts == 0:
        tamts = 1
    amts, sects = (list(t)
                   for t in zip(*sorted(zip(amts, sects), reverse=True)))
    fig1 = plt.figure()
    col_map = plt.get_cmap('Paired')
    pl = plt.bar(sects, amts, color=col_map.colors)
    plt.xticks(sects, rotation='vertical')
    i = 0
    for p in pl:
        width = p.get_width()
        height = p.get_height()
        gx, gy = p.get_xy()
        plt.text(gx + width / 2, gy + height * 1.01, str("{0:.1f}".format(amts[i] * 100 / tamts)) + '%',
                 ha='center')
        i += 1
    # plt.legend(sects, ncol=3)
    fig1.set_size_inches(15, 6)
    img1data = StringIO()
    fig1.savefig(img1data, transparent=True,
                 bbox_inches='tight', pad_inches=0, format='svg')
    img1data.seek(0)
    data1 = img1data.getvalue()
    # print(hldgs)
    return render(request, 'mfholding.html', {'hdata': hldgs, 'graph1': data1})


def deleq(request):
    if not request.user.is_authenticated:
        return redirect('login')

    user = request.user
    h = Holdings.objects.get(usid=user.id)
    h.data['symbol'] = []
    h.data['net_qty'] = []
    h.data['avg_price'] = []
    h.data['ltp'] = []
    h.data['sector'] = []
    h.save()
    g = Graphs.objects.get(usid=user.id)
    g.g1 = ""
    g.g2 = ""
    g.save()

    messages.info(request, "Equity portfolio data deleted!")
    return redirect("settings")


def delmf(request):
    if not request.user.is_authenticated:
        return redirect('login')

    user = request.user
    h = Holdings.objects.get(usid=user.id)
    h.data2['schemeId'] = []
    h.data2['invAmt'] = []
    h.data2['units'] = []
    h.data2['nav'] = []
    h.data2['schemeCd'] = []
    h.save()

    messages.info(request, "Mutual Fund portfolio data deleted!")
    return redirect("settings")


def settings(request):
    if not request.user.is_authenticated:
        return redirect('login')

    user = request.user

    if request.method == 'POST':
        ufname = str(request.POST['ufname'])
        ulname = str(request.POST['ulname'])
        #uemail = str(request.POST['uemail'])
        #uphone = str(request.POST['uphone'])
        upass = str(request.POST['upass'])
        ucpass = str(request.POST['ucpass'])

        if(ufname != "" and user.first_name != ufname):
            user.first_name = ufname
        if(ulname != "" and user.last_name != ulname):
            user.last_name = ulname
        # Add email and phone option later
        if(upass != "" and upass == ucpass):
            user.set_password(upass)
        elif(upass != ""):
            messages.warning(request, "Passwords don't match!")
        user.save()
        messages.success(request, "Profile Updated!")
        return redirect('settings')

    return render(request, 'settings.html', {})

# def mfh_charts(request):  #For Additional plots for holdings analysis
#    if request.method == "POST":
#    return JsonResponse({'status': 1})


# UI improvements
# Graph sizes relative to screen size / Make graph using data in JS
# Interactive graphs using mpld3/plotly
#
# Settings page contact feedback option
# Forget Password during login
#
# Seperate collection for user meta(request.META) info + phone
#
# Modify Login Page as Landing Home Page
#
# New Common Dasboard with daily news/movers etc as landing db, seperate equities and mf areas
#
# MF HOlding analysis add columns like %change(p/l) or something
# Update cards UI / dropdown of diff stats : total invested, current values, etc.
#
# Counter for monthly clicks on add-ons for premium
# Revamp UI, kind of like smallcase
# Make client side improvements using ajax/js
# Google Auth and Crawler pe update


# Hints:
# https://www.nseindia.com/api/quote-equity?symbol=xyz   <== nse api link
# TO make changes to model, delete migrations folder, delete collection holdings and graphs from mongodb and delete all users also from author
# Then save models.py , do python manage.py makemigrations stockapp, #python manage.py migrate --fake stockapp zero#, python manage.py migrate stockapp
# MongoDB login with google 123 gmail
# For mf holding analysis, used zerodha link found on inspect element network tab fetch/XHR tab .json link on zerodha mf(say kotak emerging) website
# Using ATOM inbuilt terminal, powershell opens type ->cmd, workon test, python manage.py runserver
