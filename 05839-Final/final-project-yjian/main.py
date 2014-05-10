#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
from webapp2_extras import jinja2

from google.appengine.api import files
from google.appengine.api import memcache
from apiclient.discovery import build
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from oauth2client.appengine import AppAssertionCredentials 
from django.utils import simplejson
from google.appengine.ext.webapp import template
import httplib2
import urllib

import logging, os, math


# BigQuery API Settings
_PROJECT_NUMBER        = '883955795680' 

# Define your production Cloud SQL instance information. 
_DATABASE_NAME = 'githubarchive:github.timeline'

logging.info("setting up credentials")
credentials = AppAssertionCredentials(scope='https://www.googleapis.com/auth/bigquery')
http        = credentials.authorize(httplib2.Http(memcache))
service     = build("bigquery", "v2", http=http)
logging.info("done setting up credentials")

# we are adding a new class that will 
# help us to use jinja. MainHandler will sublclass this new
# class (BaseHandler), and BaseHandler is in charge of subclassing
# webapp2.RequestHandler  
class BaseHandler(webapp2.RequestHandler):
    @webapp2.cached_property
    def jinja2(self):
        # Returns a Jinja2 renderer cached in the app registry.
        return jinja2.get_jinja2(app=self.app)
        
    # lets jinja render our response
    def render_response(self, _template, context):
        values = {'url_for': self.uri_for}
        #logging.info(context)
        values.update(context)
        self.response.headers['Content-Type'] = 'text/html'

        # Renders a template and writes the result to the response.
        rv = self.jinja2.render_template(_template, **values)
        self.response.headers['Content-Type'] = 'text/html; charset=utf-8'
        self.response.write(rv)

class MainHandler(BaseHandler):
    def run_query(self, query_string, timeout=100000):
		if (os.getenv('SERVER_SOFTWARE') and
			os.getenv('SERVER_SOFTWARE').startswith('Google App Engine/')):
			# set up the query 
			query = {'query':query_string, 'timeoutMs':timeout}
			# service is the oauth2 setup that we created above
			jobCollection = service.jobs()
			# project number is the project number you should have 
			# defined in your app
			return jobCollection.query(projectId=_PROJECT_NUMBER,body=query).execute()
		else:
			return None

    def prepare_data(self):
        start_date = "2014-04-01"
        end_date = "2014-05-08"
        query_string = "SELECT repository_language, count(*) as ct \
                        FROM [githubarchive:github.timeline] \
                        where repository_organization is not NULL \
                        and repository_language is not NULL \
                        and created_at <= \'%s\' \
                        and created_at >= \'%s\' \
                        group by repository_language order by ct desc limit 50" % (end_date, start_date)
        
        res = self.run_query(query_string)
        rows = res['rows']
        for r in rows:
            org = r[u'f'][0][u'v']
        logging.info("*******   result *******: \n")
        logging.info(str(res))
        logging.info(query_string)

    def get(self):
        #self.prepare_data()
        #self.response.write('<a href="http://runyunz-final.appspot.com/lang=Java">Sample</a>')
        self.response.write('<a href="http://final-project-yjian.appspot.com/lang?lang=Java,PHP,Python">Sample</a>')

class TopCoderHandler(webapp2.RequestHandler):
    def get(self):
        data = []
        params = self.request.get('org')
        start_date = "2014-01-01"
        end_date = "2014-05-09"
        query_str = "SELECT actor_attributes_name,actor, count(*) as ct \
                     FROM [githubarchive:github.timeline] \
                     where actor_attributes_name is not null \
                     and created_at >= \'%s\' \
                     and created_at <= \'%s\' \
                     and repository_organization='GNOME' \
                     group by actor,actor_attributes_name order by ct desc limit 10" % (start_date, end_date)
        res = self.run_query(query_str)
        if res is not None:
            rows = res['rows']
            for r in rows:
                name = r[u'f'][0][u'v']
                uid = r[u'f'][1][u'v']
                data.append([name.encode('utf-8'), uid.encode('utf-8')])
            
        logging.info("****** "+str(data))
        context = {"data":data}
        path = os.path.join(os.path.dirname(__file__), 'templates/topcoder.html')
    	self.response.out.write(template.render(path, context))	
    
    def run_query(self, query_string, timeout=100000):
		if (os.getenv('SERVER_SOFTWARE') and
			os.getenv('SERVER_SOFTWARE').startswith('Google App Engine/')):
			# set up the query 
			query = {'query':query_string, 'timeoutMs':timeout}
			# service is the oauth2 setup that we created above
			jobCollection = service.jobs()
			# project number is the project number you should have 
			# defined in your app
			return jobCollection.query(projectId=_PROJECT_NUMBER,body=query).execute()
		else:
			return None

