import requests
import re
import webbrowser
import xmnlp
import jieba
import jieba.posseg as pseg
import jieba.analyse
import PIL
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw
from snownlp import SnowNLP
from lxml import etree
from collections import Counter
from bottle import route, run, template, request, redirect

################################################################
#供run_main调用

def handle_text(text_list):
    text2_list = []
    for text in text_list:
        a = re.findall('(.*?)//@', text)
        if len(a) == 0:
            text2_list.append(text)
        if len(a)>0:
            text2_list.append(a[0])
            
    text3_list = []
    for text in text2_list:
        a = re.findall('.*转发理由(.*?)', text)
        text = text.replace('[组图共','')
        text = text.replace('原图','')
        if len(a) == 0:
             if len(text)>0:
                    text3_list.append(text)
        if len(a)>0:
             if len(a[0])>0:
                    text3_list.append(a[0])
    return text3_list

def getcookies(cookie):
    cookies = {}
    for line in cookie.split(';'):
        name, value = line.strip().split('=', 1)
        cookies[name]=value
    return cookies

def get_pages_num(UID, cookies):
    url_1 = "https://weibo.cn/" + str(UID) + "?page=1"
    res1 = requests.get(url_1, cookies = cookies)
    a1 = re.findall('.*1/(.*)页</div>.*', res1.text)

    url_2 = "https://weibo.cn/" + str(UID) + "?page=2"
    res2 = requests.get(url_2, cookies = cookies)
    a2 = re.findall('.*2/(.*)页</div>.*', res2.text)

    url_3 = "https://weibo.cn/" + str(UID) + "?page=3"
    res3 = requests.get(url_3, cookies = cookies)
    a3 = re.findall('.*3/(.*)页</div>.*', res3.text)

    for a in [a1, a2, a3]:
        try:
            if int(a[0]) >0 and int(a[0]) <9999:
                pages_count = int(a[0])
                return pages_count
        except:
            pages_count = 500

    return pages_count
'''
    if len(''.join(a)) == 0 or len(''.join(a))>20:
        print('获取总页数出现问题')
        pages_count = 500
    else:
        pages_count = int(a[0])
    return pages_count

'''

def get_html(url,cookies):
    re = requests.get(url,cookies=cookies)
    return re.content    


def get_comment(lxml):
    text=[]
    count =1
    html = etree.HTML(lxml)

    if html == None:
        return 'nothing'

    all_comments = html.xpath('//div[@class="c"]')

    if len(all_comments) == 0:
        return 'nothing'

    for each in all_comments:
        comment = each.xpath('string(.)')+"\n\n"
        text.append(comment)
        count+=1
        if count == len(all_comments)-1:
            break
    return text

def get_cuts_list(pages_count, UID, cookies):
    cuts_list = []
    for page in range(0, pages_count):
        page = page +1
        url = "https://weibo.cn/" + str(UID) + "?page=" + str(page)
        lxml = get_html(url,cookies)
        cuts_tmp = get_comment(lxml)
        if cuts_tmp == 'nothing':
            break
        else:
            cuts_list.extend(cuts_tmp)
    return cuts_list

def get_feats(cuts_list):
    originals_list = []
    reposts_list = []
    time_list = []
    text_list = []
    like_sum = 0
    repost_sum = 0
    comment_sum = 0
    for content in cuts_list:
        tmp = re.findall('(转发了\xa0+)', content)
        tmp1 = re.findall('(..:..)', content)
        if len(tmp1)>0:
            time_list.append(tmp1[-1])
        if len(tmp) >0:
            reposts_list.append(content)
            try:
                like_sum += int(re.findall('赞[[](.*?)[]]\xa0.*', content[content.find('转发理由'):])[0])
            except:
                pass
            try:
                repost_sum += int(re.findall('转发[[](.*?)[]]\xa0.*', content[content.find('转发理由'):])[0])
            except:
                pass
            try:
                comment_sum += int(re.findall('评论[[](.*?)[]]\xa0.*', content[content.find('转发理由'):])[0])
            except:
                pass
            try:
                text_list.append(re.findall('转发理由:(.*)赞.*', content)[0])
            except:
                pass

        if len(tmp) == 0:
            originals_list.append(content)
            try:
                like_sum += int(re.findall('赞[[](.*?)[]]\xa0.*', content)[0])
            except:
                pass
            try:
                repost_sum += int(re.findall('转发[[](.*?)[]]\xa0.*', content)[0])
            except:
                pass
            try:
                comment_sum += int(re.findall('评论[[](.*?)[]]\xa0.*', content)[0])
            except:
                pass
            try:
                text_list.append(re.findall('(.*)赞.*', content)[0])
            except:
                pass
    return originals_list, reposts_list, time_list, text_list, like_sum, repost_sum, comment_sum

