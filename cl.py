#!/usr/bin/env python
# -*- coding: utf-8 -*-

from core.clcore import *
from core.constants import CL_ROOT
from core.config import Config

import os
import sys
import socket
import time
import urllib
import urllib2
import signal
import datetime
import threading
import Queue
import time


import smtplib
import mimetypes
from types import *
from email import Encoders
from email.MIMEBase import MIMEBase
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText


halt = False

try:
	import argparse
except ImportError:
	print 'Missing needed module: easy_install argparse'
	halt = True
	
try:
	import yaml
except ImportError:
	print 'Missing needed module: easy_install yaml'
	halt = True
	
try:
	import sqlite3
except ImportError:
	print 'Missing needed module: easy_install sqlite3'
	halt = True
	
try:
	import xlwt
except ImportError:
	print 'Missing needed module: easy_install xlwt'
	halt = True
	
try:
	from BeautifulSoup import BeautifulSoup
except ImportError:
	print 'Missing needed module: easy_install BeautifulSoup'
	halt = True
	
if halt == True:
	sys.exit()
	
sigint = False
results = []

def logo():
	print " .---. .-.    "
	print "/  ___}| |    "
	print "\     }| `--. "
	print " `---' `----' "
	print 'Craigslist Scanner...'
	print 'Author: Jaime Filson aka WiK'
	print 'Email: wick2o@gmail.com'
	print ""
	
def sendEmailReport(isResults):
	e_body  = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><html xmlns="http://www.w3.org/1999/xhtml">'
	e_body += '<html>'
	e_body += '<body style="font-size:12px;font-family:Verdana">'
	e_body += '<p>'
	
	if isResults == True:
		e_body += "The following attachment is the results from today's CL scan<br/><br/>"
	else:
		e_body += "There was no new results from today's CL scan<br/><br/>"
		
	e_body += '</p></body></html>'

	e_msg = MIMEMultipart()
	e_msg['From'] = cfg.email.efrom
	e_msg['To'] = cfg.email.recipients
	e_msg['Subject'] = 'Results of todays CL scan'
	e_msg.attach(MIMEText(e_body, 'html'))
	
	if isResults == True:
		if args.outfile == "":
			f_name =  os.path.join(CL_ROOT, 'data', 'output-%s.xls' % (datetime.datetime.now().strftime('%Y-%m-%d')))
		else:
			f_name = os.path.join(CL_ROOT, 'data', '%s-%s.xls' % (args.outfile, datetime.datetime.now().strftime('%Y-%m-%d')))
		#f_name =  os.path.join(CL_ROOT, 'data', 'output-%s.xls' % (datetime.datetime.now().strftime('%Y-%m-%d')))
		e_file = MIMEBase('application', 'octet-stream')
		e_file.set_payload(open(f_name, 'rb').read())
		Encoders.encode_base64(e_file)
		e_file.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f_name))
		e_msg.attach(e_file)

	server = smtplib.SMTP(host=cfg.email.server, port=cfg.email.port)
	server.starttls()
	server.login(cfg.email.username, cfg.email.password)
	for em in cfg.email.recipients.split(','):
		server.sendmail(cfg.email.e_from, em.strip(), e_msg.as_string())
	server.quit()

def generate_task_data():
	my_task_data = []
	
	for search_term in searchterm_dict['search_terms']:
		for state_itm in usa_dict:
			for city_itm in usa_dict[state_itm]:
				if city_itm['city']['enable'] == True:
					try:
						for sub_itm in c_itm['city']['subs']:
							tmp_data = {}
							tmp_data['name'] = city_itm['city']['name']
							tmp_data['state'] = state_itm
							tmp_data['id'] = city_itm['city']['id']
							tmp_data['search_term'] = search_term
							tmp_data['sub'] = sub_itm
							my_task_data.append(tmp_data)
					except:
						tmp_data = {}
						tmp_data['name'] = city_itm['city']['name']
						tmp_data['state'] = state_itm
						tmp_data['id'] = city_itm['city']['id']
						tmp_data['search_term'] = search_term
						tmp_data['sub'] = ''
						my_task_data.append(tmp_data)
	return my_task_data

