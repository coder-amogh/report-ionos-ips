#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import shutil
import sys

import subprocess

from email.message import EmailMessage

from email.mime.base import MIMEBase
from email import encoders

import smtplib as smtp

import time
import datetime

from dotenv import load_dotenv

load_dotenv()

class Mailer:
	def __init__(self, hostname = os.environ.get("EMAIL_HOSTNAME"), port = int(os.environ.get("EMAIL_PORT")), username = os.environ.get("EMAIL_USERNAME"), password = os.environ.get("EMAIL_PASSWORD"), from_name = os.environ.get("EMAIL_FROM_NAME")):
		'''
			Instantiates the object
		'''
		self.hostname = hostname
		self.port = port
		self.username = username
		self.password = password
		self.from_name = from_name

	def create_new(self, to = None, subject = '', message = '', cc = None, bcc = None, is_html = True):
		'''
			Creates new mail object
		'''

		html_message = message
		
		self.msg = EmailMessage()

		if to is None:
			return False

		self.msg["From"] = f'{self.from_name} <{self.username}>'
		self.msg["To"] = to
		self.msg["Subject"] = subject

		if cc is not None:
			self.msg["Cc"] = cc

		if bcc is not None:
			self.msg["Bcc"] = bcc

		if not is_html:
			html_message = f'''
				<!DOCTYPE html>
				<html>
				<head>
					<meta charset="utf-8">
				</head>
				<body>
					<p>{message}</p>
				</body>
				</html>
			'''

		self.msg.set_content("Please enable HTML to view this message!")
		self.msg.add_alternative(html_message, subtype = "html")

		return True

	def attach_file(self, filename, file_path):
		'''
			Attaches file to an exiting email
		'''

		with open(file_path, "rb") as attachment:		  
			# instance of MIMEBase and named as p
			p = MIMEBase("application", "octet-stream")
			  
			# To change the payload into encoded form
			p.set_payload((attachment).read())
			  
			# encode into base64
			encoders.encode_base64(p)
			   
			p.add_header("Content-Disposition", f"attachment; filename={filename.split('.')[0]}")
			  
			# attach the instance 'p' to instance 'msg'
			self.msg.attach(p)

		return True

	def login(self):
		'''
			Logs into the mail provider
		'''

		self.conn = smtp.SMTP(self.hostname, self.port)
		self.conn.ehlo()
		self.conn.starttls()
		self.conn.ehlo()
		self.conn.login(self.username, self.password)

		return True

	def logout(self):
		try:
			self.conn.logout()
		except:
			pass

	def send(self):
		'''
			Sends the email
		'''

		self.conn.send_message(self.msg)

		return True

	def __del__(self):
		pass

nohup_configs = {
	"work": False, # bool: work or not
	"column": 2, # indexes from 1
	"grep_text": "404 not found", # text to search through
	"split_colon": True, # if colon exists in FastAPI logs
	"replace_chars_list": ["(", ")", "'", '"'],
	"filepaths": ["nohup.*"], # file paths in a list, you can also use regex
	"line_split_char": "\n"
}

auth_configs = {
	"work": True,
	"column": "NF-3",
	"grep_text": "Failed password",
	"filepaths": ["/var/log/auth.log", "/var/log/auth.log.1"],
	"line_split_char": "\n",
	"work_zmore": True,
	"zmore_grep_text": "Failed password",
	"zmore_files": ["/var/log/auth.log.*.gz"]
}

'''
82.223.0.0/16
70.35.0.0/16
212.227.0.0/16
217.160.0.0/16
74.208.0.0/16
'''

REPORT_IPS_STARTS_WITH_LIST = ("82.223", "70.35", "212.227", "217.160", "74.208",)

if nohup_configs["work"]:
	NEW_MKDIR_NAME = f'logs-{int(time.time())}'

	os.mkdir(NEW_MKDIR_NAME)

	ZIP_FILE_NAME = f'{NEW_MKDIR_NAME}.zip'

	command = f'cat {" ".join(nohup_configs["filepaths"])} | grep -i "{nohup_configs["grep_text"]}" | awk \'{{ print ${nohup_configs["column"]} }}\' | uniq '

	# https://stackoverflow.com/a/4760517
	output = subprocess.check_output(command, shell = True)

	r = output.decode()

	report_ips = set()
	other_ips = set()

	for line in r.strip().split(nohup_configs["line_split_char"]):
		ip = line.strip()

		if nohup_configs["split_colon"]:
			ip = "".join(ip.split(":")[:-1])

		if nohup_configs["replace_chars_list"] != []:
			for char in nohup_configs["replace_chars_list"]:
				ip = ip.replace(char, "")

		for report_ip in REPORT_IPS_STARTS_WITH_LIST:
			if ip.startswith(report_ip):
				report_ips.add(ip)
			else:
				other_ips.add(ip)

	if len(report_ips) > 0:
		# Copy all the log files in the filepaths to a new directory
		for file in nohup_configs["filepaths"]:
			os.system(f'cp {file} {NEW_MKDIR_NAME}/')

		os.system(f"zip -r {ZIP_FILE_NAME} {NEW_MKDIR_NAME}")

		html_message = f'''
			<!DOCTYPE html>
			<html>
			<head>
				<meta charset="utf-8">
			</head>
			<body>
				<p>
					Attached is the ZIP file of network access logs (apache or nginx or frameworks like FastAPI) through which this script has identified few of the IPs which belong to IONOS and are trying to hack my server's password thereby gaining access to my server and doing some damage which might affect me. 
				</p>

				<p>
					This script is based on: https://github.com/coder-amogh/report-ionos-ips
				</p>

				<p>Hope you will take these weekly automated reports seriously and take required action on it.</p>

				<hr>

				<p>IPs found:</p>

				<div style="border: 1px solid black; padding: 10px;">
					{'<br>'.join(report_ips)}
				</div>

				<hr>

				<p>Please drop a reply to this email, and if possible do mention what actions are taken against this.</p>
			</body>
			</html>
		'''

		print("Mailing...")

		mailer = Mailer()
		mailer.create_new(to = "coderamogh@gmail.com", subject = f'Spam network request logs reports for the week {datetime.datetime.now().strftime("%U")}', message = html_message, is_html = True)
		mailer.attach_file(ZIP_FILE_NAME, os.path.join(os.getcwd(), ZIP_FILE_NAME))
		mailer.login()
		mailer.send()
		mailer.logout()

		print("Sent mail!")
	else:
		print("No IPs by IONOS found...")

	if len(other_ips) > 0:
		other_ips_file_name = f'nohup-{datetime.datetime.now().strftime("%s")}.txt'

		print(f"Other {len(other_ips)} IPs are found though... Check the {other_ips_file_name} file.")

		with open(other_ips_file_name, "w") as f:
			for ip in other_ips:
				output = subprocess.check_output(f"geoiplookup {ip}", shell = True)
				output = output.decode()

				country = output.split("GeoIP Country Edition:")[1].strip()

				f.write(f'{ip}\t\t==> {country}\n')

		print("Done!")

	try:
		shutil.rmtree(NEW_MKDIR_NAME, ignore_errors = True)
		os.remove(ZIP_FILE_NAME)
	except:
		pass

