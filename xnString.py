#coding=utf-8
#! /usr/bin/env python
import json,re
#
import inspect
#
import enum

def getFuncName():
	return inspect.stack()[1][3]

def j2o(data, prerr=True, **args):
	try:
		return json.loads(data)
	except Exception as e:
		if prerr:
			print("Error: json to object")
			print("    data  :",data)
			print("    error :",e)
			print("    args  :",args)
		else:
			pass#raise e
		return None
def o2j(data):
	return json.dumps(data)
def replaceBackSlash(data):
	data.replace("\\","/")
	return data
def jsonFormat(data):
	ret = ""
	for c in data:
		if c == "\n":
			#continue
			pass
		elif c == "'":
			ret = ret + '"'
		else:
			ret = ret + c
	return ret
def getValueByLine(data):
	ret = ""
	flag = False
	for c in data:
		if flag:
			ret += c
		if c == ':':
			flag = True
	ret = ret[:-1]
	if ret[0] == "'" and ret [-1]== "'":
		ret = ret[1:-1]
	else:
		ret = int(ret)
	return ret
def checkDirName(name):
	ret = ""
	for c in name:
		if c in "/\\:*?\"<>|\n\r\t":
			ret += "#"
		elif c == '.':
			ret += "。"
		else:
			ret += c
	return ret
#
def getSuffix(name):
	suffix = r".*(?P<suffix>\.[^\/\\]*)$"
	regex = re.compile(suffix)
	ans = regex.search(name)
	if ans:
		return ans.groupdict()['suffix']
	else:
		return ''
def __testgetSuf():
	print(getFuncName()+"():")
	print(getSuffix("a.jpg"))
	print(getSuffix("/b.jpg"))
	print(getSuffix("a.b/c.jpg"))
	print(getSuffix("abds.dac.dw/"))
	print(getSuffix("abds.dac.dw/a\\"))
	print("")
#

#
httpPre = r"^(?:http:\/\/){0,1}"
suffix = r".*$"
userDF = httpPre + r"www\.renren\.com\/(?P<Uid>[0-9]*)\/profile" + suffix
listDF = httpPre + r"photo\.renren\.com\/photo/(?P<Uid>[0-9]*)\/albumlist\/v7" + suffix
albumDF = httpPre + r"photo\.renren\.com\/photo/(?P<Uid>[0-9]*)\/album-(?P<Aid>[0-9]*)" + suffix
friendDF = httpPre + r"friend\.renren\.com\/(?:groupsdata|managefriends)" + suffix
shareDF = httpPre + r"share\.renren\.com\/share\/[0-9]*\/[0-9]*" + suffix
photoDF = httpPre + r"photo\.renren\.com\/photo\/[0-9]*\/photo-[0-9]*" + suffix
__regex_domain_user = re.compile(userDF)
__regex_domain_list = re.compile(listDF)
__regex_domain_album = re.compile(albumDF)
__regex_domain_friend = re.compile(friendDF)
__regex_domain_share = re.compile(shareDF)
__regex_domain_photo = re.compile(photoDF)
__regex_domain = {
				__regex_domain_user : enum.func.user,
				__regex_domain_list : enum.func.user,
				__regex_domain_album : enum.func.album,
				__regex_domain_friend : enum.func.friend,
				__regex_domain_share : enum.func.share,
				__regex_domain_photo : enum.func.photo}
def analysisDomain(domain):
	global __regex_domain
	regex_list = __regex_domain
	#print(domain)
	for (regex,ret) in regex_list.items():
		ans = regex.search(domain)
		if ans:
			return [ret,ans.groupdict()]
	return [None,None]
def __testDomain():
	print(getFuncName(),"():")
	print(analysisDomain(r"http://www.renren.com/315134008/profile"))
	print(analysisDomain(r"http://photo.renren.com/photo/315134008/albumlist/v7#"))
	print(analysisDomain(r"http://photo.renren.com/photo/315134008/album-315134008/v7"))
	print(analysisDomain(r"http://friend.renren.com/managefriends"))
	print(analysisDomain(r"http://share.renren.com/share/374925814/17919772445"))
	print(analysisDomain(r"http://photo.renren.com/photo/270215571/photo-8220534797"))
	print("")
#

#
title = r"\<title\>人人网 - (?P<Name>.*)\<\/title\>"
__regex_title = re.compile(title)
def getNameFromHtml(html):
	global __regex_title
	regex = __regex_title
	ans = regex.search(html)
	if ans:
		return ans.groupdict()['Name']
	else:
		return None
def __testgetNFH():
	print(getFuncName(),"():")
	with open("test/profile.html","r",encoding = 'UTF-8') as fd:
		print(getNameFromHtml(fd.read()))
	print("")
#

