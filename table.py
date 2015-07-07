#don't table
#coding=utf-8
#! /usr/bin/env python
import sys,os,re
def first(line):
	for c in line:
		if c!='\t' and c!=' ' and c!='\n':
			return c
	return None
selfname = __file__
cwpath = os.getcwd()
print(cwpath)
for filename in os.listdir(cwpath):
	if filename[-3:] == ".py":
		with open(cwpath+'/'+filename,"r",encoding = 'UTF8') as fd:
			lines = fd.readlines()
		if lines[0] == "#don't table\n":
			continue
		print(filename)
		last = ""
		for line in lines:
			if 'def ' in line or 'class ' in line:
				if first(last) == '#':
					print("\t%s"%last[:-1])
				print("\t%s"%line[:-1])
			last = line
"""
for parent,dirname,filenames in os.walk(cwpath):
	print(parent)
	print(dirname)
	print(filenames)
print(selfname)
"""