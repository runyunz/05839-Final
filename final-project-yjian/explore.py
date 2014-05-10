import httplib2
from apiclient.discovery import build
import urllib
import json
import csv
import matplotlib.pyplot as plt 
import collections

# This API key is provided by google as described in the tutorial
API_KEY = 'AIzaSyAGNJUbVZRN0M_3BADuMiwbEmynJcZ53QI'

TABLE_ID = '1mSdQLhEFvH8ENi5dGoNXuXO1Lxd9wON349o2szE'
# open the data stored in a file called "data.json"
    

if __name__ == '__main__':
    service = build('fusiontables', 'v1', developerKey=API_KEY)
    #query = "SELECT * FROM " + TABLE_ID + " WHERE  AnimalType = 'DOG'"
    #query = "SELECT ZipFound, ZipPlaced FROM " + TABLE_ID
    query = "SELECT 'YearReport','State' FROM " + TABLE_ID
    data = service.query().sql(sql=query).execute()
    columns = data['columns']
    rows = data['rows']

    year_id = columns.index(u'YearReport')
    state_id = columns.index(u'State')
    states_year_occr = {}
    data_ret = []

    for row in rows: 
        year = row[year_id]
        state = row[state_id]
        year_occr = states_year_occr.get(state)
        if year_occr is not None:
            if year in ['', '1995', '1996', '1997']:
                continue
            if year_occr.get(year):
                year_occr[year] += 1
            else:
                year_occr[year] = 1
        else:
            states_year_occr[state] = {year : 1}
        
    for st, yr_oc in states_year_occr.iteritems():
        if st == 'Ca':
            continue
        res = {}
        res['name'] = st
        tmp = []
        total = 0
        for yr, oc in yr_oc.iteritems():
            tmp.append([yr, oc])
            total += oc
        res['events'] = tmp
        res['total'] = total
        data_ret.append(res)
    newlist = sorted(data_ret, key=lambda k: k['total'], reverse=True) 
    f = open("data/auxi.json")
    obj = json.load(f)
    for item in newlist:
        name = item.get('name')
        for o in obj:
            if name == o.get('name'):
                item['newstitle'] = o.get('event')
                item['newslink'] = o.get('link')
                item['img'] = o.get('img')
    fp = open("data/data.json", "w+")
    json.dump(newlist, fp)
