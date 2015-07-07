#coding=utf-8
#! /usr/bin/env python
import sys,os,time
import pickle
import xnString
import enum
from functools import reduce
#事务流程：
#工作开始		向主log中写入action=BEGIN的数据
#分析预处理		向子log中写入子任务的action=BEGIN的数据
#分析完成		向主log中写入action=WORK的数据
#子任务完成		向子log中写入action=END的数据
#全部完成		向子log中写入action=EXIT的数据
#全部完成		向主log中写入action=END的数据
#本次清理		删除子log
#下次启动		清除主log条目
"""
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
class func(object):
	album = "ALBUM"
	user = "USER"
	friend = "FRIEND"
	log = "LOG"
	attributes = [album,user,friend,log]
	def __iter__(self):
		return self.attributes.__iter__()
	def __next__(self):
		return self.attributes.__next__()
class suffix(object):
	temp ="_temp"
	modify ="[modify]"
	attributes = [temp,modify]
	def __iter__(self):
		return self.attributes.__iter__()
	def __next__(self):
		return self.attributes.__next__()
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
#
class InvalidLogIdError(Exception):
	def __init__(self, LogId, filename):
		Exception.__init__(self)
		self.message = "try to use a INVALID LOG ID [%s] in [%s]"%(LogId,filename)
	def __str__(self):
		return str(self.message)
class InvalidWorkIdError(Exception):
	def __init__(self, WorkId, filename):
		Exception.__init__(self)
		self.message = "try to use a INVALID WORK ID [%s] in [%s]"%(WorkId,filename)
	def __str__(self):
		return str(self.message)
class UnfinishedFuncError(Exception):
	def __init__(self, filename, workid):
		Exception.__init__(self)
		self.message = "try to FINISH LOG [%s], but WORK ID %s WITHOUT `END`"%(filename,workid)
	def __str__(self):
		return str(self.message)
class WorkFormatError(Exception):
	def __init__(self, filename):
		Exception.__init__(self)
		self.message = "try to READ LOG [%s], but the DATA IS NOT UNIFIC."%(filename)
	def __str__(self):
		return str(self.message)
#
def isItem(text,funclist):
	obj = xnString.j2o(text, prerr = False)
	if type(obj) != dict:
		return None
	for attr in enum.attributes:
		if not attr in obj:
			return None
		else:
			if attr == 'action' and not obj[attr] in enum.action:
				print("transform to object error:\n\
						object:%s\n\
						attributes:%s\n\
						actionList:%s\n"%(obj,attr,enum.action))
				return None
			if attr == 'func' and not obj[attr] in funclist:
				print("transform to object error:\n\
						object:%s\n\
						attributes:%s\n\
						funcList:%s\n"%(obj,attr,funclist))
				return None
	return obj
class File:
	def __init__(self, name , funclist = enum.func.attributes, prflag = True):
		self.__name = name
		self.__mname = name + enum.suffix.modify
		self.__tname = name + enum.suffix.temp
		self.funclist = (lambda l,v:l if v in l else l+[v])(funclist,enum.func.log)
		self.flag_msg = prflag
		self.cache = []
		self.extid = []
		self.finished = []
		self.__id = 1
		self.__end = False
		self.getName = lambda: self.__name
		self.isEnd = lambda: self.__end
		self.isExist = lambda LogId: LogId in self.extid
		self.check()
	def __del__(self):
		pass
	#
	def __clean(self ,name = None):
		if not name:
			name = self.__name
		if os.path.exists(name + enum.suffix.modify):
			self.__clean(name + enum.suffix.modify)
		if os.path.exists(name + enum.suffix.temp):
			self.__clean(name + enum.suffix.temp)
	#
	def create(self, lines = ['']):
		if os.path.exists(self.__name):
			self.remove()
		with open(self.__name,"w") as fd:
			for line in lines:
				data = xnString.o2j(line)
				data = '' if data == '""' else data
				fd.write(data+'\n')
	#
	def remove(self, name = None):
		if not name:
			name = self.__name
		self.__clean(name)
		if os.path.exists(name):
			os.remove(name)
			return True
		else:
			return False
	#
	def __modify_rename(self):
		if os.path.exists(self.__name):
			os.remove(self.__name)
		os.rename(self.__mname, self.__name)
	#
	def modify(self, lines = ['']):
		self.__clean()
		with open(self.__tname, "w") as fd:
			for line in lines:
				data = xnString.o2j(line)
				data = '' if data == '""' else data
				fd.write(data + '\n')
		os.rename(self.__tname, self.__mname)
		self.__modify_rename()
		self.cache = lines
	def append(self, line):
		self.modify(self.cache + [line])
	#
	def __checkM(self):
		if os.path.exists(self.__mname):
			self.__modify_rename()
			return True
		else:
			return False
	#
	def __repair(self,name):
		msg = "LOG [ %s ] 已损坏，输入序号完成功能:\n\
		0.重置文件\n\
		1.退出以人工查看\n"%name
		while True:
			mode = input(msg)
			if mode == "0":
				return True
			elif mode == "1":
				return False
			else:
				print("序号错误.")
	#
	def error(self):
		if self.flag_msg and self.__repair(self.__name):
			self.create()
			cache = []
			extid = []
		else:
			sys.exit()
	#
	def check(self):
		if self.__checkM():
			print("LOG [ %s ] :发现之前未完成的日志更新工作，已更新成功"%self.__name)
		self.__clean()
		if not os.path.exists(self.__name):
			self.create()
			print("LOG [ %s ] :已创建日志文件"%self.__name)
			return True
		#get value
		with open(self.__name,"r") as fd:
			lines = str(fd.read()).split('\n')
		self.cache = list(map(lambda x:isItem(x,self.funclist),filter(lambda x:x!="",lines)))
		if None in self.cache:
			flag = False
			self.error()
			return False
		else:
			self.extid = list(set((list(map(lambda x:x['id'],self.cache)))))
			self.__id = reduce(lambda x,y:x if x>y else y,map(lambda x:int(x['id']),self.cache), 0) + 1
		if len(self.cache) >= 1 and self.cache[-1]['action'] == enum.action.exit:
			print("LOG [ %s ] :日志文件已经结束"%self.__name)
			self.__end = True
		return True
	#
	def clearup(self):
		self.finished = list(map(lambda x:x['id'],filter(lambda x:x['action'] == enum.action.end, self.cache)))
		self.cache = list(filter(lambda x:not x['id'] in self.finished,self.cache))
		#self.modify(self.cache)
		self.extid = list(set(map(lambda x:x['id'], self.cache)))
		self.__id = reduce(lambda x,y:x if x>int(y) else int(y), self.extid , 0) + 1
	#
	def getNewId(self):
		self.__id += 1
		return str(self.__id - 1)
	#
	def getUnifData(self, name = "data"):
		if len(self.cache):
			retdict = {}
			retfunc = self.cache[0]['func']
			for data in self.cache:
				if name in data and data['func'] == retfunc:
					retdict[data['id']] = data[name]
				else:
					return None
			return retdict
		else:
			return {}
	#
	def test(self):
		"""
		print("after reading:")
		for line in self.cache:
			print(line)
		print(self.extid)
		print(self.__id)
		self.clearup()
		print("after clearup:")
		for line in self.cache:
			print(line)
		print(self.extid)
		print(self.__id)
		"""
make = lambda id, action, func, data:{'id':str(id),'action':action,'func':func,'data':data}
class Log:
	dirname = "logfile"
	filename = "log"
	suffix = ".txt"
	name = lambda self,label:self.dirname + self.filename + str(label) + self.suffix
	def __init__(self, directory = "logfile", filename = "log"):
		self.dirname = directory
		self.filename = filename if filename else self.filename
		if self.dirname and self.dirname[-1] != '/' and self.dirname[-1] != '\\':
			self.dirname += '/'
		if self.dirname and not os.path.isdir(self.dirname):
			os.makedirs(self.dirname)
		self.main = self.name("_main")
		self.fd = File(self.main)
		self.fd.clearup()
		#self.fd.test()
		if self.fd.isEnd():
			self.fd.create()
		for work in self.fd.finished:
			if self.fd.remove(self.name(work)):
				print("LOG [ %s ] :已结束事务的日志文件 [ %s ] 已删除"%(self.fd.getName(),self.name(work)))
		self.fd.modify(self.fd.cache)
		if self.fd.finished:
			print("LOG [ %s ] :无效事务已被删除"%self.fd.getName())
		self.log = {}
		for LogId in self.fd.extid:
			fd = File(self.name(LogId))
			fd.clearup()
			fd.modify(fd.cache)
			self.log[LogId] = fd
		self.work = {}
		for line in self.fd.cache:
			self.work[line['id']] = make(line['id'],line['action'],line['func'],line['data'])
		print("已载入所有事务的日志")
		print("")
	def __del__(self):
		pass
	#开始事务
	def start(self, func, **args):
		if 'args' in args:
			args = args['args']
		#
		LogId = self.fd.getNewId()
		data = make(LogId, enum.action.begin, func, args)
		#
		self.fd.append(data)
		fd = File(self.name(LogId))
		fd.create()
		#
		self.fd.extid.append(LogId)
		self.log[LogId] = fd
		self.work[LogId] = data
		return LogId
	#预处理完成
	def ready(self, LogId):
		LogId = str(LogId)
		if not LogId in self.fd.extid:
			raise InvalidLogIdError(LogId, self.main)
		data = make(LogId, enum.action.work, self.work[LogId]['func'], self.work[LogId]['data'])
		self.fd.append(data)
		self.work[LogId] = data
	def isReady(self, LogId):
		LogId = str(LogId)
		if not LogId in self.fd.extid:
			raise InvalidLogIdError(LogId, self.main)
		return self.work[LogId]['action'] == enum.action.work
	#结束事务
	def finish(self, LogId):
		LogId = str(LogId)
		if not LogId in self.fd.extid:
			raise InvalidLogIdError(LogId, self.main)
		if self.log[LogId].extid:
			raise UnfinishedFuncError(self.name(LogId), self.log[LogId].extid)
		data = make(LogId, enum.action.end, self.work[LogId]['func'], self.work[LogId]['data'])
		self.fd.append(data)
		#
		self.fd.extid.remove(LogId)
		self.log.pop(LogId)
		self.work.pop(LogId)
	#重启未预处理完成的事务
	def restart(self, LogId):
		LogId = str(LogId)
		if not LogId in self.fd.extid:
			raise InvalidLogIdError(LogId, self.main)
		self.log[LogId].create()
	#向事务内插入开始信息
	def begin(self, LogId, func, **args):
		LogId = str(LogId)
		if not LogId in self.fd.extid:
			raise InvalidLogIdError(LogId, self.main)
		WorkId = self.log[LogId].getNewId()
		data = make(WorkId, enum.action.begin, func, args)
		self.log[LogId].append(data)
		self.log[LogId].extid.append(WorkId)
		return WorkId
	#向事务内插入结束信息
	def end(self, LogId, WorkId, func, **args):
		LogId = str(LogId)
		WorkId = str(WorkId)
		if not LogId in self.fd.extid:
			raise InvalidLogIdError(LogId, self.main)
		if not WorkId in self.log[LogId].extid:
			raise InvalidWorkIdError(WorkId, self.name(LogId))
		data = make(WorkId, enum.action.end, func, args)
		self.log[LogId].append(data)
		self.log[LogId].extid.remove(WorkId)
	#读取事务中的统一格式数据
	def get(self, LogId):
		LogId = str(LogId)
		if not LogId in self.fd.extid:
			raise InvalidLogIdError(LogId, self.main)
		data = self.log[LogId].getUnifData()
		if data == None:
			raise WorkFormatError(self.name(LogId))
		return data
	def getWork(self, LogId):
		LogId = str(LogId)
		if not LogId in self.fd.extid:
			raise InvalidLogIdError(LogId, self.main)
		data = self.work[LogId]
		return data
	#
	def exists(self, LogId):
		LogId = str(LogId)
		return LogId in self.fd.extid
	#
	def test(self):
		print("before:")
		for Lid in self.fd.extid:
			print(self.work[Lid])
		#
		self.start(enum.func.album, Uid = 11111,Aid = 22222)
		if self.work['8']['action'] != enum.action.work:
			self.ready("8")
		self.end('8','1',enum.func.album, Uid = 3333)
		self.finish('8')
		if(self.exists("9")):
			self.finish("9")
		#
		print("after:")
		for Lid in self.fd.extid:
			print(self.work[Lid])
def main():
	pass
	#f = File(r"logfile/log_main.txt")
	#f.test()
	#log = Log()
	#log.test()
	#log.test()
if __name__ == '__main__':
	main()