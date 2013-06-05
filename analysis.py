#!/usr/bin/env python
# encoding: utf-8

# This is a library to manage analysis objects.
# Note that it doesn't care about performance and will happily lock up any thread its methods are called in.
# So spawn some worker threads to do this stuff.

import os
import shutil
import datetime as dt
import feeder
import subprocess
import copy
import json
import studies
import reports
import storage

store = storage.Filestore('data')

class Analysis:
	# Metadata attributes
	name = ''
	status = ''
	sourceFeeder = ''
	climate = ''
	created = ''
	simStartDate = ''
	simLength = ''
	simLengthUnits = 0
	# Data attributes
	reports = []
	studyNames = []
	# Internal attributes
	studies = []

	def __init__(self, name, jsonMdDict, jsonDict):
		self.reports = jsonDict['reports']
		self.studyNames = jsonDict['studyNames']
		self.status = jsonMdDict['status']
		self.sourceFeeder = jsonMdDict['sourceFeeder']
		self.climate = jsonMdDict['climate']
		self.created = jsonMdDict['created']
		self.simStartDate = jsonMdDict['simStartDate']
		self.simLength = jsonMdDict['simLength']
		self.simLengthUnits = jsonMdDict['simLengthUnits']
		self.name = name
		self.studies = [studies.gridlabd.GridlabStudy(studyName, store.getMetadata('Study', self.name + '---' + studyName), store.get('Study', self.name + '---' + studyName)) for studyName in self.studyNames]

	def generateReportHtml(self):
		# Iterate over reports and collect what we need: 
		reportList = []
		for report in self.reports:
			# call the relevant reporting function by name.
			reportModule = getattr(reports, report['reportType'])
			reportList.append(reportModule.outputHtml(self, report))
		return reportList

	def run(self):
		# NOTE! We are running studies serially. We use lower levels of RAM/CPU, potentially saving time if swapping were to occur.
		# Update status to running.
		md = getMetadata(analysisName)
		md['status'] = 'running'
		putMetadata(analysisName, md)
		startTime = dt.datetime.now()
		for studyName in self.studies:
			# If we've been terminated, don't run any more studies.
			if md['status'] == 'terminated': return False
			with open('analyses/' + analysisName + '/studies/' + studyName + '/metadata.json') as studyMd:
				studyType = json.load(studyMd)['studyType']
			studyModule = getattr(studies, studyType)
			try:
				studyModule.run(analysisName, studyName)
			except Exception, e:
				md = getMetadata(analysisName)
				print "Got an error, but everything should be alright. Error:", e
				md['status'] = 'ERROR'
				putMetadata(analysisName, md)
				with open('analyses/' + analysisName + '/studies/' + studyName + '/cleanOutput.json', 'w') as cleanOutput:
					cleanOutput.write('{}')
				# return
		# Update status to postRun and include running time IF WE DIDN'T TERMINATE.
		md = getMetadata(analysisName)
		if md['status'] != 'terminated' and md['status'] != 'ERROR':
			endTime = dt.datetime.now()
			md['runTime'] = str(dt.timedelta(seconds=int((endTime - startTime).total_seconds())))
			md['status'] = 'postRun'
			putMetadata(analysisName, md)

	def terminate(self):
		# Get all the pids.
		pids = []
		studiesDir = 'analyses/' + analysisName + '/studies/'
		for studyName in os.listdir(studiesDir):
			studyFiles = os.listdir(studiesDir + studyName)
			if 'PID.txt' in studyFiles:
				with open(studiesDir + studyName + '/PID.txt','r') as pidFile: pids.append(int(pidFile.read()))
				os.remove(studiesDir + studyName + '/PID.txt')
		try:
			for pid in pids: os.kill(pid, 15)
		except:
			print 'We could not kill some PIDs. They may have already completed normally.'
		# Update that analysis status.
		md = getMetadata(analysisName)
		md['status'] = 'terminated'
		putMetadata(analysisName, md)
		return

	def toJson(self):
		pass

	def mdToJson(self):
		pass

if __name__ == '__main__':
	pass