def progressbar(progress, total):
	progress_percentage = int(100 / (float(total) / float(progress)))
	sys.stdout.write("%s%% complete\r" % (progress_percentage))

def run_process(itm):
	try:
		if itm['sub'] == '':
			url = 'http://%s.craigslist.org/search/sss?query=%s' % (itm['name'], itm['search_term'].replace(' ', '+'))
		else:
			url = 'http://%s.craigslist.org/search/sss/%s?query=%s' % (itm['name'], itm['sub'], itm['search_term'].replace(' ', '+'))
			
		req = urllib2.Request(url)
		req.add_header('User-Agent', get_useragent())
		req.add_header('Referer', 'http://%s.craigslist.org' % (itm['name']))
		
		page = urllib2.urlopen(req)
		page_content = page.read()
		page.close()
		
		if page_content != None:
			if 'Nothing found for that search' in page_content:
				pass
			elif 'Zero LOCAL results found' in page_content:
				pass
			else:
				soup = BeautifulSoup(page_content)
				res = soup.findAll('p', {'class':'row'})
				for res_itm in res:
					tmp_res = {}
					try:
						tmp_res['pl'] = res_itm.find('span', {'class':'pl'}).find('a').string.strip()
					except:
						tmp_res['pl'] = 'None'
					try:
						tmp_res['date'] = res_itm.find('span', {'class':'date'}).string
					except:
						tmp_res['date'] = 'None'
					try:
						tmp_res['price'] = res_itm.find('span', {'class':'price'}).string
					except:
						tmp_res['price'] = 'None'
					try:
						tmp_res['gc'] = res_itm.find('a', {'class':'gc'}).string
					except:
						tmp_res['gc'] = 'None'
					try:
						tmp_res['pnr'] = res_itm.find('span', {'class':'pnr'}).find('small').string.strip()
					except:
						tmp_res['pnr'] = 'None'
					try:
						t_href = res_itm.find('span', {'class':'pl'}).find('a')['href']
						if t_href.startswith('/'):
							tmp_res['href'] = 'http://%s.craigslist.org%s' % (itm['name'], t_href)
						else:
							tmp_res['href'] = t_href
					except:
						tmp_res['href'] = 'None'
					try:
						tmp_res['pid'] = res_itm['data-pid']
					except:
						tmp_res['pid'] = 'None'
					
					tmp_res['name'] = itm['name']
					tmp_res['state'] = itm['state']
					tmp_res['search_term'] = itm['search_term']
					tmp_res['sub'] = itm['sub']
					
					is_tmp_res_new = True
					for fin_res_itm in results:
						if tmp_res['pid'] == fin_res_itm['pid']:
							is_tmp_res_new = False
							break
							
					if is_tmp_res_new == True:
						results.append(tmp_res)
						if args.debug:
							print '%s [DEBUG] Added %s %s' % (datetime.datetime.now(), tmp_res['pid'],tmp_res['href'])
					else:
						if args.debug:
							print '%s [DEBUG] Skipping %s %s' % (datetime.datetime.now(), tmp_res['pid'], tmp_res['href'])
	except:
		print '%s [ERROR] There has been an error tring to access %s' % (datetime.datetime.now(), url)
		
	if args.wait > 0:
			time.sleep(args.wait)

def process_handler(task_data):
	progress = 0
	
	if args.threads > 1:
		q = Queue.Queue()
		threads = []
		for itm in task_data:
			q.put(itm)
		progress_lock = threading.Lock()
		
		while not q.empty():
			if args.threads >= threading.activeCount():
				q_itm = q.get()
				try:
					t = threading.Thread(target=run_process, args=(q_itm,))
					t.deamon = True
					threads.append(t)
					t.start()
				finally:
					progress = len(task_data) - q.qsize()
					progress_lock.acquire()
					try:
						progressbar(progress, len(task_data))
					finally:
						progress_lock.release()
					q.task_done()
					
		while threading.activeCount() > 1:
			time.sleep(0.1)
			
		for thread in threads:
			thread.join()
			
		q.join()
		
	else:
		for itm in task_data:
			run_process(itm)
			progress += 1
			progressbar(progress, len(task_data))   
	return
		

