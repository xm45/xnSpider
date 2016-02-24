#coding=utf-8
#! /usr/bin/env python
import requests,http,urllib
import sys,os,time
import re,pickle
import signal

import enum
import threadPool
import xnString
import makeLog

defaultDir = r"D:/图片/renren/"
userFile = "userFile.pickle"
rename_file = True

def createFile(filename):
	directory = ""
	name = ""
	for c in filename:
		if c == '/':
			directory = name
		name += c
	if directory != "":
		if os.path.isdir(directory):
			pass
		else:
			os.makedirs(directory)
#
#
class User:
	username = ''
	password = ''
	filename = ''
	def __init__(self, fname):
		self.filename = fname
		if os.path.exists(self.filename):
			self.__load()
		else:
			self.stdio()
	def __load(self):
		fd = open(self.filename, "rb")
		self.username = pickle.load(fd)
		self.password = pickle.load(fd)
		self.filename = pickle.load(fd)
		fd.close()
		print("从文件中读入用户名和密码成功！")
	def __dump(self):
		fd = open(self.filename, "wb")
		pickle.dump(self.username,fd)
		pickle.dump(self.password,fd)
		pickle.dump(self.filename,fd)
		fd.close()
	def stdio(self):
		self.username = input("username:")
		self.password = input("password:")
		self.__dump()
#
class LackParameterError(Exception):
	def __init__(self, pname, args):
		Exception.__init__(self)
		self.message = "\
		Lack of Parameter : can't find parameter \n\
				Parameter : %s\n\
				Dict : %s\n"%(pname,args)
	def __str__(self):
		return str(self.message)
class InvalidModeError(Exception):
	def __init__(self, mode):
		Exception.__init__(self)
		self.message = "Mode is invalid : %s"%(mode)
	def __str__(self):
		return str(self.message)
class SelfidDiffError(Exception):
	def __init__(self, now, log):
		Exception.__init__(self)
		self.message = "the selfid is DIFFERENT with LOG: now[ %s ] log[ %s ]"%(now,log)
	def __str__(self):
		return str(self.message)
