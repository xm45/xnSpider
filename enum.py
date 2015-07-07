#coding=utf-8
#! /usr/bin/env python

class action(object):
	#动作信息
	#开始子事务，预处理完成，子事务结束，本事务结束，出错
	begin = 'BEGIN'
	work = 'WORK'
	end = 'END'
	exit = 'EXIT.'
	error = 'ERROR.'
	attributes = [begin,end,exit,error,work]
	def __iter__(self):
		return self.attributes.__iter__()
	def __next__(self):
		return self.attributes.__next__()
	def __str__(self):
		return str(self.attributes)
class func(object):
	album = "ALBUM"
	user = "USER"
	friend = "FRIEND"
	share = "SHARE"#unuse in log
	photo = "PHOTO"#unuse in log
	log = "LOG"
	attributes = [album,user,friend,log]
	def __iter__(self):
		return self.attributes.__iter__()
	def __next__(self):
		return self.attributes.__next__()
	def __str__(self):
		return str(self.attributes)
class suffix(object):
	temp ="_temp"
	modify ="[modify]"
	attributes = [temp,modify]
	def __iter__(self):
		return self.attributes.__iter__()
	def __next__(self):
		return self.attributes.__next__()
	def __str__(self):
		return str(self.attributes)
need = {
		func.album:{
			'input':['selfid','Uid','Aid'],
			'ready':['dirname']},
		func.user:{
			'input':['selfid','Uid'],
			'ready':['dirname','Uname']},
		func.friend:{
			'input':['selfid'],
			'ready':['dirname']}}
class inf(action, func):
	end = {
			'id':'0',
			'action':action.exit,
			'func':func.log,
			'data':{}}
	error = {
			'id':'0',
			'action':action.error,
			'func':func.log,
			'data':{}}
	attributes = [end,error]
	def __iter__(self):
		return self.attributes.__iter__()
	def __next__(self):
		return self.attributes.__next__()
	def __str__(self):
		return str(self.attributes)
"""
class enum(object):
	action = action()
	func = func()
	suffix = suffix()
	inf = inf()
	attributes = ['id','action','func','data']
	def __iter__(self):
		return self.attributes.__iter__()
	def __next__(self):
		return self.attributes.__next__()
"""
action = action()
func = func()
suffix = suffix()
inf = inf()
attributes = ['id','action','func','data']
def __str__():
	return str(attributes)