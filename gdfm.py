## GD FM.py
## 从荔枝网获取广东FM电台的真实播放url，并输出成.m3u8播放列表文件。
## 作者：广州阿健（CSDN ID: Scott0902）
## 创作时间：2022年9月

import requests
import time
import hmac
import re
import base64
import json
import win32api
from hashlib import sha256

# 调用方生成的签名值，使用HmacSHA256算法计算并经Base64编码后的字符串，密钥为签名认证令牌密钥
# 感谢CSDN的王里木目心
def getSignature(XClientId, X_Signature):
    signature = str(base64.b64encode(hmac.new(XClientId.encode('utf-8'), X_Signature.encode('utf-8'), digestmod=sha256).digest()),'utf-8')
    return signature

# 加密算法，感谢简书网的嗷呜呜
def getpage(url):
    d=str(int(time.time()*1000))
    v='GET\n'+url+'\n'+d+'\n'
    signature = getSignature(XClientId,v)
    headers.update({'x-itouchtv-ca-signature': signature,'x-itouchtv-ca-timestamp': d})
    res=se.get(url,headers=headers).text
    return res

headers={'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
'origin': 'https://www.gdtv.cn',
'referer': 'https://www.gdtv.cn/',
'x-itouchtv-ca-key': '89541443007807288657755311869534',
'x-itouchtv-client': 'WEB_PC',
'x-itouchtv-device-id': 'WEB_9527-3547-709394',	# 这里的deviceID随便编都行，但必须以WEB_开头
}

# HMACSHA256的密钥
XClientId = 'dfkcY1c3sfuw0Cii9DWjOUO3iQy2hqlDxyvDXd1oVMxwYAJSgeB6phO8eW1dfuwX'

# 创建一个session对象，使它能够自动记录上一次请求中的cookie信息
se = requests.session()
# 最终生成的.m3u8文件路径和文件名
outputfilename=r'C:\GD FM.m3u8'
# 播放.m3u8的播放器软件路径
player=r'C:\Program Files (x86)\Pure Codec\x64\PotPlayerMini64.exe'

# 获取FM频道名称列表
data=json.loads(getpage('https://gdtv-api.gdtv.cn/api/tv/v2/tvChannel?category=1'))
fm=[]
for i in data:
    fm_number=re.search('audio/fm(.*?).m3u8',i['playUrl'])[1]
    # 数字加小数点，由字符串改为数字，为了最后一步按自然顺序重新排序
    fm_number=float(fm_number[:-1]+'.'+fm_number[-1]) 
    fm.append([str(i['pk']),fm_number,i['name']])


print(f'今天日期：{time.strftime("%Y年%m月%d日",time.localtime())}\n当前时间：{time.strftime("%H:%M:%S",time.localtime())}')
print('-'*80)
# 输出中文，为了对齐，宽度不够时采用中文空格填充
# :<{} 左对齐 :^{} 中间对齐 :>{} 右对齐
# 对齐符号后面的{}表示变量的总宽度
tplt = "{0:^16}\t{1:<16}\t{2:<16}"
print(tplt.format('FM频道','\t当前的节目','主持人',chr(12288)))
print('-'*80)
tplt = "{0:<8}{1:<12}\t{2:<12}\t{3:<12}"
fields=['name','beginAt','endAt','anchor'] # 节目清单需要用到的json字段

for i in fm:

    res=getpage('https://tcdn-api.itouchtv.cn/getParam')
    t2=re.search(':"(.*?)"',res)[1]
    node=str(base64.b64encode(t2.encode('utf-8')),'utf-8')

    play_url='https://gdtv-api.gdtv.cn/api/tv/v2/tvChannel/'+i[0]+'?tvChannelPk='+i[0]+'&node='+node
    # 这一步需要先进行options预验，至关重要！
    res=se.options(play_url)
    # 做完options才做get
    res=getpage(play_url)
    real_url=re.search(r':\\"(.*?)\\',res)[1]
    # 当链接含有auth_key才真正有效
    if 'auth_key' in res:
        i.append(real_url)
        # 获取当前日期，然后获取当天的节目清单
        today=time.strftime("%Y-%m-%d",time.localtime())
        program_url='https://gdtv-api.gdtv.cn/api/tv/v2/tvMenu?tvChannelPk='+i[0]+'&beginAt='+today+'&endAt='+today
        data=json.loads(getpage(program_url))
        data2=data['resultList'][0] #后面要有[0]，否则类型变成list，不是dict
        # 按当前时间来获取当前的节目名称
        now=time.time()*1000
        for k in data2['tvMenus']:
            if now>k[fields[1]] and now<k[fields[2]]:
            	print(tplt.format(f'FM {str(i[1])}',i[2],k[fields[0]],k[fields[3]], chr(12288)))
    else:
        print(f'FM {str(i[1])}的链接被加密，程序终止！')
        exit()
        
# 按自然顺序重新排序
fm.sort(key=lambda x:x[1])
# 写入.m3u文件
file=open(outputfilename,"w",encoding="utf-8")
file.write("#EXTM3U\n")
for i in fm:
    file.write(f'#EXTINF:-1 group-title="广东FM电台",FM {str(i[1])} {i[2]}\n{i[3]}\n')
file.close()
print('-'*80)
print('\n已获取链接并写入.m3u8文件：',outputfilename)
if input('\n现在播放FM请按1，按其他键退出。')=='1':
	win32api.ShellExecute(0,'open',player,outputfilename,'',1)
else:
	exit()