#
#
class Spider:
	#构造函数
	def __init__(self, logdir = "lg",prwork = True, prdown = True):
		self.__session = requests.session()
		#线程池
		self.__pool = threadPool.Pool(8)
		self.__cnt = 0
		self.flag_pwm = prwork#print work message flag
		self.flag_pdm = prdown#print download message flag
		self.work_msg = lambda msg: self.flag_pwm and print(msg,end="",flush=True)
		self.down_msg = lambda msg: self.flag_pdm and print(msg,end="",flush=True)
		self.log = makeLog.Log(logdir)
		self.selfid = 0
	#登录
	def login(self, user):
		#定义post的参数
		reqdata={'email':user.username,
		'password':user.password,
		'autoLogin':'true',
		'origURL':'http://www.renren.com/home',
		'domain':'renren.com'
		}
		domain = r"http://www.renren.com/ajaxLogin/login?1=1"
		response = self.__session.post(domain, data = reqdata)
		resdict = xnString.j2o(response.text)
		if resdict['code'] == True:
			self.work_msg("\n登陆成功！\n")
			self.work_msg("您的用户ID是: %s \n"%self.__getSelfUid())
			self.work_msg("您的用户名是: %s \n"%self.getNameByUid(self.selfid))
			self.work_msg("您的 cookies: %s \n"%self.getcookies())
			return True
		else:
			self.work_msg("\n登录失败！\n")
			self.work_msg(resdict['failDescription']+'\n')
			return False
	#登出
	def logout(self):
		domain = r"http://www.renren.com/Logout.do"
		response = self.getHtml(domain)
		self.work_msg(response+'\n')
	#获取网页内容
	def getHtml(self, domain, stream = False, timeout = 50):
		ret = None
		while True:
			try:
				ret = self.__session.get(domain, stream = stream, timeout = timeout)
				if ret.status_code != 200 or len(ret.content) < 200:
					print(ret.status_code, len(ret.content), domain)
					print(ret.text)
					time.sleep(1)
					continue
					return None
				retlen = len(ret.content)
				reqlen = ret.headers.get('Content-Length')
				if  reqlen != None and retlen < int(reqlen):
					print("Length Inconsistency");
					print("domain: ",domain)
					print(reqlen)
					print(retlen)
					print("retry")
					continue
				return ret
			except Exception as e:
				print("\n")
				print(e)
				time.sleep(1)
	#获取cookies
	def getcookies(self, domain = r"http://www.renren.com/home"):
		response = self.getHtml(domain)
		return response.cookies.get_dict()
	#获取自己的名字
	def __getSelfUid(self):
		domain = r"http://www.renren.com/home"
		response = self.getHtml(domain)
		self.selfid = xnString.getIdFromHtml(response.text)
		return self.selfid
	#获取用户名
	def getNameByUid(self, Uid):
		domain = r"http://www.renren.com/%s/profile"%Uid
		response = self.getHtml(domain)
		name = xnString.getNameFromHtml(response.text)
		if name:
			return name
		else:
			work_msg("ERROR: 无法从用户id[ %s ]解析出用户名\n"%Uid)
			return "NULL"
	#计数函数
	def recount(self):
		self.__cnt = 0
	def __count(self, num = 1):
		self.__cnt += num
	def count(self):
		return self.__cnt
	#等待下载任务结束
	def wait_allcomplete(self, data = ""):
		self.__pool.wait_allcomplete(data, self.flag_pdm)
	#获取相册列表
	def getAlbumlist(self, Uid):
		domain = "http://photo.renren.com/photo/%s/albumlist/v7"%Uid
		response = self.getHtml(domain)
		albumlist = xnString.getAlbumlistFromHtml(response.text, domain, 'getAlbumlist')
		if albumlist:
			return albumlist
		else:
			self.work_msg("\t\t从用户id[ %s ]获取用户信息失败\n"%Uid)
			return []
	#下载相册
	def makeAlbumName(self, old_name, Uid):
		if old_name in ['快速上传','手机相册','头像相册']:
			return old_name + "—" + self.getNameByUid(Uid)
		else:
			return old_name
	def getAlbum(self, Uid, Aid, directory = defaultDir):
		global rename_file
		plist = r'http://photo.renren.com/photo/%s/album-%s/bypage/ajax/v7?page=%d&pageSize=100'
		domain = "http://photo.renren.com/photo/%s/album-%s/v7"%(Uid,Aid)
		response = self.getHtml(domain)
		#
		metadata = xnString.getAlbumFromHtml(response.text)
		if metadata == None:
			self.work_msg("\t\t获取相册[ %s  %s ]信息失败，可能是因为加密\n"%(Uid,Aid))
			return
		#
		#self.__cnt += metadata['photoCount']
		#
		if metadata['photoCount'] == 0:
			return
		pageId = 1

		metadata['albumName'] = self.makeAlbumName(metadata['albumName'], Uid)

		adir = directory + xnString.checkDirName(metadata['albumName'])+'/'
		createFile(adir)
		if self.flag_pdm:
			self.work_msg("\t\t开始下载\t相册\t[%4d]\t<%s>"%(metadata['photoCount'],metadata['albumName']))
		else:
			self.work_msg("\t\t开始下载\t相册\t[%4d]\t<%s>\n"%(metadata['photoCount'],metadata['albumName']))
		while (pageId-1)*100 < metadata['photoCount']:
			while True:
				try:
					page = plist%(Uid, Aid, pageId)
					response = self.getHtml(page)
					photolist = xnString.getPhotolist(response.text, page, 'getPhotolist')
					break
				except:
					pass
			if photolist:
				for photo in photolist:
					url = photo['url']
					pos = str(photo['position'])
					if rename_file:
						filename = adir + pos + xnString.getSuffix(url)
					else:
						#test
						purl = url.split('/')
						filename = adir + purl[-1]
						#test
					if os.path.exists(filename) and os.path.getsize(filename) != 0:
						continue
					else:
						self.__count()
						self.__pool.add_job(self.getPicT, url, filename)
					#getPic(photo, adir)
			else:
				self.work_msg("找不到photoList, User:%s Album:%s Page:%d\n"%(Uid,Aid,pageId))
			pageId += 1

	#下载图片
	def getPic(self, url, filename, mutex):
		#pl = filename.split('/')
		#pname = pl[-1]
		response = self.getHtml(url,stream = True)
		if not response:
			return
		while True:
			mutex.acquire()
			with open(filename,"wb") as fd:
				fd.write(response.content)
				fd.flush()
			mutex.release()
			if os.path.getsize(filename) != 0:
				break
	#包装给线程池
	def getPicT(self, args, mutex):
		self.getPic(args[0],args[1],mutex)
	#获取路径名
	def getDirName(self, Uid, Uname = "", directory = defaultDir):
		Uname = Uname or self.getNameByUid(Uid)
		dirname = directory + xnString.checkDirName(Uname) + "   "+ Uid +'/'
		return dirname
	#获取好友列表
	def getFriends(self):
		domain = "http://friend.renren.com/groupsdata"
		response = self.getHtml(domain)
		friends = xnString.getFriendlist(response.text, domain, 'getFriends')
		return friends
	#无log版本
	def work_nolog(self, mode, directory = defaultDir, **args):
		if 'args' in args:
			args = args['args']
		if mode == enum.func.album:
			if not 'Uid' in args:
				LackParameterError('Uid', args)
			if not 'Aid' in args:
				LackParameterError('Aid', args)
			#
			#print(args)
			self.getAlbum(args['Uid'], args['Aid'], directory+"_相册/")
			#
		elif mode == enum.func.user:
			if not 'Uid' in args:
				LackParameterError('Uid', args)
			#
			Uid = args['Uid']
			Uname = self.getNameByUid(Uid)
			albumlist = self.getAlbumlist(Uid)
			#
			dirname = self.getDirName(Uid, Uname, directory)
			self.work_msg("%s %s\n"%(Uid, Uname))
			for albumId in albumlist:
				self.getAlbum(Uid, albumId, dirname)
			#
		elif mode == enum.func.friend:
			if not 'selfid' in args:
				LackParameterError('selfid', args)
			friends = self.getFriends()
			#
			temp = self.flag_pdm
			self.flag_pdm = False
			for f in friends:
				albumlist = self.getAlbumlist(f['id'])
				dirname = self.getDirName(f['id'], f['name'], directory)
				self.work_msg("%s %s\n"%(f['id'], f['name']))
				for albumId in albumlist:
					self.getAlbum(f['id'], albumId, dirname)
				self.wait_allcomplete("该用户下载完成\n")
			self.flag_pdm = temp
		else:
			InvalidModeError(mode)
	#有log版本
	def work(self, mode , directory = defaultDir, uselog = True, **args):
		if 'args' in args:
			args = args['args']
		for attr in enum.need[mode]['input']:
			if attr not in args:
				LackParameterError(attr, args)
		if not uselog:
			self.work_nolog(mode, directory, args = args)
			return
		#判断
		args['directory'] = directory
		args['selfid'] = self.selfid
		LogId = self.log.start(mode, args = args)
		#开始
		work = {}
		if mode == enum.func.user:
			Uid = args['Uid']
			Uname = self.getNameByUid(Uid)
			albumlist = self.getAlbumlist(Uid)
			for albumId in albumlist:
				WorkId = self.log.begin(LogId, enum.func.album, Aid = albumId, Uname = Uname)
				work[WorkId] = albumId
		elif mode == enum.func.friend:
			friends = self.getFriends()
			for f in friends:
				WorkId = self.log.begin(LogId, enum.func.user, id = f['id'], name = f['name'])
				work[WorkId] = f
		self.log.ready(LogId)
		#准备完成
		if mode == enum.func.album:
			dirname = directory + "_相册/"
			self.getAlbum(args['Uid'], args['Aid'], dirname)
			self.wait_allcomplete("\n该相册下载完成\n")
			self.log.finish(LogId)
		elif mode == enum.func.user:
			dirname = self.getDirName(Uid, Uname, directory)
			self.work_msg("%s %s\n"%(Uid, Uname))
			for WorkId in work:
				albumId = work[WorkId]
				self.getAlbum(Uid, albumId, dirname)
				self.wait_allcomplete("\n该相册下载完成\n")
				self.log.end(LogId, WorkId, enum.func.album)
			self.log.finish(LogId)
		elif mode == enum.func.friend:
			for WorkId in work:
				f = work[WorkId]
				albumlist = self.getAlbumlist(f['id'])
				dirname = self.getDirName(f['id'], f['name'], directory)
				self.work_msg("%s %s\n"%(f['id'], f['name']))
				#
				temp = self.flag_pdm
				self.flag_pdm = False
				for albumId in albumlist:
					self.getAlbum(f['id'], albumId, dirname)
				self.work_msg("\n等待下载完成\n")
				self.flag_pdm = temp
				#
				self.wait_allcomplete("\n该用户下载完成\n")
				self.log.end(LogId, WorkId, enum.func.user)
			self.log.finish(LogId)
		else:
			InvalidModeError(mode)
	#重启工作
	def recover(self, LogId = 0):
		args = self.log.getWork(LogId)
		if 'directory' not in args['data']:
			LackParameterError('directory',args['data'])
		directory = args['data']['directory']
		mode = args['func']
		for attr in enum.need[mode]['input']:
			if attr not in args['data']:
				LackParameterError(attr, args)

		work = {}
		if args['action'] == enum.action.end:
			self.log.finish(LogId)
			return
		elif args['action'] == enum.action.begin:
			self.log.restart(LogId)
			if mode == enum.func.user:
				Uid = args['data']['Uid']
				Uname = self.getNameByUid(Uid)
				albumlist = self.getAlbumlist(Uid)
				for albumId in albumlist:
					WorkId = self.log.begin(LogId, enum.func.album, Aid = albumId, Uname = Uname)
					work[WorkId] = albumId
			elif mode == enum.func.friend:
				friends = self.getFriends()
				for f in friends:
					WorkId = self.log.begin(LogId, enum.func.user, id = f['id'], name = f['name'])
					work[WorkId] = f
			self.log.ready(LogId)
		elif args['action'] == enum.action.work:
			if not 'selfid' in args['data']:
				LackParameterError('selfid',args['data'])
			if self.selfid != args['data']['selfid']:
				raise SelfidDiffError(self.selfid, args['data']['selfid'])
			if 'Uid' in args['data']:
				Uid = args['data']['Uid']
				Uname = self.getNameByUid(Uid)
			if 'Aid' in args['data']:
				Aid = args['data']['Aid']
			work = self.log.get(LogId)
		#准备完成
		if mode == enum.func.album:
			dirname = directory + "_相册/"
			self.getAlbum(Uid, Aid, dirname)
			self.wait_allcomplete("\n该相册下载完成\n")
			self.log.finish(LogId)
		elif mode == enum.func.user:
			dirname = self.getDirName(Uid, Uname, directory)
			self.work_msg("%s %s\n"%(Uid, Uname))
			for WorkId in work:
				albumId = work[WorkId]['Aid']
				self.getAlbum(Uid, albumId, dirname)
				self.wait_allcomplete("\n该相册下载完成\n")
				self.log.end(LogId, WorkId, enum.func.album)
			self.log.finish(LogId)
		elif mode == enum.func.friend:
			for WorkId in work:
				f = work[WorkId]
				albumlist = self.getAlbumlist(f['id'])
				dirname = self.getDirName(f['id'], f['name'], directory)
				self.work_msg("%s %s\n"%(f['id'], f['name']))
				#
				temp = self.flag_pdm
				self.flag_pdm = False
				for albumId in albumlist:
					self.getAlbum(f['id'], albumId, dirname)
				self.work_msg("\n等待下载完成\n")
				self.flag_pdm = temp
				#
				self.wait_allcomplete("\n该用户下载完成\n")
				self.log.end(LogId, WorkId, enum.func.user)
			self.log.finish(LogId)
		else:
			InvalidModeError(mode)
	#分析域名
	def Domain(self, domain):
		mode,args = xnString.analysisDomain(domain)
		return [mode,args]
