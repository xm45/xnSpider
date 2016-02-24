#coding=utf-8
#! /usr/bin/env python
import queue
import threading
import time
#no lock !!!
class Pool:
	def __init__(self, thread_num = 10):
		self.works = queue.Queue(100000)
		self.threads = []
		self.filemutex = threading.Lock()
		self.__init_threads(thread_num)
		self.last = -1
		self.lasttime = 5
	def __init_threads(self, thread_num):
		self.mutex = threading.Lock()
		self.data = {}
		self.set('cnt', 0)
		for i in range(thread_num):
			mutex = threading.Lock()
			data = {}
			thread = Consumer(self.works, mutex, data, self.mutex, self.data, self.filemutex)
			tdict = {'tid':i,'mutex':mutex,'data':data,'thread':thread}
			self.threads.append(tdict)
	def add_job(self, func, *args):
		self.add('cnt', 1)
		self.works.put((func, list(args)))
	def wait_allcomplete(self, inf = "\nall complete", pr = True):
		while True:
			size = self.getSize()
			if size != self.last:
				if pr:
					print(size,end = " ",flush = True)
				#if size == 1:
				#	self.pr()
			if size != 0:
				if self.last == -1:
					ti = self.lasttime
				else:
					ti = (self.last - size) / self.lasttime * size
				if ti < 0.5:
					ti = 0.5
				if ti > 5:
					ti = 5
				time.sleep(ti)
				self.last = size
				self.lasttime = ti
			else:
				self.last = -1
				self.lasttime = 5
				break
		"""
		while self.works.qsize()!=0:
			time.sleep(1)#print(self.works.qsize(),flush=True)
		for tdict in self.threads:
			tid = tdict['tid']
			mutex = tdict['mutex']
			data = tdict['data']
			thread = tdict['thread']
			if thread.isAlive():
				while thread.get('running') == True:
					time.sleep(1)
		"""
		print(inf,flush = True)
	def get(self, name):
		self.mutex.acquire()
		if name not in self.data:
			ret = None
		else:
			ret = self.data[name]
		self.mutex.release()
		return ret
	def set(self, name, value):
		self.mutex.acquire()
		self.data[name] = value
		self.mutex.release()
	def add(self, name, value = 1):
		self.mutex.acquire()
		self.data[name] += value
		self.mutex.release()
	def getSize(self):
		return self.get('cnt')
	def pr(self):
		for tdict in self.threads:
			data = tdict['data']
			print("%s %s %s"%(data['name'],data['cnt'],data['running']))
class Consumer(threading.Thread):
	def __init__(self, work_queue, mutex, data, fmutex, fdata, filemutex):
		threading.Thread.__init__(self)
		self.work_queue = work_queue
		self.mutex = mutex
		self.data = data
		self.fmutex = fmutex
		self.fdata = fdata
		self.filemutex = filemutex
		#self.running = False
		self.setDaemon(True)
		self.start()
	def run(self):
		self.set('running',False)
		self.set('cnt', 0)
		self.set('name', threading.current_thread())
		while True:
			func,args = self.work_queue.get()
			self.set('running',True)
			while True:
				try:
					func(args, mutex = self.filemutex)
					break
				except Exception as e:
					print()
					print(e)
			self.add('cnt', 1)
			self.fadd('cnt', -1)
			self.work_queue.task_done()
			self.set('running',False)
	def fadd(self, name, value):
		self.fmutex.acquire()
		self.fdata[name] += value
		self.fmutex.release()
	def add(self, name, value = 1):
		#self.mutex.acquire()
		self.data[name] += value
		#self.mutex.release()
	def set(self, name, value):
		#self.mutex.acquire()
		self.data[name] = value
		#self.mutex.release()
	def get(self, name):
		#self.mutex.acquire()
		if name not in self.data:
			ret = None
		else:
			ret = self.data[name]
		#self.mutex.release()
		return ret
def do_job(args):
	#time.sleep(0.01)#模拟处理时间
	print(threading.current_thread(), list(args), flush=True)
	pass
if __name__ == '__main__':
	start = time.time()
	work_manager =  Pool(60)
	print("main")
	for i in range(1,1000):
	    work_manager.add_job(do_job,i)
	work_manager.wait_allcomplete()
	end = time.time()
	print("cost all time: %s" % (end-start))
	exit(0)