#
selfid = r"id : \"(?P<Id>.*)\""
__regex_selfid = re.compile(selfid)
def getIdFromHtml(html):
	global __regex_selfid
	regex = __regex_selfid
	ans = regex.search(html)
	if ans:
		return ans.groupdict()['Id']
	else:
		return None
def __testgetIFH():
	print(getFuncName(),"():")
	with open("test/profile.html","r",encoding = 'UTF-8') as fd:
		print(getIdFromHtml(fd.read()))
	print("")
#

#
albumListFormat = r"'albumList': (?P<albumlist>\[.*\])"
__regex_albumlist = re.compile(albumListFormat)
def getAlbumlistFromHtml(html, domain, func):
	global __regex_albumlist
	regex = __regex_albumlist
	ans = regex.search(html)
	if ans:
		albumlist = []
		albumdict = j2o(ans.groupdict()['albumlist'],domain = domain, func = func)
		for album in albumdict:
			albumlist.append(album['albumId'])
		return albumlist
	else:
		return []
def __testgetALFH():
	print(getFuncName(),"():")
	with open("test/albumlist.html","r",encoding = 'UTF-8') as fd:
		print(getAlbumlistFromHtml(fd.read(),"",""))
	print("")
#
albumMetadataFormat = r"nx\.data\.photo = \{\"photoList\":(?P<metadata>\{(?:.*\n)*\})\}\;\n"
__regex_album = re.compile(albumMetadataFormat)
def __getValueSpe(text , name, quotes = False):
	rstr = r"\'%s\':%s,"%(name,r"\'(.*)\'" if quotes else "(.*)")
	regex = re.compile(rstr)
	ans = regex.search(text)
	return ans.groups()[0]
def getAlbumFromHtml(html):
	global __regex_album
	regex = __regex_album
	ans = regex.search(html)
	if ans:
		metadata = ans.groupdict()['metadata']
		album = {}
		album['albumId'] = __getValueSpe(metadata,'albumId')
		album['albumName'] = __getValueSpe(metadata,'albumName', quotes = True)
		album['photoCount'] = int(__getValueSpe(metadata,'photoCount'))
		return album
	else:
		return None
def __testgetAFH():
	print(getFuncName(),"():")
	with open("test/album_.html","r",encoding = 'UTF-8') as fd:
		print(getAlbumFromHtml(fd.read()))
	print("")
#

#
def getPhotolist(text, domain, func):
	lines = j2o(text, domain = domain, func = func)
	if 'photoList' in lines:
		ans = lines['photoList']
		return ans
	else:
		return None
def __testgetP():
	print(getFuncName(),"():")
	with open("test/photolist.html","r",encoding = 'UTF-8') as fd:
		print(getPhotolist(fd.read()))
	print("")
#
friendlistFormat = r"\"friends\": (?P<friendlist>\[.*\]),"
__regex_friendlist = re.compile(friendlistFormat)
def getFriendlist(text, domain, func):
	global __regex_friendlist
	regex = __regex_friendlist
	ans = regex.search(text)
	friendlist = j2o(ans.groups()[0],domain = domain, func = func)
	simplelist = []
	for f in friendlist:
		d = {}
		d['id'] = str(f['fid'])
		d['name'] = f['fname']
		simplelist.append(d)
	return simplelist
def __testgetF():
	print(getFuncName(),"():")
	with open("test/friendlist.html","r",encoding = 'UTF-8') as fd:
		print(getFriendlist(fd.read()))
	print("")
#
photoAddress = r"(?P<address>http://photo.renren.com/photo/[0-9]*/photo-[0-9]*)"
__regex_share_photo = re.compile(photoAddress)
def getPhotoFromShareHtml(html):
	global __regex_share_photo
	regex = __regex_share_photo
	ans = regex.search(html)
	if ans:
		return ans.groups()[0]
	else:
		return None
def __testgetPFSH():
	print(getFuncName(),"():")
	with open("test/share.html","r",encoding = 'UTF-8') as fd:
		print(getPhotoFromShareHtml(fd.read()))
	print("")
#
photo2album = r'\"albumId\":\"(?P<Aid>[0-9]*)\".*\"owner\":(?P<Uid>[0-9]*)'
__regex_photo2album = re.compile(photo2album)
def getAlbumFromPhotoHtml(html):
	global __regex_photo2album
	regex = __regex_photo2album
	ans = regex.search(html)
	if ans:
		return ans.groupdict()
	else:
		return None
def __testgetAFPH():
	print(getFuncName(),"():")
	with open("test/photo.html","r",encoding = 'UTF-8') as fd:
		print(getAlbumFromPhotoHtml(fd.read()))
	print("")
#
def __test():
	__testgetSuf()
	__testDomain()
	__testgetNFH()
	__testgetIFH()
	__testgetALFH()
	__testgetAFH()
	__testgetPFSH()
	__testgetAFPH()
#
def main():
	__test()
if __name__ == '__main__':
	main()