if auth_configs["work"]:
	NEW_MKDIR_NAME = f'logs-{int(time.time())}'

	os.mkdir(NEW_MKDIR_NAME)

	ZIP_FILE_NAME = f'{NEW_MKDIR_NAME}.zip'

	command = f'cat {" ".join(auth_configs["filepaths"])} | grep -i "{auth_configs["grep_text"]}" | awk \'{{ print $({auth_configs["column"]}) }}\''

	if auth_configs["work_zmore"]:
		zmore_command = f'zmore {" ".join(auth_configs["filepaths"])} | grep -i "{auth_configs["zmore_grep_text"]}" | awk \'{{ print $({auth_configs["column"]}) }}\''
		# command = f'{{ {command} & {zmore_command}; }} | uniq | wc -l'
		command = f'(({command}) && ({zmore_command})) | uniq'

	# https://stackoverflow.com/a/4760517
	output = subprocess.check_output(command, shell = True)

	r = output.decode()

	report_ips = set()

	other_ips = set()

	for line in r.strip().split(auth_configs["line_split_char"]):
		ip = line.strip()

		for report_ip in REPORT_IPS_STARTS_WITH_LIST:
			if ip.startswith(report_ip):
				report_ips.add(ip)
			else:
				other_ips.add(ip)

	if len(report_ips) > 0:
		# Copy all the log files in the filepaths to a new directory
		for file in auth_configs["filepaths"]:
			os.system(f'cp {file} {NEW_MKDIR_NAME}/')
			os.system(f'truncate -s 0 {file}')

		os.system(f"zip -r {ZIP_FILE_NAME} {NEW_MKDIR_NAME}")

		html_message = f'''
			<!DOCTYPE html>
			<html>
			<head>
				<meta charset="utf-8">
			</head>
			<body>
				<p>
					Attached is the ZIP file of SSH failed password access logs through which this script has identified few of the IPs which belong to IONOS and are trying to hack my server's password thereby gaining access to my server and doing some damage which might affect me. 
				</p>

				<p>
					This script is based on: https://github.com/coder-amogh/report-ionos-ips
				</p>

				<p>Hope you will take these weekly automated reports seriously and take required action on it.</p>

				<hr>

				<p>IPs found:</p>

				<div style="border: 1px solid black; padding: 10px;">
					{'<br>'.join(report_ips)}
				</div>

				<hr>

				<p>Please drop a reply to this email, and if possible do mention what actions are taken against this.</p>
			</body>
			</html>
		'''

		print("Mailing...")

		mailer = Mailer()
		mailer.create_new(to = os.environ.get("EMAIL_TO"), cc = os.environ.get("EMAIL_CC"), subject = f'Spam SSH auth request logs reports for the week {datetime.datetime.now().strftime("%U")}', message = html_message, is_html = True)
		mailer.attach_file(ZIP_FILE_NAME, os.path.join(os.getcwd(), ZIP_FILE_NAME))
		mailer.login()
		mailer.send()
		mailer.logout()

		print("Sent mail!")

	else:
		print("No IPs by IONOS found...")

	if len(other_ips) > 0:
		other_ips_file_name = f'auth-{datetime.datetime.now().strftime("%s")}.txt'

		print(f"Other {len(other_ips)} IPs are found though... Check the {other_ips_file_name} file.")

		with open(other_ips_file_name, "w") as f:
			for ip in other_ips:
				output = subprocess.check_output(f"geoiplookup {ip}", shell = True)
				output = output.decode()

				country = output.split("GeoIP Country Edition:")[1].strip()

				f.write(f'{ip}\t\t==> {country}\n')

		print("Done!")
	try:
		shutil.rmtree(NEW_MKDIR_NAME, ignore_errors = True)

		os.remove(ZIP_FILE_NAME)
	except:
		pass