def handle_time(time_list):
    time2_list = []
    a = ['0','1','2','3','4','5','6','7','8','9']
    for time in time_list:
        if time[0]  in a:
            time2 = time[:2]
            time2_list.append(time2)
    aa = Counter(time2_list)
    bb = dict(aa)
    return sorted(bb.items(), key=lambda d: d[0]) 

def get_weibo_img_list(text_list):
    weibo_img_list = []
    for text in text_list:
        text = text.replace('[超话]','')
        tmp = re.findall('[[](.*?)[]]', text)
        if len(tmp) >0:
            for chars in tmp:
                if ('图' in chars) or ('顶' in chars) or ('好友圈' in chars) or ('0' in chars) or ('组' in chars) or ('原' in chars) or ('共' in chars) :
                    tmp.remove(chars)
        weibo_img_list.extend(tmp)
    weibo_img_list1 = weibo_img_list
    aa = Counter(weibo_img_list).most_common(3)
    bb = dict(aa)
    return sorted(bb.items(), key=lambda d: d[1]), weibo_img_list1 

def get_theme_list(text_list):
    theme_list = []
    for text in text_list:
        tmp = re.findall('[#《](.*?)[#》]', text)
        if len(tmp) >0:
            theme_list.extend(tmp)
    aa = Counter(theme_list).most_common(5)
    bb = dict(aa)
    return sorted(bb.items(), key=lambda d: d[1])

def get_all_fenci(text_list, weibo_img_list):
    all_texts = ''.join(text_list)
    santi_words = [x for x, flag in pseg.cut(all_texts) if 'n' in flag and len(x)>1 and x not in weibo_img_list and x not in ['全文','原文','原图','好友']]
    aa = Counter(santi_words).most_common(5)
    bb = dict(aa)
    return sorted(bb.items(), key=lambda d: d[1])

def get_pos_neg(text_list):
    positive_texts = []
    negative_texts = []
    for text in text_list:
        text = text.replace('<','')
        text = text.replace(' ','')
        if len(text)>0:
            score1 = SnowNLP(text).sentiments
            score2 = xmnlp.sentiment(text)
            tmp = "".join(jieba.analyse.textrank(text))
            if len(tmp)>0:
                score3 = SnowNLP(tmp).sentiments
                if score1<0.45 and score2<0.45 and score3<0.45:
                    negative_texts.append(text)
                if score1>0.55 and score2>0.55 and score3>0.55:
                    positive_texts.append(text)
            if len(tmp)==0:
                if score1<0.45 and score2<0.45:
                    negative_texts.append(text)
                if score1>0.55 and score2>0.55:
                    positive_texts.append(text)
    return positive_texts, negative_texts


def get_pos_neg_fenci(positive_texts, negative_texts, weibo_img_list):
    negative_texts1 = ''.join(negative_texts)
    santi_words = [x for x, flag in pseg.cut(negative_texts1) if 'n' in flag and len(x)>1 and x not in weibo_img_list and x not in ['全文','原文','原图','好友']]
    negative_fenci = Counter(santi_words).most_common(5)

    positive_texts1 = ''.join(positive_texts)
    santi_words = [x for x, flag in pseg.cut(positive_texts1) if 'n' in flag and len(x)>1 and x not in weibo_img_list and x not in ['全文','原文','原图','好友']]
    positive_fenci = Counter(santi_words).most_common(5)

    return dict(positive_fenci), dict(negative_fenci)




