#don't table
#coding=utf-8
#! /usr/bin/env python
class ConstError(Exception):
	def __init__(self):
		Exception.__init__(self)
		self.message = "try to modify the constant object"
	def __str__(self):
		return str(self.message)
class ConstNoneError(Exception):
	def __init__(self):
		Exception.__init__(self)
		self.message = "try to set a None value "
	def __str__(self):
		return str(self.message)
class pair(object):
	__key = "key"
	__value = "value"
	def __init__(self,key,value):
		self.__key = key
		self.__value = value
	def __str__(self):
		return self.var().__str__()
	def __call__(self):
		return self.__value
	__repr__ = __str__
	def key(self):
		return self.__key
	def value(self):
		return self.__value
	def var(self):
		return (self.__key,self.__value)
class const(object):
	def __init__(self, *args):
		if len(args)%2 == 0:
			begin = 0
			self.__main = None
		else:
			begin = 1
			self.__main = args[0]
		for i in range(begin,len(args),2):
			self.__setattr__(args[i],args[i+1])
	def __str__(self):
		line = []
		for d in self.__dict__.values():
			line += [d]
		return line.__str__()
	__repr__ = __str__
	def __setattr__(self, name, value):
		#print("setattr",name,value)
		if value == None and name != '_const__main':
			raise ConstNoneError
		if name in self.__dict__:
			raise ConstError
		else:
			self.__dict__[name] = pair(name,value)
	def __getattr__(self, name):
		return None
	def __getitem__(self,name):
		if name in self.__dict__:
			return self.__dict__[name]
		else:
			return None
	def __call__(self):
		return self.__main
	def __iter__(self):
		return self.__dict__.__iter__()
	#def __next__(self):
	#	self.__dict__.next()
	def has(self, name):
		return hasattr(self,name)
	def list(self):
		for v in self.__dict__:
			print(self.__dict__[v].var())
	def name(self):
		return self.__main
def main():
	a = const("first",'a','A','b','B')
	b= const("name",'c',const('c','C'),'d',const('d','D'))
	#a.list()
	#print(a)
	#b.list()
	#a.list()
	print(a)
	for v in a:
		print(v)
	#a.__list = []
	#print(a.__list)
if __name__ == '__main__':
	main()