class SpiderCmd(Spider):
	def __init__(self, logdir = "lg",prwork = True, prdown = True):
		super(SpiderCmd, self).__init__(logdir, prwork, prdown)
	def getByAll(self):
		self.recount()
		start = time.time()
		self.work(enum.func.friend)
		self.wait_allcomplete("\n本次下载完成\n")
		end = time.time()
		print("总共 %s 张图片  耗时 %s"%(self.count(), end-start))
	def getByUser(self):
		Uid = input('假设该用户主页为：http://www.renren.com/用户id/profile，请输入该id：')
		print("开始解析与下载\n\
			'|'代表检索到一张已存在图片\n\
			'*'代表下载完一张未下载图片\n")
		self.recount()
		start = time.time()
		self.work(enum.func.user, Uid = Uid)
		self.wait_allcomplete("\n该用户下载完成\n")
		end = time.time()
		print("总共 %s 张图片  耗时 %s"%(self.count(), end-start))
	def getByAlbum(self):
		Uid = input('假设该用户主页为：http://photo.renren.com/photo/用户id/album-相册id，请输入用户id：')
		Aid = input('假设该用户主页为：http://photo.renren.com/photo/用户id/album-相册id，请输入相册id：')
		print("开始解析与下载\n\
			'|'代表检索到一张已存在图片\n\
			'*'代表下载完一张未下载图片\n")
		self.recount()
		start = time.time()
		#self.getAlbum(Uid,Aid)
		self.work(enum.func.album, Uid = Uid, Aid = Aid)
		self.wait_allcomplete("\n该相册下载完成\n")
		end = time.time()
		print("总共 %s 张图片  耗时 %s"%(self.count(), end-start))
	def getByDomain(self):
		msg = '\n可分析的有 \n\t相片地址\n\t分享相片地址\n\t相册地址\n\t相册列表地址\n\t个人主页地址\n\t自己好友列表地址\n\t输入finish退出\n\t输入exit结束\n请输入地址：'
		while True:
			domain = input(msg)
			if domain == "finish":
				return
			if domain == "exit":
				exit(0)
			mode,args = self.Domain(domain)
			if not mode:
				print("无法解析的地址")
				continue
			if mode == enum.func.share:
				response = self.getHtml(domain)
				domain = xnString.getPhotoFromShareHtml(response.text)
				if not domain:
					print("无法从分享页面分析出照片地址")
					continue
				mode = enum.func.photo
			if mode == enum.func.photo:
				response = self.getHtml(domain)
				args = xnString.getAlbumFromPhotoHtml(response.text)
				if not args:
					print("无法从照片地址分析出相册地址")
					continue
				mode = enum.func.album
			self.recount()
			start = time.time()
			self.work(mode, args = args)
			self.wait_allcomplete("\n本次下载完成\n")
			end = time.time()
			print("总共 %s 张图片  耗时 %s"%(self.count(), end-start))
	def getByLog(self):
		while True:
			while True:
				print("选择LOG文件,输入0退出")
				for WorkId in self.log.work:
					line = self.log.work[WorkId]
					print("\t\t%s\t\t下载对象:%s\t\t下载阶段:%s\t\t数据:%s"%(line['id'],line['func'],line['action'],line['data']))
				LogId = input("\n输入序号:")
				if not LogId in self.log.fd.extid:
					if LogId == '0':
						return
					print("序号错误")
				else:
					break
			self.recount()
			start = time.time()
			self.recover(LogId)
			self.wait_allcomplete("\n本次下载完成\n")
			end = time.time()
			print("总共 %s 张图片  耗时 %s"%(self.count(), end-start))
def controller():
	global userFile
	work = SpiderCmd()
	while True:
		user = User(userFile)
		print("删除%s文件即可重新设置账户信息\n"%userFile)
		print("本程序未使用验证码，短时间内多次启动将无法使用")
		print("重复登录严重者将被暂时冻结人人账号(可自行解封)")
		if work.login(user):
			break
		if os.path.exists("userFile.pickle"):
			os.remove("userFile.pickle")
	while True:
		msg = '\n输入序号启动指定功能\n\
			0.退出\n\
			1.下载本账户全部好友的相册\n\
			2.下载指定用户的全部相册\n\
			3.下载指定相册\n\
			4.输入网址，自动分析类型\n\
			5.使用日志文件恢复中断的工程\n'
		mode = input(msg)
		if mode == "0":
			break
		elif mode == "1":
			work.getByAll()
		elif mode == "2":
			work.getByUser()
		elif mode == "3":
			work.getByAlbum()
		elif mode == "4":
			work.getByDomain()
		elif mode == "5":
			work.getByLog()
		else:
			print("序号错误\n")
def main():
	controller()
	pass
if __name__ == '__main__':
	main()