def draw(imageFile, font_path,  save_path,cuts_list,originals_list,reposts_list,time_list,text_list,like_sum,repost_sum,comment_sum,time_dict,weibo_img_list,theme_list,all_fenci,positive_texts,negative_texts,positive_fenci,negative_fenci):
    all_num = len(cuts_list)
    originals_num = len(originals_list)
    reposts_num = len(reposts_list)
    positive_num = len(positive_texts)
    negative_num = len(negative_texts)
    line1 = '总共抓取了共' + str(all_num) +'篇微博，其中：'
    line2 = '原创微博共' + str(originals_num) + '篇，转发微博共' + str(reposts_num) + '篇'
    line3 = '偏积极情感的微博共' + str(positive_num)+ '篇，偏消极情感的微博共' + str(negative_num) + '篇'
    line4 = '所有抓取的微博中最常使用的关键词：'
    line5 = ''
    for i in range(len(all_fenci)):
        a = '「' + all_fenci[-(i+1)][0] + '」，使用了' + str(all_fenci[-(i+1)][1])+ '次；'
        line5 += a
    line6 = '所有偏积极情感的的微博中最常使用的关键词：'
    line7 = ''
    fenci = sorted(positive_fenci.items(), key=lambda d: d[1]) 
    for i in range(len(fenci)):
        a = '「' + fenci[-(i+1)][0] + '」，使用了' + str(fenci[-(i+1)][1])+ '次；'
        line7 += a
    line8 = '所有偏消极情感的的微博中最常使用的关键词：'
    line9 = ''
    fenci = sorted(negative_fenci.items(), key=lambda d: d[1]) 
    for i in range(len(fenci)):
        a = '「' + fenci[-(i+1)][0] + '」，使用了' + str(fenci[-(i+1)][1])+ '次；'
        line9 += a
    line10  = '获得的总赞数：' + str(like_sum)
    line11  = '获得的总评论数：' + str(comment_sum)
    line12  = '获得的总转发数：' + str(repost_sum)
    line13 = '各个小时段发博次数统计：'
    line14 = ''
    for i in range(len(time_dict)):
        a = '「' + time_dict[i][0] + '点，' + str(time_dict[i][1])+ '次」 '
        line14 += a
    line15 = '最爱使用的表情：'
    line16 = ''
    for i in range(len(weibo_img_list)):
        a = '「' + weibo_img_list[-(i+1)][0] + '」，使用了' + str(weibo_img_list[-(i+1)][1])+ '次；'
        line16 += a
    line17 = '最爱使用的话题：'
    line18 = ''
    for i in range(len(theme_list)):
        a = '「' + theme_list [-(i+1)][0] + '」，使用了' + str(theme_list [-(i+1)][1])+ '次；'
        line18 += a

    im1=Image.open(imageFile)
    font1 = ImageFont.truetype(font_path,20)
    font2 = ImageFont.truetype(font_path,15)
    draw = ImageDraw.Draw(im1)
    draw.text((10,30), line1, (255,255,255),font1)
    draw.text((30,60), line2, (255,255,255),font2)
    draw.text((30,90), line3, (255,255,255),font2)
    draw.text((10,130), line4, (255,255,255),font1)

    if len(line5.split('；'))>4:
        draw.text((30,160), line5.split('；')[0] +'   '+ line5.split('；')[1], (255,255,255),font2)
        draw.text((30,190), line5.split('；')[2] +'   '+ line5.split('；')[3], (255,255,255),font2)
    else:
        draw.text((30,190), '暂无记录', (255,255,255),font2) 

    draw.text((10,230), line6, (255,255,255),font1)
    if len(line7.split('；'))>2:
        draw.text((30,260), line7.split('；')[0] +'   '+ line7.split('；')[1], (255,255,255),font2)
    else:
        draw.text((30,260), '暂无记录', (255,255,255),font2)   
    draw.text((10,300), line8, (255,255,255),font1)
    if len(line9.split('；'))>2:
        draw.text((30,330), line9.split('；')[0] +'   '+ line9.split('；')[1], (255,255,255),font2)
    else:
        draw.text((30,330), '暂无记录', (255,255,255),font2)   
    draw.text((10,370), line10, (255,255,255),font1)
    draw.text((10,400), line11, (255,255,255),font1)
    draw.text((10,430), line12, (255,255,255),font1)
    draw.text((10,470), line15, (255,255,255),font1)
    if len(line16.split('；'))>2:
        draw.text((30,500), line16.split('；')[0] +'   '+ line16.split('；')[1], (255,255,255),font2)
    else:
        draw.text((30,500), '暂无记录', (255,255,255),font2)
    draw.text((10,540), line17, (255,255,255),font1)
    if len(line18.split('；'))>2:
        draw.text((30,570), line18.split('；')[0] +'   '+ line18.split('；')[1], (255,255,255),font2)
    else:
        draw.text((30,570), '暂无记录', (255,255,255),font2) 
    draw.text((10,610), line13, (255,255,255),font1)
    list1 = line14.strip().split(' ')
    num = len(list1)
    a = int(num/3)
    b = num%3
    for  i in range(a):
        line = list1[3*i] + list1[3*i + 1] + list1[3*i + 2]
        draw.text((30,640 + 30*i), line, (255,255,255),font2)
        line = ''

    line = ''
    if b >0:
        for j in range(b):
            line += list1[a + j]
            draw.text((30,640 + 30*a), line, (255,255,255),font2)

    draw = ImageDraw.Draw(im1)
    im1.save(save_path)