def generate_output_file():
	wb = xlwt.Workbook(encoding='utf=8')
	sht_summary = wb.add_sheet('Summary')
	sht_data = wb.add_sheet('Data')
	
	percent_style = xlwt.XFStyle()
	percent_style.num_format_str = '0.00%'
	
	h_font = xlwt.Font()
	h_font.name = 'Verdana'
	h_font.bold = True
	h_font.underline = xlwt.Font.UNDERLINE_DOUBLE
	h_font.colour_index = 4
	h_style = xlwt.XFStyle()
	h_style.font = h_font
	
	sht_summary.write(1, 0, 'Keyword Breakdown:')
	sht_summary.col(0).width = 20 * 256
	sht_summary.write(3, 0, 'Total Items:')
	sht_summary.write(5, 0, 'Keyword')
	sht_summary.write(5, 1, 'Percentage')
	sht_summary.col(1).width = 20 * 256
	
	if args.debug:
		print '%s [DEBUG] Attempting to parse sections_to_ignore.yml.' % (datetime.datetime.now())
	
	f = open(os.path.join(CL_ROOT, 'data', 'sections_to_ignore.yml'), 'r')
	sections_to_ignore = yaml.safe_load(f)
	f.close
	
	sht_data.col(0).width = 11 * 256
	sht_data.col(1).width = 8 * 256	
	sht_data.col(2).width = 8 * 256
	sht_data.col(3).width = 60 * 256
	sht_data.col(4).width = 40 * 256
	sht_data.col(5).width = 35 * 256
	sht_data.col(6).width = 8 * 256
	sht_data.col(7).width = 30 * 256
	sht_data.col(8).width = 30 * 256
	sht_data.col(9).width = 30 * 256
	
	data_ctr = 0
	for itm in results:
		if not itm['gc'].replace('&amp;','&') in sections_to_ignore['sections_to_ignore']:
			sht_data.write(data_ctr, 0, itm['pid']) # Craigslist ID Number
			sht_data.write(data_ctr, 1, itm['date'])
			sht_data.write(data_ctr, 2, itm['price']) # Cost of item if known
			sht_data.write(data_ctr, 3, itm['pl']) # Subject
			sht_data.write(data_ctr, 4, itm['pnr']) # Unknown?
			sht_data.write(data_ctr, 5, itm['name']) # City
			sht_data.write(data_ctr, 6, xlwt.Formula('HYPERLINK("%s", "GOTO")' % (itm['href'])), h_style)
			sht_data.write(data_ctr, 7, itm['state']) # state
			sht_data.write(data_ctr, 8, itm['gc']) # section
			sht_data.write(data_ctr, 9, itm['search_term']) #Search term used
			data_ctr += 1
			
	if data_ctr == 0:
		return False

	if args.debug:
		print '%s [DEBUG] Attempting to parse search_terms.yml.' % (datetime.datetime.now())
		
	sht_summary.write(3, 1, data_ctr)
	
	term_ctr = 6
	for s_term in searchterm_dict['search_terms']:
		sht_summary.write(term_ctr, 0, s_term)
		sht_summary.write(term_ctr, 1, xlwt.Formula('COUNTIF(Data!J1:J%s,A%s)/B4' % (data_ctr, term_ctr + 1)), percent_style)
		term_ctr += 1
	
	if args.debug:
		print '%s [DEBUG] Saving output file' % (datetime.datetime.now())
	
	if args.outfile == "":
		f_name =  os.path.join(CL_ROOT, 'data', 'output-%s.xls' % (datetime.datetime.now().strftime('%Y-%m-%d')))
	else:
		f_name = os.path.join(CL_ROOT, 'data', '%s-%s.xls' % (args.outfile, datetime.datetime.now().strftime('%Y-%m-%d')))
	
	if os.path.exists(os.path.join(CL_ROOT, f_name)):
		os.remove(os.path.join(CL_ROOT, f_name))
		
	wb.save(os.path.join(CL_ROOT, f_name))
	
	return True
	