class OrgHandler(webapp2.RequestHandler):
    def get(self):
    	data = []
        start_date = "2014-01-01"
        end_date = "2014-05-09"
    	#res.append(self.compute(user1))
    	#res.append(self.compute(user2))
        #logging.info("************ language: "+lang)
        params = self.request.get('lang')
        logging.info("************ params: "+str(params))
        lang = params
        langs = lang.split(',')
        logging.info("language: ******* "+str(langs))
    	#users = [user1, user2]
        for l in langs:
            query_str = "SELECT repository_organization, count(*) as ct \
                         FROM [githubarchive:github.timeline] \
                         where repository_language=\'%s\' and \
                         created_at >= \'%s\' and \
                         created_at <= \'%s\' and \
                         repository_organization is not NULL \
                         group by repository_organization order by ct desc limit 10 "%(l, start_date, end_date)
            res = self.run_query(query_str)
            logging.info("*******  res ******"+str(res))
            if res is None:
                continue
            elif res.get('rows'):
                rows = res['rows']
            
                for r in rows:
                    org = r[u'f'][0][u'v']
                    ct = r[u'f'][1][u'v']
                    data.append([l.encode('utf-8'), org.encode('utf-8'), int(ct), 0])
            
        logging.info("****** "+str(data))
        '''
        data = [
		['Lite','AL',16,0],
		['Small','AL',1278,4],
		['Medium','AL',27,0],
		['Plus','AL',58,0],
		['Grand','AL',1551,15]]
        '''
    	context = {"res": data}
        path = os.path.join(os.path.dirname(__file__), 'templates/bipartie.html')
    	self.response.out.write(template.render(path, context))	

    def compute(self, user):
		logging.info("running birth related queries")
		# query_string = "SELECT count(*) FROM [{0}] WHERE actor='{1}' AND type='FollowEvent';".format(_DATABASE_NAME, user1)
		query_string = "SELECT type, COUNT(*) as count FROM [{0}] \
						WHERE actor='{1}' AND type IN ('FollowEvent', 'WatchEvent', 'PushEvent', \
						'PullRequestEvent', 'IssueCommentEvent', 'PullRequestReviewCommentEvent') \
						GROUP BY type;".format(_DATABASE_NAME, user)
		res = self.run_query(query_string)
		res_parse = self.parse(res)

		query_string = "SELECT count(*) as count FROM [{0}] \
						WHERE payload_target_login='{1}' AND type='FollowEvent';".format(_DATABASE_NAME, user)
		res2 = self.run_query(query_string)
		query_string = "SELECT count(*) as count FROM [{0}] \
						WHERE repository_owner='{1}' AND type='WatchEvent';".format(_DATABASE_NAME, user)
		res3 = self.run_query(query_string)
		res_parse.append(self.parse2(res2, res3))
		return res_parse

		# context = {"res": res_parse,"res2": res2, "res3": res3}
		# self.render_response('radar.html', context)

    def run_query(self, query_string, timeout=10000):
		if (os.getenv('SERVER_SOFTWARE') and
			os.getenv('SERVER_SOFTWARE').startswith('Google App Engine/')):
			# set up the query 
			query = {'query':query_string, 'timeoutMs':timeout}
			logging.info(query)
			# service is the oauth2 setup that we created above
			jobCollection = service.jobs()
			# project number is the project number you should have 
			# defined in your app
			return jobCollection.query(projectId=_PROJECT_NUMBER,body=query).execute()
		else:
			return None

    def parse(self, res):
    	# process
    	rows = res[u'rows']
    	records = {}
        res_parse = []
        for row in rows:
            request = row[u'f'][0][u'v']
            count = row[u'f'][1][u'v']
            if request == None: 
            	request = u'None'
            # record = {'request':unicode.encode(request), 'count':int(count)}
            records[request] = int(count)

        # compute Exploration
        val = 0
        val += records.get('FollowEvent', 0)
        val += records.get('WatchEvent', 0)

        if val > 0:
        	val = round(math.log(val), 2)
        	if val == 0: val = 0.3
        if val > 5: val = 5.0

        axis = {'axis': 'Exploration', 'value': val}
        res_parse.append(axis)

        # compute Contribution
        val = 0
        val = records.get('PushEvent', 0)

        
        if val > 0:
        	val = round(math.log(val), 2)
        	if val == 0: val = 0.3
        if val > 5: val = 5.0

        axis = {'axis': 'Contribution', 'value': val}
        res_parse.append(axis)

        # compute Collaboration
        val = 0
        val = records.get('PullRequestEvent', 0)

        if val > 0:
        	val = round(math.log(val), 2)
        	if val == 0: val = 0.3
        if val > 5: val = 5.0

        axis = {'axis': 'Collaboration', 'value': val}
        res_parse.append(axis)

        # compute Communication
        val = 0
        val += records.get('IssueCommentEvent', 0)
        val += records.get('PullRequestReviewCommentEvent', 0)

        if val > 0:
        	val = round(math.log(val), 2)
        	if val == 0: val = 0.3
        if val > 5: val = 5.0

        axis = {'axis': 'Communication', 'value': val}
        res_parse.append(axis)        

        return res_parse

    def parse2(self, res2, res3):
    	records = {}
        res_parse = []
        val = 0

    	rows = res2[u'rows']
    	for row in rows:
    		val += int(row[u'f'][0][u'v'])
    	rows = res3[u'rows']
    	for row in rows:
    		val += int(row[u'f'][0][u'v'])

        if val > 0:
        	val = round(math.log(val), 2)
        	if val == 0: val = 0.3
        if val > 5: val = 5.0

        axis = {'axis': 'Reputation', 'value': val}
    	return axis

app = webapp2.WSGIApplication([
    (r'/', MainHandler),
    (r'/lang', OrgHandler),
    (r'/topcoder', TopCoderHandler)
], debug=True)