'''
###################################################################
#部署在服务器上时
@route('/get_result', method = "GET")
def run_main():
    UID = request.query.UID
    cookies = getcookies("ALF=1550821879; _T_WM=4c2f3e8c076f9f926e3ef81d9cb858a1; SUB=_2A25xTG6pDeRhGeVP7FAW9SfIwz6IHXVSz3LhrDV6PUJbkdAKLUfQkW1NTMphbxdDZuic22v2rgYoPlIeOzgqpuuC; SUHB=0mxUd2B8Gc5wHh; SCF=AuPUzKuknrcU0sL50BA5J9O9pUppy_FfKhXYCqspn0W0M17n71A7DMjdCe-c3juACulPh9CVz5SFTNWAW93Kvyo.; SSOLoginState=1548230393")
    pages_count = get_pages_num(UID, cookies)
    cuts_list = get_cuts_list(pages_count, UID, cookies)
    originals_list, reposts_list, time_list, text_list, like_sum, repost_sum, comment_sum = get_feats(cuts_list)
    time_dict = handle_time(time_list)
    text_list1 = handle_text(text_list)
    weibo_img_list, weibo_img_list1 = get_weibo_img_list(text_list1)
    theme_list = get_theme_list(text_list1)
    all_fenci = get_all_fenci(text_list1, weibo_img_list1)
    positive_texts, negative_texts = get_pos_neg(text_list1)
    positive_fenci, negative_fenci = get_pos_neg_fenci(positive_texts, negative_texts, weibo_img_list1)
    imageFile = '/home/zdd/weibo/bg4.jpg'
    font_path = '/home/zdd/weibo/font.ttf'
    save_path = '/home/zdd/weibo/result/' + str(UID) + '.jpg'
    draw(imageFile, font_path,  save_path,cuts_list,originals_list,reposts_list,time_list,text_list,like_sum,repost_sum,comment_sum,time_dict,weibo_img_list,theme_list,all_fenci,positive_texts,negative_texts,positive_fenci,negative_fenci)
    data1 = {'img': open(save_path,'rb')}
    data2 = {'name':str(UID)}
    r = requests.post('http://120.27.27.42:8889/save_img', files=data1, data = data2)
    redirect(r.text)
    #webbrowser.open_new(url)

#######################################################################
run(host='0.0.0.0', port=8887, debug=True)
'''

######################################################################
def test_main(UID, original_cookies, bg_path, font_path, save_path):
	cookies = getcookies(original_cookies)
    pages_count = get_pages_num(UID, cookies)
    cuts_list = get_cuts_list(pages_count, UID, cookies)
    originals_list, reposts_list, time_list, text_list, like_sum, repost_sum, comment_sum = get_feats(cuts_list)
    time_dict = handle_time(time_list)
    text_list1 = handle_text(text_list)
    weibo_img_list, weibo_img_list1 = get_weibo_img_list(text_list1)
    theme_list = get_theme_list(text_list1)
    all_fenci = get_all_fenci(text_list1, weibo_img_list1)
    positive_texts, negative_texts = get_pos_neg(text_list1)
    positive_fenci, negative_fenci = get_pos_neg_fenci(positive_texts, negative_texts, weibo_img_list1)
    imageFile = bg_path
    font_path = font_path
    save_path = save_path
    draw(imageFile, font_path,  save_path,cuts_list,originals_list,reposts_list,time_list,text_list,like_sum,repost_sum,comment_sum,time_dict,weibo_img_list,theme_list,all_fenci,positive_texts,negative_texts,positive_fenci,negative_fenci)

if __name__ == '__main__':
	UID =
	original_cookies = 
	bg_path = 
	font_path = 
	save_path = 
	test_main(UID, original_cookies, bg_path, font_path, save_path)