def db_check(db_name):
	if os.path.exists(db_name):
		if args.debug:
			print '%s [DEBUG] Skipping database generation, %s already exists.' % (datetime.datetime.now(), db_name)
	else:
		if args.debug:
			print '%s [DEBUG] Generating database %s.' % (datetime.datetime.now(), db_name)
			try:
				db = sqlite3.connect(db_name)
				db.execute('CREATE TABLE ads (id INTEGER PRIMARY KEY,date varchar(50),url varchar(255),subject varchar(255),cost varchar(25),location varchar(255),section varchar(100),s_term varchar(100),hash varchar(255),sub varchar(60), found_on_first varchar(100),found_on_last varchar(100))')
				db.commit()
			except e:
				print '%s [ERROR] %s' % (datetime.datetime.now(), e)
			finally:
				if db:
					db.close()
					del db
	
def setup():
	parser = argparse.ArgumentParser()
	parser.add_argument('-t', '--threads', action='store', dest='threads', default=0, type=int, help='Enable Threading. Specifiy max # of threads')
	parser.add_argument('-w', '--wait', action='store', dest='wait', default=0, type=int, help='Wait time between tasks')
	parser.add_argument('-s', '--sterms', action='store', dest='sterms', default='', help='yaml file of search terms')
	parser.add_argument('-c', '--config', action='store', dest='config', default='', help='yaml file of usa config')
	parser.add_argument('-o', '--out', action='store', dest='outfile', default='', help='output file base name, no ext')
	
	verbose_group = parser.add_mutually_exclusive_group()
	verbose_group.add_argument('-d', '--debug', action='store_true', dest='debug', help='Show Debugging messages')
	verbose_group.add_argument('-dd', '--verydebug', action='store_true', dest='verydebug', help='Show Very Debugging messages')
	verbose_group.add_argument('-q', '--quite', action='store_true', dest='quite', help='Hide all messages')
	
	global cfg
	cfg = Config()
	
	global args
	args = parser.parse_args()
	
def main():
	setup()

	if not args.quite:
		logo()
	
	if args.debug:
		print '%s [DEBUG] Checking config files' % (datetime.datetime.now())
	
	if args.sterms == "":
		file_sterms = os.path.join(CL_ROOT, 'data', 'search_terms.yml')
	else:
		if os.path.isfile(args.sterms) and os.path.exists(args.sterms):
			file_sterms = args.sterms
		else:
			print '%s [ERROR] %s does not seem to exists' % (datetime.datetime.now(), args.sterms)
			sys.exit()
	try:
		f = open(file_sterms, 'r')
		global searchterm_dict
		searchterm_dict = yaml.safe_load(f)
		f.close()
	except:
		print '%s [ERROR] Unable to open %s' % (datetime.datetime.now(), file_sterms)
		sys.exit()
	
	if args.debug:
		print '%s [DEBUG] Succssfully loaded %s' % (datetime.datetime.now(), file_sterms)

	if args.config == "":
		file_config = os.path.join(CL_ROOT, 'data', 'usa.yml')
	else:
		if os.path.isfile(args.config) and os.path.exists(args.config):
			file_config = args.config
		else:
			print '%s [ERROR] %s does not seem to exists' % (datetime.datetime.now(), args.config)
			sys.exit()
	try:
		f = open(file_config, 'r')
		global usa_dict
		usa_dict = yaml.safe_load(f)
		f.close()
	except:
		print '%s [ERROR] Unable to open %s' % (datetime.datetime.now(), file_config)
		sys.exit()
		
	if args.debug:
		print '%s [DEBUG] Successfully loaded %s' % (datetime.datetime.now(), file_config)
		
	if args.debug:
		print '%s [DEBUG] Generating the task data.' % (datetime.datetime.now())
		
	task_data = generate_task_data()
	
	if args.debug:
		print '%s [DEBUG] Processing the task data.' % (datetime.datetime.now())
		
	process_handler(task_data)
	
	if not args.quite:
		print 'Generating output file. Please wait...'
		
	res = generate_output_file()

	if not args.quite:
		print 'Sending email...'
		
	sendEmailReport(res)
	
	if args.debug:
		print '%s [DEBUG] Exiting Software.' % (datetime.datetime.now())
	
	if not args.quite:
		print 'Completed, now existing'
	
	sys.exit()
	
if __name__ == "__main__":
	main()