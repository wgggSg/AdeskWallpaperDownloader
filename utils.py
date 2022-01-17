import os
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from mergeImg import merge_images

import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

def mkdir(path):
    path=path.strip()
    path=path.rstrip("\\")
    if not os.path.exists(path):
        os.makedirs(path) 
        return True
    else:
        return False
    
def get_yaml_data(yaml_file):
    # 打开yaml文件
    file = open(yaml_file, 'r', encoding="utf-8")
    file_data = file.read()
    data = yaml.load(file_data,Loader=Loader)
    file.close()
    return data

def getImageFromUrl(url,resize=(0,0)):
    if resize != (0,0):
        flag = url.find("?sign")
        w, h = resize
        if flag<0:
            url = url + "?imageMogr2/thumbnail/!{0}x{1}r/gravity/Center/crop/{0}x{1}".format(w,h)
        else:
            url = url[:flag+1] + "imageMogr2/thumbnail/!{0}x{1}r/gravity/Center/crop/{0}x{1}&".format(w,h) + url[flag+1:]
    resp = requests.get(url,headers={'User-Agent': config['user-agent']})
    return Image.open(BytesIO(resp.content))

def getJson(url):
    resp = requests.get(url,headers={'User-Agent': 'picasso,300,nearme'})
    return resp.json()

def getCategorys():
    """
        return a categorys dict : 'id','rname'
    """
    categorys_json = getJson(r"http://service.picasso.adesk.com/v1/wallpaper/category")
    return categorys_json["res"]["category"][::-1]

def getWallpapers(cid,page=1,pagesize=8,order='new'):
    # eg http://service.picasso.adesk.com/v1/wallpaper/category/4e4d610cdf714d2966000003/wallpaper?limit=10&skip=0&adult=true&first=1&order=hot
    wallpapers_json = getJson("http://service.picasso.adesk.com/v1/wallpaper/category/" + cid
                              + "/wallpaper?limit=" + str(pagesize)
                              + "&skip=" + str((page-1)*pagesize)
                              + "&adult=false&first=0&order=" + order)["res"]["wallpaper"]
    return wallpapers_json

def drawText(image,text,font_pth='source\令东齐伋体(QIJIFALLBACK).ttf',fillColor='#000000',direction=None):
    draw = ImageDraw.Draw(image)
    setFont = ImageFont.truetype(font_pth,100)
    draw.text((40,40),text,font=setFont,fill=fillColor,direction=None)

def displayWallpapers(wallpapers):
    wallpaper_images = list()
    for i,wp in enumerate(wallpapers):
        # eg: http://img5.adesk.com/5c90894fe7bce7558d790953?imageMogr2/thumbnail/!640x480r/gravity/Center/crop/640x480
        url = wp["preview"]
        flag = url.find("?sign")
        if flag<0:
            url = url + "?imageMogr2/thumbnail/!640x480r/gravity/Center/crop/640x480"
        else:
            url = url[:flag+1] + "imageMogr2/thumbnail/!640x480r/gravity/Center/crop/640x480&" + url[flag+1:]
        wp_img = getImageFromUrl(url)
        # plt.subplot(plt_row,plt_col,i+1)
        # plt.imshow(wp_img)
        wallpaper_images.append(wp_img)
        print("\r加载过程{}/{}({}%): ".format(i+1,len(wallpapers),100*((i+1)/len(wallpapers)))+"▋" * int(20*((i+1)/len(wallpapers))), end="")
    merge_images(wallpaper_images,400,4).show()
    print(" 加载完成")
    
def download_wallpaper_byidx(rname,wallpapers,idx,root_dir='',debug=False):
    if debug:
        print("图片 {} 下载中......".format(idx+1))
    download_wallpaper(rname,wallpapers[idx]['img'],wallpapers[idx]['id'],root_dir)
    if debug:
        print("图 {} 保存成功！".format(idx+1))
        
def download_wallpaper(rname,url,filename,root_dir='',debug=False):
    if debug:
        print("图片 {} 下载中......".format(rname))
    dir_name =  root_dir + rname + "/"
    mkdir(dir_name)
    getImageFromUrl(url).save(dir_name + filename + ".png")
    if debug:
        print("图 {} 保存成功！".format(rname))
    
        
def getDlUrlFromURL(url):
    mark1 = 'imageMogr2'
    mark2 = 'sign'
    flag1 = url.find(mark1)
    flag2 = url.find(mark2)
    if flag1>-1:
        url = url[:flag1]+url[flag2:]
    return url



plt_row = 2
plt_col = 4
pagesize = plt_row * plt_col
root_dir = ""
config = get_yaml_data('config.yaml')
    
def program(categorys):
    for i,c in enumerate(categorys):
        print(i+1,c['rname'],end=' ',sep=':')
    print("\n请选择壁纸分类：",end="")
    try:
        cid_num = int(input())
    except:
        return
    if cid_num<1:
        return False
    cid = categorys[cid_num-1]['id']
    rname = categorys[cid_num-1]['rname']
    print(cid)
    while(True):
        print("[{}]请输入页数（默认为1，输入<1退出）:".format(rname),end="")
        try:
            page = int(input())
        except:
            print("请输入数字！！")
            continue
        if page<1:
            break
        
        wallpapers = getWallpapers(cid,page,pagesize)
        print(rname,"初始化完成，加载中...")
        displayWallpapers(wallpapers)
        
        while(True):
            print("[{}]保存图片（输入不存在的序号退出）：".format(rname),end="")
            try:
                img_index = int(input())
            except:
                print("请输入数字！！")
                continue
            if img_index<1 or img_index>pagesize:
                break
            
            download_wallpaper_byidx(rname,wallpapers,img_index-1,root_dir,debug=True)
    return True

if __name__ == '__main__':
    print('初始化...')
    categorys = getCategorys()
    print('初始化完成')
    while(program(categorys)):pass