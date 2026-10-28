from pathlib import Path
import math, re, html, subprocess
import numpy as np
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle

ROOT = Path('/home/zzy/study/cs224n')
WORK = ROOT/'tmp/pdfs/lecture4-guide'
ASSETS = WORK/'assets'
OUT = ROOT/'output/pdf/lecture4-visual-guide-zh.pdf'
SRC = ROOT/'slides/cs224n-spr2024-lecture04-dep-parsing.pdf'
ASSETS.mkdir(parents=True, exist_ok=True)
OUT.parent.mkdir(parents=True, exist_ok=True)

pdfmetrics.registerFont(TTFont('Latin', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('LatinB', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Mono', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'))
pdfmetrics.registerFont(TTFont('CN', '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf'))
pdfmetrics.registerFontFamily('Latin', normal='Latin', bold='LatinB', italic='Latin', boldItalic='LatinB')

W,H = 595.276,841.89
M=44
CW=W-2*M
NAVY=colors.HexColor('#173348')
TEAL=colors.HexColor('#007F86')
ORANGE=colors.HexColor('#C97621')
RED=colors.HexColor('#BC514C')
BLUE=colors.HexColor('#3A6DB2')
MUTED=colors.HexColor('#637789')
LIGHT=colors.HexColor('#EEF5F7')
LINE=colors.HexColor('#D5E1E7')
INK=colors.HexColor('#243C4D')
WHITE=colors.white

def mark(s):
    s=html.escape(str(s), quote=False)
    s=re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',s)
    return re.sub(r'([\u2e80-\uffef]+)',r'<font name="CN">\1</font>',s).replace('\n','<br/>')

def par(text,size=10.5,leading=17,color=INK,align=TA_LEFT,bold=False):
    return Paragraph(mark(text),ParagraphStyle('x',fontName='LatinB' if bold else 'Latin',fontSize=size,leading=leading,textColor=color,wordWrap='CJK',alignment=align,spaceAfter=0))

def label(c,text,x,y,w,size=10,color=INK,align=TA_CENTER,bold=False):
    p=par(text,size,size*1.42,color,align,bold)
    _,hh=p.wrap(w,1000)
    p.drawOn(c,x,y-hh)
    return hh

def box(c,x,y,w,h,text='',fill=LIGHT,stroke=LINE,size=10,color=INK):
    c.setFillColor(fill);c.setStrokeColor(stroke);c.setLineWidth(.7)
    c.roundRect(x,y,w,h,7,fill=1,stroke=1)
    if text:
        p=par(text,size,size*1.42,color,TA_CENTER)
        _,hh=p.wrap(w-12,h)
        p.drawOn(c,x+6,y+(h-hh)/2)

def arrow(c,x1,y1,x2,y2,color=TEAL,width=1.4,head=5):
    c.setStrokeColor(color);c.setFillColor(color);c.setLineWidth(width)
    c.line(x1,y1,x2,y2)
    a=math.atan2(y2-y1,x2-x1)
    p=c.beginPath();p.moveTo(x2,y2)
    p.lineTo(x2-head*math.cos(a-.5),y2-head*math.sin(a-.5))
    p.lineTo(x2-head*math.cos(a+.5),y2-head*math.sin(a+.5));p.close()
    c.drawPath(p,fill=1,stroke=0)

def curve(c,x1,x2,y,rise,color=TEAL,width=1.5):
    c.setStrokeColor(color);c.setLineWidth(width)
    p=c.beginPath();p.moveTo(x1,y);p.curveTo(x1,y+rise,x2,y+rise,x2,y)
    c.drawPath(p)
    arrow(c,x2,y+5,x2,y,color,width,5)

def dep(c,x,y,w,h,words,edges):
    xs=np.linspace(x+22,x+w-22,len(words))
    base=y+28
    for i,word in enumerate(words):
        label(c,word,xs[i]-30,base-5,60,10.5)
        label(c,str(i),xs[i]-20,y+8,40,8,MUTED)
    for a,b,col in edges:
        curve(c,xs[a],xs[b],base+2,22+abs(a-b)*18,col)

def twin_struct(c,x,y,w,h):
    mid=x+w/2
    label(c,'短语结构：增加短语类别节点',x+8,y+h-12,w/2-16,11,TEAL)
    label(c,'依存结构：词直接连接到词',mid+8,y+h-12,w/2-16,11,BLUE)
    a=x+20;b=mid+20
    pos={'S':(a+104,y+h-62),'NP':(a+65,y+h-108),'VP':(a+174,y+h-108),'The':(a+15,y+43),'cuddly':(a+78,y+43),'cat':(a+132,y+43),'sleeps':(a+193,y+43)}
    for u,v in [('S','NP'),('S','VP'),('NP','The'),('NP','cuddly'),('NP','cat'),('VP','sleeps')]:
        c.setStrokeColor(LINE);c.line(*pos[u],*pos[v])
    for k,(xx,yy) in pos.items():
        box(c,xx-24,yy-11,48,24,k,WHITE,LINE,9)
    p2={'sleeps':(b+104,y+h-62),'cat':(b+104,y+h-119),'The':(b+43,y+43),'cuddly':(b+164,y+43)}
    for u,v in [('sleeps','cat'),('cat','The'),('cat','cuddly')]:
        xx,yy=p2[u];xx2,yy2=p2[v];arrow(c,xx,yy-13,xx2,yy2+14,BLUE)
    for k,(xx,yy) in p2.items():box(c,xx-29,yy-12,58,26,k,WHITE,LINE,9)

def basic_dep(c,x,y,w,h):
    dep(c,x+14,y+12,w-28,h-20,['ROOT','I','ate','fish'],[(0,2,TEAL),(2,1,BLUE),(2,3,ORANGE)])
    xs=np.linspace(x+36,x+w-36,4)
    label(c,'root',(xs[0]+xs[2])/2-30,y+102,60,9,TEAL)
    label(c,'nsubj',(xs[1]+xs[2])/2-35,y+62,70,9,BLUE)
    label(c,'obj',(xs[2]+xs[3])/2-32,y+84,65,9,ORANGE)

def projectivity(c,x,y,w,h):
    half=w/2
    label(c,'投射：可以嵌套，不发生交叉',x+5,y+h-12,half-10,10.5,TEAL)
    label(c,'非投射：仍然是树，但有交叉',x+half+5,y+h-12,half-10,10.5,ORANGE)
    dep(c,x+6,y+18,half-12,h-45,['R','1','2','3','4'],[(0,1,MUTED),(1,2,MUTED),(1,3,TEAL),(3,4,BLUE)])
    dep(c,x+half+6,y+18,half-12,h-45,['R','1','2','3','4'],[(0,1,MUTED),(1,2,MUTED),(1,3,TEAL),(2,4,ORANGE)])

def state_board(c,x,y,w,h):
    steps=[('初始',['ROOT'],['I','ate','fish'],'无'),('1  Shift',['ROOT','I'],['ate','fish'],'无'),('2  Shift',['ROOT','I','ate'],['fish'],'无'),('3  Left-Arc',['ROOT','ate'],['fish'],'ate → I / nsubj'),('4  Shift',['ROOT','ate','fish'],[],'无'),('5  Right-Arc',['ROOT','ate'],[],'ate → fish / obj'),('6  Right-Arc',['ROOT'],[],'ROOT → ate / root')]
    label(c,'动作',x+4,y+h-8,78,9,MUTED)
    label(c,'栈：右端为栈顶',x+86,y+h-8,155,9,MUTED)
    label(c,'缓冲区：左端先读',x+246,y+h-8,125,9,MUTED)
    label(c,'本步新增边',x+375,y+h-8,w-380,9,MUTED)
    rh=(h-40)/7
    for i,(act,stack,buf,edge) in enumerate(steps):
        yy=y+h-35-(i+1)*rh
        if i%2==0:
            c.setFillColor(colors.HexColor('#F7FAFB'));c.rect(x+3,yy+1,w-6,rh-2,fill=1,stroke=0)
        label(c,act,x+5,yy+rh-13,79,8.3,INK)
        for j,t in enumerate(stack):box(c,x+90+j*47,yy+10,43,27,t,WHITE,TEAL,8.3)
        for j,t in enumerate(buf):box(c,x+250+j*40,yy+10,37,27,t,WHITE,ORANGE,8.3)
        if not buf:label(c,'空',x+258,yy+rh-13,80,9,MUTED)
        label(c,edge,x+375,yy+rh-12,w-380,8.2,BLUE if edge!='无' else MUTED)

def sparse_dense(c,x,y,w,h):
    label(c,'精确匹配的组合特征',x+10,y+h-13,w/2-20,11,RED)
    label(c,'共享向量与同一套分类器',x+w/2+10,y+h-13,w/2-20,11,TEAL)
    for k,word in enumerate(['has + good','has + excellent']):
        yy=y+h-68-k*68
        box(c,x+18,yy,w/2-36,35,word,WHITE,LINE,10)
        label(c,'独立组合维度 / 各自积累证据',x+15,yy-6,w/2-30,8.5,MUTED)
        box(c,x+w/2+15,yy,w/2-30,35,word,WHITE,LINE,10)
    arrow(c,x+w*.64,y+52,x+w*.75,y+24,TEAL)
    arrow(c,x+w*.87,y+52,x+w*.75,y+24,TEAL)
    label(c,'相似的表示可通过共享参数泛化',x+w/2+5,y+18,w/2-10,9.5,TEAL)

def vector(c,x,y,vals,cellw=28,cellh=25,fill=LIGHT,fmt=True):
    for i,v in enumerate(vals):
        box(c,x+i*cellw,y,cellw-2,cellh,format(v,'.2f') if fmt and isinstance(v,(int,float)) else str(v),fill,LINE,8)

def lookup(c,x,y,w,h):
    cols=[('词表 E_w','good','[0.2, -0.1, 0.7]',TEAL),('词性表 E_t','JJ','[0.6, 0.3]',BLUE),('标签表 E_r','nsubj','[-0.2, 0.8]',ORANGE)]
    for k,(name,t,vals,col) in enumerate(cols):
        xx=x+10+k*w/3
        label(c,name,xx,y+h-12,w/3-20,11,col)
        for j in range(4):
            fill=colors.HexColor('#DDF0ED') if j==2 else WHITE
            box(c,xx+8,y+h-60-j*30,w/3-36,25,('...','... ',t,'...')[j],fill,LINE,9)
        arrow(c,xx+w/6-10,y+61,xx+w/6-10,y+35,col)
        label(c,vals,xx-3,y+30,w/3-10,9,col)

def concat(c,x,y,w,h):
    segs=[('s1.word',TEAL),('s1.POS',BLUE),('s2.word',TEAL),('b1.word',ORANGE),('child.label',RED)]
    sw=(w-26)/len(segs)
    label(c,'前向：有顺序地拼接，角色由所在区间保留',x+8,y+h-12,w-16,11,INK)
    for i,(t,col) in enumerate(segs):
        xx=x+13+i*sw
        box(c,xx,y+h-95,sw-4,45,t,colors.Color(col.red,col.green,col.blue,alpha=.10),col,8.5)
        arrow(c,xx+sw/2,y+h-104,xx+sw/2,y+63,col)
        box(c,xx,y+26,sw-4,35,'对应梯度切片',WHITE,col,8)
    label(c,'反向：按原边界切分 g_x，传回对应 embedding 行',x+8,y+17,w-16,10,TEAL)

def numeric_forward(c,x,y,w,h):
    entries=[('输入 x','[1, 2, -1]'),('W 与 b1','W = [[1,0,1], [0,1,-1]]\nb1 = [1,-1]'),('z 与 h','z = [1,2]\nh = ReLU(z) = [1,2]'),('U 与 b2','U = [[1,0], [0,1], [-1,0]]\nb2 = [0,0,0]'),('输出 logits','o = [1,2,-1]'),('softmax 概率','p ≈ [0.2595, 0.7054, 0.0351]')]
    bw=(w-40)/2;bh=(h-45)/3
    for i,(tit,txt) in enumerate(entries):
        col=i%2;row=i//2;xx=x+12+col*(bw+16);yy=y+h-18-(row+1)*bh
        box(c,xx,yy,bw,bh-12,'',WHITE,LINE)
        label(c,str(i+1)+'  '+tit,xx+8,yy+bh-23,bw-16,10,TEAL)
        label(c,txt,xx+8,yy+bh-48,bw-16,9,INK)

def backward_flow(c,x,y,w,h):
    names=[('o','g_o = p - q'),('h','g_h = Uᵀ g_o'),('z','g_z = g_h ⊙ 1[z>0]'),('x','g_x = Wᵀ g_z')]
    bw=104;gap=(w-4*bw-24)/3
    for i,(a,b) in enumerate(names):
        xx=x+12+i*(bw+gap)
        box(c,xx,y+37,bw,h-75,a+'\n'+b,WHITE,TEAL,9)
        if i<3:arrow(c,xx+bw+2,y+h/2,x+12+(i+1)*(bw+gap)-3,y+h/2,TEAL)
    label(c,'箭头是梯度传播方向；全部 g 与对应变量同形状',x+8,y+25,w-16,9.5,MUTED)

def beam(c,x,y,w,h):
    cx=x+w/2;top=y+h-23
    box(c,cx-40,top-23,80,29,'初始状态',WHITE,LINE,10)
    p1=[(x+w*.25,top-87,'A：0.6',RED),(x+w*.75,top-87,'B：0.4',TEAL)]
    for xx,yy,t,col in p1:
        arrow(c,cx,top-23,xx,yy+14,col);box(c,xx-46,yy-14,92,28,t,WHITE,col,10)
    leaves=[(x+w*.12,'A1：0.5','0.30',RED),(x+w*.38,'A2：0.5','0.30',RED),(x+w*.63,'B1：0.9','0.36',TEAL),(x+w*.88,'B2：0.1','0.04',TEAL)]
    ly=y+65
    for i,(xx,t,score,col) in enumerate(leaves):
        px=p1[0 if i<2 else 1][0]
        arrow(c,px,top-101,xx,ly+16,col)
        box(c,xx-43,ly-15,86,31,t,WHITE,col,9)
        label(c,'整条路径 '+score,xx-52,ly-24,104,9,col)
    label(c,'贪心先选 A；保留 A、B 后，B1 的完整概率最高',x+8,y+18,w-16,10,INK)

def contextual(c,x,y,w,h):
    texts=['The river overflowed its bank.','She deposited cash at the bank.']
    for k,t in enumerate(texts):
        yy=y+h-70-k*112
        box(c,x+12,yy,w*.49,48,t,WHITE,LINE,10)
        box(c,x+w*.53,yy,78,48,'同一个\nEncoder',WHITE,TEAL,9)
        arrow(c,x+w*.49+17,yy+24,x+w*.53-3,yy+24,TEAL)
        arrow(c,x+w*.53+81,yy+24,x+w-93,yy+24,TEAL)
        box(c,x+w-90,yy,78,48,'h_bank¹' if k==0 else 'h_bank²',WHITE,BLUE if k==0 else ORANGE,10)
    label(c,'查表时 E[bank] 相同；上下文编码后的两个向量可以不同',x+8,y+20,w-16,10,TEAL)

def result_bars(c,x,y,w,h):
    rows=[('MaltParser',89.8,87.2,469),('MSTParser',91.4,88.1,10),('TurboParser',92.3,89.6,8),('C&M 2014',92.0,89.7,654)]
    label(c,'吞吐量：句 / 秒（同一张课件比较表）',x+8,y+h-10,w-16,11,INK)
    for i,(name,uas,las,speed) in enumerate(rows):
        yy=y+h-55-i*37
        label(c,name,x+12,yy+8,112,9,INK,TA_LEFT)
        c.setFillColor(TEAL if i==3 else colors.HexColor('#91ACBE'))
        c.roundRect(x+130,yy-7,(w-195)*speed/654,16,3,fill=1,stroke=0)
        label(c,str(speed),x+135+(w-195)*speed/654,yy+8,44,9,INK)

def prepare_assets():
    crops={8:(.025,.24,.96,.93),14:(.13,.28,.84,.81),16:(.36,.34,.96,.94),21:(.145,.38,.86,.74),25:(.08,.60,.94,.99),38:(.12,.28,.91,.95),39:(.25,.58,.76,.96),40:(.07,.18,.99,.94),44:(.09,.48,.62,.90)}
    for page,bounds in crops.items():
        out=ASSETS/f'original-{page:02}'
        if not out.with_suffix('.png').exists():
            subprocess.run(['pdftoppm','-f',str(page),'-l',str(page),'-scale-to','2200','-png','-singlefile',str(SRC),str(out)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        im=Image.open(out.with_suffix('.png')).convert('RGB')
        a,b,d,e=bounds
        im.crop((int(a*im.width),int(b*im.height),int(d*im.width),int(e*im.height))).save(ASSETS/f'crop-{page:02}.png')

class Book:
    def __init__(self):
        self.c=canvas.Canvas(str(OUT),pagesize=(W,H),pageCompression=1)
        self.c.setTitle('CS224N Lecture 4 中文图解讲义：从句法结构到神经解析')
        self.c.setAuthor('学习讲义 / 基于 Christopher Manning 的 CS224N Spring 2024 Lecture 4')
        self.num=0;self.fnum=0;self.section=None;self.pages=[]
    def page(self,title,section,source,bookmark=False):
        if self.num:self.end()
        self.num+=1;self.y=H-113
        self.pages.append((self.num,title,section,source))
        c=self.c
        c.setFillColor(TEAL);c.rect(0,H-8,W,8,fill=1,stroke=0)
        label(c,'CS224N  /  LECTURE 4',M,H-25,250,8,MUTED,TA_LEFT)
        label(c,section,W-M-210,H-25,210,8,MUTED,2)
        pp=par(title,21,29,NAVY,bold=True);_,hh=pp.wrap(CW,70)
        pp.drawOn(c,M,H-57-hh)
        self.y=H-70-hh
        label(c,source,M,self.y,CW,8.2,MUTED,TA_LEFT)
        self.y-=27
        if bookmark:
            key=f'chapter-{self.num}'
            c.bookmarkPage(key);c.addOutlineEntry(section,key,0)
    def need(self,h):
        if self.y-h<48:raise RuntimeError(f'Page {self.num} overflow: y={self.y:.1f}, need={h:.1f}')
    def p(self,text,size=10.5,leading=17,gap=10,color=INK):
        pp=par(text,size,leading,color);_,hh=pp.wrap(CW,2000)
        self.need(hh+gap);pp.drawOn(self.c,M,self.y-hh);self.y-=hh+gap
    def sub(self,text):
        self.p(text,12,18,8,TEAL)
    def note(self,title,text,color=TEAL):
        pp=par(title+'  '+text,10,16,INK);_,hh=pp.wrap(CW-24,2000);hh+=20
        self.need(hh+11);self.c.setFillColor(LIGHT);self.c.roundRect(M,self.y-hh,CW,hh,6,fill=1,stroke=0)
        self.c.setFillColor(color);self.c.rect(M,self.y-hh,3,hh,fill=1,stroke=0)
        pp.drawOn(self.c,M+12,self.y-hh+10);self.y-=hh+11
    def eq(self,text):
        self.note('公式',text)
    def table(self,heads,rows,widths=None,size=9.1):
        widths=widths or [CW/len(heads)]*len(heads)
        vals=[[par(t,size,14,WHITE if ri==0 else INK,bold=ri==0) for t in row] for ri,row in enumerate([heads]+rows)]
        t=Table(vals,colWidths=widths,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('ROWBACKGROUNDS',(0,1),(-1,-1),[WHITE,LIGHT]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,0),.5,NAVY),('LINEBELOW',(0,1),(-1,-1),.35,LINE)]))
        _,hh=t.wrap(CW,2000);self.need(hh+12);t.drawOn(self.c,M,self.y-hh);self.y-=hh+12
    def fig(self,func,height,guide,caption):
        self.note('读图前',guide)
        self.need(height+38);self.fnum+=1
        self.c.setFillColor(colors.HexColor('#F6FAFB'));self.c.setStrokeColor(LINE)
        self.c.roundRect(M,self.y-height,CW,height,8,fill=1,stroke=1)
        func(self.c,M,self.y-height,CW,height)
        self.y-=height+6
        pp=par(f'图 {self.fnum:02}  '+caption,8.3,12,MUTED);_,hh=pp.wrap(CW,100)
        pp.drawOn(self.c,M,self.y-hh);self.y-=hh+12
    def original(self,page,height,guide,caption):
        path=ASSETS/f'crop-{page:02}.png'
        def draw(c,x,y,w,h):
            im=Image.open(path);iw,ih=im.size
            fac=min((w-16)/iw,(h-12)/ih)
            dw,dh=iw*fac,ih*fac
            c.drawImage(str(path),x+(w-dw)/2,y+(h-dh)/2,dw,dh,mask='auto')
        self.fig(draw,height,guide,f'课件原图局部裁切，PDF p.{page}。'+caption)
    def end(self):
        self.c.setStrokeColor(LINE);self.c.line(M,36,W-M,36)
        label(self.c,'中文图解讲义  ·  原图归原课件作者  ·  页码均为 PDF 页码',M,28,CW-40,7.2,MUTED,TA_LEFT)
        label(self.c,f'{self.num:02}',W-M-30,28,30,8,TEAL,2)
        self.c.showPage()
    def finish(self):
        self.end();self.c.save()
        (WORK/'page-map.txt').write_text('\n'.join(f'{a:02} | {b} | {c} | {d}' for a,b,c,d in self.pages))
        print(f'WROTE {OUT} / {self.num} pages / {self.fnum} figures')

def build():
    prepare_assets()
    b=Book()
    b.page('从词之间的关系\n到可训练的神经解析器','LECTURE 4 中文图解讲义','基于 CS224N Spring 2024 · Christopher Manning · Dependency Parsing',True)
    b.p('这份讲义把原课件的 45 页，整理成可以按顺序自学的中文解释。前半部分建立句法与解析的直觉；后半部分深入 embedding、完整训练链路、搜索和上下文化表示。',12,20,16)
    b.note('阅读约定','所有教学图之前都有“读图前”说明。蓝绿箭头表示中心词指向依存词；其他颜色只用于突出角色，不代表固定的语法标签。')
    b.fig(basic_dep,180,'先找动作 ate，再看箭头从哪里出发、指向谁。ROOT 是虚拟节点；I 与 fish 都直接依存于 ate。边上的词说明关系类别。','自绘。一个句子被转换成带方向、带标签的词间连接。')
    b.p('贯穿全书的问题：如何把一句话转换成一个受约束的结构？我们依次定义输出、构造训练样本、学习表示与评分，再选择合法的结果。')
    b.eq('句子 / 解析状态 → 表示向量 → 动作或边的分数 → 结构选择 → 依存树')
    b.p('评分按“大模型算法学习的可迁移价值”重新校准。高分块要能推导与实现；低分块保留概念，不要求投入同样多的练习时间。',10.5,17,10)
    b.p('制作日期：2026-10-24。原图来自用户提供课件；中文解释、自绘示意与数值例子为本讲义补充。原课件出处与覆盖页码见末页。',8.8,14,8,MUTED)

    b.page('阅读地图：把精力用在真正重要处','阅读导航','沿用原先的 8 个知识块；评分不是课程官方评级')
    b.p('前三块主要定义任务，第四、五块解释传统解析。第六、七块把它变成完整的神经学习问题，第八块连接到搜索、上下文化表示和结构化解码。')
    b.table(['块 / 评分','课件 PDF 页','本讲义页','学习到什么程度'],[
        ['1  句法与歧义 / 4','3-14','3-6','区分两种结构，理解组合与作用范围'],
        ['2  依存定义与树库 / 2','15-23','7-8','读懂 head、标签、ROOT 与监督数据'],
        ['3  约束与投射性 / 2','24-25','9','区别合法树、环和交叉边'],
        ['4  转移解析 / 3','26-30','10-11','走通一个动作序列'],
        ['5  预测与评估 / 4','31-34','12-14','区分评分、搜索、指标与表达范围'],
        ['6  稠密表示 / 7','35-38','15-19','会查表、拼接、算维数和传梯度'],
        ['7  神经动作分类 / 8','39-41','20-25','能实现前向、损失、反传与更新'],
        ['8  搜索与图式解析 / 6','42-45','26-30','掌握上下文化表示和全局结构选择'],
    ],[155,64,65,CW-284],8.9)
    b.sub('两条阅读路线')
    b.p('顺序学习：从第 3 页逐页阅读。核心复习：先回到第 17-25 页，再看第 26-30 页。第 31 页提供自测；第 32 页用于查术语和回看原课件。')
    b.note('和大模型课程的连接','本讲专属的 Arc 动作、投射化和解析标签优先级较低。embedding 的任务训练、logits 与交叉熵、上下文编码、搜索与约束的分工，值得持续保留。')
    b.p('下文“原图”标注指直接取自课件的局部画面；“自绘”标注指为解释而重画的示意。所有实验数字均为课件中的历史比较，不能当作当前模型排名。',9.3,15,8,MUTED)

    b.page('01  同一句话，两种结构视角','第 1 块 · 4/10','对应课件 PDF p.3-6',True)
    b.p('认识每个词，并不等于知道整句话表达什么。还要确定谁做动作、谁被描述、哪些词一起组成单位。课件用短语结构与依存结构，分别表达这些关系。')
    b.fig(twin_struct,222,'左图先看 S、NP、VP：它们是额外的句子或短语类别。右图只看原句中的词：箭头从中心词指向依存词。两图都在分析 The cuddly cat sleeps。','自绘。短语结构强调组成与嵌套；依存结构强调词间直接关系。')
    b.table(['视角','主要回答','节点是什么'],[
        ['短语结构 constituency','哪些词形成一个单位？单位怎样嵌套？','词 + NP、VP 等短语节点'],
        ['依存结构 dependency','哪个词依存于哪个词？关系是什么？','主要是句中每个词实例'],
    ],[125,220,CW-345])
    b.p('NP 是名词短语，VP 是动词短语。普通 CFG 规则可以描述它们的组合，例如 PP → 介词 + NP。这里理解嵌套关系即可，不需要推导 CFG 解析算法。')
    b.note('要避免的误解','语言模型需要处理词间组合关系，不意味着它必须先显式输出一棵句法树。依存解析是把这些关系明确标注出来的一种任务。')

    b.page('相同词序，仍可能有不同附着','第 1 块 · 4/10','对应课件 PDF p.7-9')
    b.p('标题 Scientists count whales from space 的词序已经确定，但 from space 仍有两个连接对象：计数行为 count，或者鲸鱼 whales。前者是借助太空观测计数，后者会被理解为“来自太空的鲸鱼”。')
    b.original(8,210,'先把注意力放在同一句英文的两次出现，再看右侧图片。上图表达观测视角，下面的太空鲸鱼图用夸张方式突出另一种附着。它不是在证明语法不合法，而是在展示语义解读不同。','原图中的对勾与叉表示课件希望采用的新闻解读。')
    b.eq('count whales + from space  /  count + whales from space')
    b.p('距离最近不是决定性规则：from space 紧挨 whales，但这里更合理地描述 count。解析还会利用词的搭配、整句语境与背景知识。')
    b.p('多个修饰语会带来组合增长。课件的收购例句中，of Toronto 描述公司，for $27 a share 描述价格，at its monthly meeting 描述批准的时间；它们不必都接在最近的名词上。')
    b.note('卡特兰数的角色','C_n = (2n)! / [(n+1)! n!] 展示许多树形结构的计数会快速增长。不能据此断言任意含 n 个介词短语的句子恰有 C_n 种合法分析。这里记住候选结构多、需要有效搜索即可。')

    b.page('并列、否定与修饰范围','第 1 块 · 4/10','对应课件 PDF p.10-13')
    b.p('下面四种表面现象，都在追问“哪一段内容与哪一段组合”。先找变化的括号范围，再看它怎样改变事实。它们是帮助理解的例子，不需要逐个背新闻标题。')
    b.table(['现象','两种可能分组','理解差异'],[
        ['并列范围','[veteran and executive] Fred Gregory\n[veteran] and [executive Fred Gregory]','前者可指一人兼有两种身份；后者可指两个人。'],
        ['否定范围','No [heart / cognitive issues]\n[No heart ...], [cognitive issues]','no 覆盖哪些内容，会改变是否存在认知问题的解读。'],
        ['词组边界','[first-hand] [job experience]\nfirst [hand job] experience','作者要表达亲身工作经验；另一种词组切分产生不合原意的读法。'],
        ['不定式附着','beach [to be used for volleyball]\nbody [to be used for volleyball]','用途应描述海滩，误接到遗体就改变了含义。'],
    ],[83,220,CW-303],9.4)
    b.sub('这些例子对模型学习意味着什么')
    b.p('词表中的每个词都认识、词序也已知，仍然可能缺少唯一解释。一个能够理解文本的表示，需要把参与者、修饰对象、并列范围和否定作用范围等关系纳入考虑。')
    b.p('句法提供组合骨架，语义与背景知识帮助选择解释。不能把一句话“词都识别对了”当作“意思也理解对了”，也不能把一棵句法树当作全部语义。')
    b.note('本块的保留项','理解语言的结构化组合，以及两种结构表示即可。具体例句与历史标题的记忆价值很低。')

    b.page('结构能做什么：沿路径找关系','第 1 块 · 4/10','对应课件 PDF p.14')
    b.p('课件以蛋白质相互作用抽取为例：从较长句子中找出哪些实体与关系词 interacts 直接或间接相连。这里的价值是把“读一句话”变成“寻找可解释的结构线索”。')
    b.original(14,276,'从中间的 interacts 开始读。它向左连接主语 KaiC，向右通过 with 关系连接 SasA；KaiA、KaiB 与 SasA 并列。下面三行把这些实体之间的依存路径写了出来。','箭头方向仍为中心词 → 依存词；沿路径阅读时可以逆着箭头走。')
    b.eq('KaiC ←(nsubj) interacts →(nmod:with) SasA')
    b.p('这条路径把两个实体与“相互作用”连接起来，为抽取 KaiC 与 SasA 的关系提供证据。再沿并列边，可以得到涉及 KaiA、KaiB 的候选关系。外围的 reporting clause（如“研究结果表明”）不再遮住核心连接。')
    b.note('适用边界','路径是特征或证据。若句子包含否定、推测、引用等内容，仍要结合这些语境判断是否能抽取肯定事实。句法路径不自动等于事实成立。')

    b.page('02  把句法关系定义成预测目标','第 2 块 · 2/10','对应课件 PDF p.15-20',True)
    b.p('依存关系通常是二元、有方向的词间关系。head 是中心词，dependent 是依存词。本课采用 head → dependent；主语、宾语也可以是 dependent，不只形容词才算修饰或依存成分。')
    b.fig(basic_dep,164,'看 ate 的两条出边：I 是它的主语，fish 是它的宾语。再看 ROOT → ate：虚拟 ROOT 让句子的核心词也有一个中心词。ROOT 不是原句里的词。','自绘。关系类型写在边上；也能转换成下表的逐词监督标签。')
    b.table(['词编号','词','中心词编号','关系标签'],[['1','I','2（ate）','nsubj'],['2','ate','0（ROOT）','root'],['3','fish','2（ate）','obj']],[64,98,170,CW-332])
    b.p('于是输出可以写成：对每个词，预测“中心词的位置 + 关系标签”。不同资料可能反向画箭头，先确认约定即可，词的角色并没有因此变化。')
    b.note('课件中的历史插曲','p.18-19 追溯帕尼尼、阿拉伯语法传统，以及现代依存语法的发展。它说明这种表示早于神经网络；对当前学习目标，只需了解背景。详见末页时间线。')

    b.page('树库：训练答案从哪里来','第 2 块 · 2/10','对应课件 PDF p.21-23')
    b.p('树库将真实句子按统一规范标成句法结构，为模型提供监督，也为模型之间的比较提供共同答案。词性语料、短语结构树库、依存树库并不相同；UD 与本讲的依存标注明确相关。')
    b.original(21,146,'每个小框对应一句话。词上方的类别是词性，弧线及其标签是依存标注。先任选一个词，找指向它的弧，再看弧从哪个词出发。无需逐条辨认这张原图的全部标签。','课件展示 Universal Dependencies 标注实例。')
    b.p('树库的价值包括：同一份标注可以复用，覆盖真实用法，保留频率与分布信息，也能固定评估标准。训练标签的定义和标注一致性，会影响我们究竟在优化与评估什么。')
    b.table(['判断线索','含义与限制'],[
        ['词对亲和性','某些词对更自然，例如 discussion 与 issues。'],
        ['依存距离','近距离连接通常常见，但长距离连接也可能正确。'],
        ['中间的成分','跨越动词、标点等成分会影响候选边的合理性。'],
        ['中心词配价','中心词通常容许哪些类型、数量、方向的依存词。'],
    ],[116,CW-116])
    b.note('区分偏好与约束','上述四项是打分线索，不是绝对规则。“最近的词”不是唯一答案；下一页的无环、单一中心词等才属于结构约束。')

    b.page('03  合法的树，不一定没有交叉','第 3 块 · 2/10','对应课件 PDF p.24-25',True)
    b.p('基本设定：每个真实词恰有一个中心词，ROOT 没有中心词，通常只有一个真实词直接连到 ROOT，并且不允许环。各词独立选最高分中心词，可能选出 A → B → A，因此必须检查整体结构。')
    b.fig(projectivity,180,'R 表示虚拟 ROOT。两图都是无环、连通、每词一个中心词的树。右图只需关注绿色 1 → 3 与橙色 2 → 4：端点按 1、2、3、4 交错，弧线便会交叉。','自绘。交叉是词序布局性质，环是图结构性质，两者不能混淆。')
    b.table(['概念','判断标准'],[['投射 projective','词按原句顺序排列，所有依存弧在同一侧且不交叉。'],['非投射 non-projective','存在交叉依存弧，但仍可能是合法的树。'],['长距离依存','边跨过很多词；它不一定与其他边交叉。']],[135,CW-135])
    b.p('普通、连续 CFG 短语树通过中心词规则转换出的依存结构是投射的；某些成分移位则需要非投射依存边来直接表达。课件的 Who ... from 疑问句用于说明这种情况。')
    b.note('算法能力边界','基础 arc-standard 只生成投射树。若目标结构不在动作系统的表达范围内，改进动作分类器本身无法把它生成出来。')

    b.page('04  四条解析路线与三个状态量','第 4 块 · 3/10','对应课件 PDF p.26-28',True)
    b.p('解析的目标是依存树，寻找它的路线可以不同。神经网络可以为这些路线提供分数，但搜索过程和输出约束仍需单独定义。')
    b.table(['路线','核心做法'],[['动态规划','组合并复用子结构。课件举出 O(n³) 的 Eisner 算法。'],['图算法','为候选边打分，再选择一棵合法的高分树。'],['约束满足','用硬约束排除不可能的边或结构。'],['转移解析','维护当前状态，执行一串动作逐步建树。']],[105,CW-105])
    b.p('转移解析状态记作 (σ, β, A)。σ 是栈，右端是栈顶；β 是缓冲区，左端是下一个词；A 是已经建立的依存边。起点是 σ=[ROOT]，β=[w1,...,wn]，A 为空。')
    b.table(['动作','栈顶为 [..., a, b] 时的效果','新增边'],[['Shift','从缓冲区取首词压入栈顶','无'],['Left-Arc_r','移除左边的依存词 a，保留 b','b → a，标签 r'],['Right-Arc_r','移除右边的依存词 b，保留 a','a → b，标签 r']],[100,270,CW-370])
    b.note('方向怎么记','Left / Right 指新边指向左侧还是右侧依存词。两种 Arc 都保留中心词、移除依存词。ROOT 不能被当作依存词移除。')

    b.page('一张图走完 I ate fish','第 4 块 · 3/10','对应课件 PDF p.29-30')
    b.fig(state_board,414,'每行是执行动作后的状态，从上向下读。绿色边框是栈，橙色边框是缓冲区。第 3 步把 ate 连向左边的 I，第 5 步把 ate 连向右边的 fish；右列只显示本步新增边，旧边仍留在 A 中。','自绘，按课件示范的动作序列重画。')
    b.p('词从栈移除，不代表从句子或结果里消失：它的依存边已经保存在 A 中。留下的中心词继续代表已构造好的局部结构。最终缓冲区为空、栈只剩 ROOT，三条边构成整棵树。')
    b.note('演算不等于预测','课件已经在每步选好了正确动作。真实解析器需要自己决定何时 Shift、何时 Arc。过早移除一个词，可能使后面的正确边再也无法建立。')
    b.p('n 个词需要 n 次 Shift，并通过 n 次 Arc 建边（包括 ROOT 边），所以动作数是 O(n)。线性时间结论还假设每步特征与模型计算成本固定。')

    b.page('05  把状态变成动作分类样本','第 5 块 · 4/10','对应课件 PDF p.31-32',True)
    b.p('训练时，可以由标准依存树构造参考动作序列，得到许多“状态 c → 目标动作 a*”样本。模型把当前状态转成特征 φ(c)，给每个动作打分，再从合法动作中选择。')
    b.eq('score(a,c) = w_aᵀ φ(c) + b_a； a* = argmax_合法动作 score(a,c)')
    b.p('不考虑标签最多有三种动作；若标签集合为 R，共有 1 + 2|R| 个动作类别。当前合法动作通常更少：空缓冲区不能 Shift，栈不足两个元素不能 Arc。合法性与模型偏好是两个判断。')
    b.table(['人工模板示例','对应一维指示特征'],[['栈顶词为 good，词性为 JJ','条件满足为 1，否则为 0。'],['次栈顶为 has/VBZ 且栈顶为 good','精确词组合拥有独立维度。'],['has 的左子节点是 He，边为 nsubj','利用已经构造的结构作为特征。']],[265,CW-265])
    b.p('课件的传统表示可达 10⁶-10⁷ 维，但每个状态只激活少量维度。稀疏向量通常只保存非零项，不意味着每次真的创建并扫描一千万个数。困难也在于人工模板多、具体组合稀少、抽取与查找有成本。')
    b.note('贪心与束搜索','贪心每步只保留一条路径；束搜索保留 k 条较好的部分动作序列，继续扩展后再筛选。前者快，后者探索更多，但有限束宽不保证全局最优。第 26 页给出完整图例。')

    b.page('把 UAS 与 LAS 真正算一遍','第 5 块 · 4/10','对应课件 PDF p.33')
    b.p('评估的基本单位是词的依存边。先比较中心词，再比较边标签。下表复现课件例子 She saw the video lecture；ROOT 的编号是 0。')
    b.table(['词','标准中心词 / 标签','预测中心词 / 标签','UAS','LAS'],[
        ['She','saw / nsubj','saw / nsubj','对','对'],
        ['saw','ROOT / root','ROOT / root','对','对'],
        ['the','lecture / det','video / det','错','错'],
        ['video','lecture / nn','lecture / nsubj','对','错'],
        ['lecture','saw / obj','saw / ccomp','对','错'],
    ],[63,154,154,68,CW-439],9.0)
    b.eq('UAS = 中心词正确数 / 评估词数 = 4/5 = 80%')
    b.eq('LAS = 中心词与标签都正确数 / 评估词数 = 2/5 = 40%')
    b.p('the 的 det 标签虽然对，但连错对象，因此 LAS 不得分。video 与 lecture 连对对象，却标错了关系，只能计入 UAS。由定义可知，同一评估协议下 LAS ≤ UAS。')
    b.note('指标到底在量什么','UAS / LAS 是逐词连接准确率，不是整句树完全正确的比例。比较结果时还要保持相同数据与标点等评估约定；本表按课件五个词计算。')
    b.sub('为什么这一页有迁移价值')
    b.p('预测输出常含多个部分。先明确“什么算对”和计分单位，才知道一个高分说明了什么。训练使用动作交叉熵，而最后报告连接准确率，两者也不是同一个量。')

    b.page('表达范围：分类再准也有做不到的事','第 5 块 · 4/10','对应课件 PDF p.34')
    b.p('基础 arc-standard 无法生成非投射树。这不是某次训练没学好，而是其动作集合与处理顺序限制了可到达的结构。课件给出五种方向：')
    b.table(['方向','改变什么','代价或含义'],[
        ['接受限制','不处理非投射边','可能丢失部分目标连接。'],
        ['改用投射表示','调整目标依存关系的表示','直接输出结构不再与原表示相同。'],
        ['后处理','先投射解析，再识别和修复','多增加一个可能出错的阶段。'],
        ['扩展动作','例如加入 SWAP，改变处理顺序','能力更强，但执行与搜索可能更复杂。'],
        ['换解码机制','如允许非投射树的图式解码','需要为更多候选边评分并选树。'],
    ],[99,190,CW-289])
    b.sub('三个不同的失败来源')
    b.p('评分问题：正确候选存在，但模型给它低分。搜索问题：评分已有帮助，但搜索提前丢弃了好路径。表达范围问题：正确结构根本不在允许的输出集合里。')
    b.note('和后续研究的连接','改网络主要改变评分能力；改搜索主要改变探索；改动作或约束改变可表达的结构。诊断错误时先定位是哪一环，而不是把所有失败都归为“模型不够大”。')
    b.p('SWAP 可以借助“调整处理顺序”的直觉理解。课件类比冒泡排序；当前路线无需推导完整扩展系统，知道它为非投射结构打开可达路径即可。')

    b.page('06  稀疏特征的问题在哪里','第 6 块 · 7/10','对应课件 PDF p.35',True)
    b.p('第 35 页批评的是大量人工、精确匹配的组合特征。把它们换成可学习稠密向量，核心收益来自表示共享与学习组合规律，不只是数字从 0/1 变成浮点数。')
    b.fig(sparse_dense,218,'左右两边使用同样的词组合。左侧把不同字面组合看成独立条件；右侧先取得词向量，再由共享网络处理。相近向量只是可学习的机会，不是自动保证。','自绘。以统计证据共享解释泛化，而非把“维数更低”当作唯一理由。')
    b.table(['课件列出的问题','具体含义'],[['稀疏 sparse','许多精确组合只出现少量次，独立权重缺少证据。'],['不完备 incomplete','人工模板难以预先覆盖所有有用的交互。'],['计算贵 expensive','每步特征抽取、组合、索引等操作可能成为瓶颈。']],[123,CW-123])
    b.p('神经模型仍然需要选择可见槽位。没有提供的上下文，不会仅靠隐藏层凭空出现。稀疏模型也能高效存非零项，因此速度应看完整实现，而非只比较名义维数。')
    b.note('95% 的正确读法','“超过 95% 时间花在特征计算”是课件讨论的传统流程中的统计，不是所有解析器的固定规律。它提示先测量瓶颈，再选择改进方案。')

    b.page('实验表：准确率、速度与证据范围','第 6 块 · 7/10','对应课件 PDF p.36')
    b.table(['解析器','UAS','LAS','句 / 秒'],[['MaltParser','89.8','87.2','469'],['MSTParser','91.4','88.1','10'],['TurboParser','92.3','89.6','8'],['Chen & Manning 2014','92.0','89.7','654']],[235,78,78,CW-391])
    b.fig(result_bars,201,'四条横条只比较最后一列吞吐量，横条从零起。最长条是 C&M 2014；它并不表示 UAS 也最高，准确率必须回到上表分别检查。','自绘，数据直接来自课件历史实验表。')
    b.p('在这组实验中，C&M 的 LAS 和吞吐量最高，但 TurboParser 的 UAS 略高。这支持“取得很好的准确率与速度组合”，不能表述成“所有指标都最好”。')
    b.note('从对比到因果','表格比较的是完整系统，不能分离 embedding、非线性分类器和工程实现各自贡献多少。需要控制其他因素、逐项移除组件的消融实验，才能更有依据地解释改进来源。')
    b.p('阅读大模型论文时也应先问：比较的数据、预算与评估是否一致？结果支持完整方案有效，还是足以支持某个组件的因果解释？这是比记住本表分数更重要的能力。')
    b.page('三张查找表，三类可学习符号','第 6 块 · 7/10','对应课件 PDF p.37')
    b.p('词、词性和依存标签都是离散符号。给每类符号一张参数表，每一行对应一个符号；给定编号，就取出对应行。各表维数可以不同。')
    b.table(['参数表','形状','一次 lookup'],[['词表 E_w','|V| × d_w','good 的编号 → 一行 d_w 维向量'],['词性表 E_t','|P| × d_t','JJ 的编号 → 一行 d_t 维向量'],['标签表 E_r','|R| × d_r','nsubj 的编号 → 一行 d_r 维向量']],[112,125,CW-237])
    b.fig(lookup,224,'三列对应三张独立的表。绿色行表示这次被选中的符号；向下箭头表示取出它的向量。图中的数值仅为教学示意，不是训练得到的真实向量。','自绘。lookup 选择参数，不改变符号编号。')
    b.eq('e_w = E_wᵀ o_w； E_w: |V| × d_w，o_w: |V| × 1，e_w: d_w × 1')
    b.p('o_w 是 one-hot 列向量。乘法只选中一行，因此代码通常直接查表，不构造巨大的 one-hot。被取出的向量属于模型参数，损失梯度能回到表中的对应行；离散编号本身不求导。')
    b.note('相似性怎样产生','课件希望 NN 与 NNS 等相近标签学到相近表示。这是训练可能带来的结构，不是给符号一个随机向量就自动成立。这里也不要求先做 SVD。')

    b.page('从当前解析状态抽取槽位','第 6 块 · 7/10','对应课件 PDF p.38')
    b.p('这个模型并非每步重新读取全部词的任意组合，而是人为选择固定槽位：栈顶、次栈顶、缓冲区首词，以及已建立的若干子节点，再把它们的符号查成向量。')
    b.original(38,296,'先看顶部状态：栈中有 has、good，缓冲区首词是 control；has 已连到主语 He。再看下表：s1 是 good，s2 是 has，b1 是 control；lc(s2) 是 He。空号表示该槽位当前不存在内容。','原图右侧明确写的是 concatenation，即拼接；中间加号不是逐元素相加的指令。')
    b.p('lc / rc 表示已构造依存结构中的左侧 / 右侧子节点。观察它们能让模型知道“哪些连接已经完成”，例如 has 已有主语。词性与已有边标签也一起作为输入。')
    b.note('NULL 的作用','缺失位置也必须保留固定的输入区间。可以给空值定义专门表示，例如 NULL 向量；不能删掉这一段并让后面的槽位向前错位。')
    b.p('网络能够学习所选信息之间的规律，但可见哪些位置仍是设计决定。稠密表示不会凭空补回没有提供的句子上下文。')

    b.page('拼接保留角色，反传切回原位','第 6 块 · 7/10','对应课件 PDF p.37-38；补充形状与梯度解释')
    b.eq('x_c = [e_word(s1); e_POS(s1); e_word(s2); e_word(b1); ...]')
    b.fig(concat,199,'上排不同颜色是不同输入区间，标签指出它来自哪个槽位。分号表示首尾拼接。反向得到 g_x 后，按完全相同的边界切片，再传回各参数表。','自绘。箭头在这里表示梯度切分去向，不是依存边。')
    b.p('为什么不用简单相加？求和会丢掉明确的区间身份；拼接让网络区分“good 位于栈顶”与“good 位于缓冲区”。同一张词表可以共享，但不同槽位的后续权重不同。')
    b.eq('D = K_w d_w + K_t d_t + K_r d_r')
    b.p('K_w、K_t、K_r 是选取的词、词性、标签槽位数。它们固定后，状态向量维数 D 固定，句子变长也不会直接改变这层分类器的输入形状。')
    b.note('重复查表时的梯度','若同一词出现在两个槽位，两段梯度都指向同一参数行，更新前应相加。不同训练样本的贡献也会累积。这和计算图分支处梯度求和是同一原则。')
    b.p('固定词向量与状态向量不要混淆：同一词类型先取到同一向量，但其他槽位的内容改变后，整个 x_c 会改变。这还不是对整句做编码后得到的上下文化词表示。')

    b.page('07  先读懂原课件的完整网络','第 7 块 · 8/10','对应课件 PDF p.39-41',True)
    b.p('网络每运行一次，只预测当前一步的动作。执行动作后，解析状态改变，重新抽取向量，再运行下一次。整棵树来自连续决策，不是图中某一层一次输出全部边。')
    b.original(40,268,'从下往上读：底部把栈与缓冲区的符号查表并拼接成 x；中间隐藏层 h 做非线性重表示；最上方 softmax 输出动作概率。右上角说明损失还能反传到最底部的 embedding。','课件展示 ReLU 版教学架构。本讲义按此公式讲解，不把它当成原论文所有实现细节的逐项复刻。')
    b.eq('z = W x + b1； h = ReLU(z)； o = U h + b2； p = softmax(o)')
    b.table(['量','形状','角色'],[['x','D × 1','拼接输入'],['W，b1，h','H × D；H × 1；H × 1','隐藏层变换'],['U，b2，o，p','C × H；其余 C × 1','C 个动作的分数和概率']],[105,192,CW-297],9)
    b.p('输出 o 是 logits，可正可负；p 是归一化概率。动作类别最多 C=1+2|R|，执行时必须排除当前不合法的动作。')

    b.page('非线性究竟增加了什么','第 7 块 · 8/10','对应课件 PDF p.39-40')
    b.p('如果去掉激活函数，两层仿射变换可以合并：o=U(Wx+b1)+b2=(UW)x+(Ub1+b2)。增加这一层并没有增加对输入 x 的非线性表达能力。')
    b.original(39,188,'左图用一条直线把两类点分开，无法贴合弯曲分布；右图展示更复杂的分类区域。它是在说明表示能力，不是在证明任意更复杂边界都一定泛化更好。','课件的二维分类区域示意。')
    b.eq('ReLU(z_i) = max(0,z_i)； z_i<0 时局部导数为 0，z_i>0 时为 1')
    b.p('加入 ReLU 后，不同输入激活不同隐藏单元，可以把多片线性区域拼成更复杂的动作决策区域。网络能学习输入成分之间的组合规律，减少人工穷举组合模板的需要。')
    b.eq('p_a > p_b ⇔ o_a > o_b；softmax 不改变 logits 的大小顺序')
    b.note('两个精确性修正','softmax 概率是非线性函数，但仿射 logits 的两类决策边界仍是线性的。课件对传统模型的表述应按线性版本理解：核 SVM 或非线性特征映射也能得到非线性边界。')
    b.p('ReLU 在恰好零点不可导，实现通常采用约定值。学习本页时关注“非线性改变表示能力”，不要把非线性和层数简单等同。')

    b.page('用一组小数字跑完整次前向','第 7 块 · 8/10','对应课件 PDF p.40；以下为自拟教学数值')
    b.p('为了能手算，缩小为 D=3、H=2、C=3。三个动作依次记为 Shift、Left-Arc、Right-Arc，并假设这次都合法。下图和后面三页始终使用同一组参数。')
    b.fig(numeric_forward,329,'按从左到右、从上到下的编号顺序读六个框。先算 W x + b1；两个结果都为正，因此 ReLU 保留它们。再算 U h + b2，最后对三个 logits 一起做 softmax。','自绘。向量在框内横写以节省空间，计算时均视为列向量。')
    b.eq('第一隐藏单元：1×1 + 0×2 + 1×(-1) + 1 = 1')
    b.eq('第二隐藏单元：0×1 + 1×2 + (-1)×(-1) - 1 = 2')
    b.p('概率最大的第二类约为 0.7054，贪心推理会选 Left-Arc。但正确动作不由模型自己的最大值定义：训练标签可能是第一类 Shift。下一页据此计算损失。')

    b.page('交叉熵：把正确动作作为监督','第 7 块 · 8/10','对应课件 PDF p.40；延续上一页数值')
    b.p('参考动作来自标注树及动作构造规则，不来自本次预测。令正确动作为第一类 Shift，其 one-hot 标签 q=[1,0,0]ᵀ。')
    b.eq('L = -log p_Shift = -log(0.2595) ≈ 1.3490')
    b.eq('L = -o_Shift + log Σ_j exp(o_j)')
    b.p('正确动作概率越接近 1，损失越接近 0。模型错得很自信时，正确动作概率很低，损失会更高。训练时通常对许多状态的损失求和或平均。')
    b.table(['动作','预测概率 p','目标 q','logit 梯度 p-q'],[['Shift','0.2595','1','-0.7405'],['Left-Arc','0.7054','0','+0.7054'],['Right-Arc','0.0351','0','+0.0351']],[119,120,98,CW-337])
    b.eq('g_o = ∂L/∂o = p - q')
    b.p('从 logits 的梯度方向看，梯度下降会推高正确类分数，压低错误类分数。实际更新的是共享网络参数，不能把它理解为每个 logit 都有一个彼此独立的自由参数。')
    b.note('为什么能得到 p-q','对 -o_Shift 求导，只有正确类得到 -1；对 log-sum-exp 求导，每类得到 p_j。两项相加就是 p_j-q_j。这也是之后语言模型分类输出头中常见的基础公式。')
    b.p('动作交叉熵是可微训练目标；UAS / LAS 是最后结构的评估指标。降低局部分类损失有助于建树，但它们不是同一个量，也没有逐步严格单调的对应关系。')

    b.page('反传：形状与数值同时检查','第 7 块 · 8/10','对应课件 PDF p.40；结合 Lecture 3 的局部规则')
    b.fig(backward_flow,133,'从左到右是反向传播顺序：先拿到输出分数的梯度，再经过 Uᵀ、ReLU 门控和 Wᵀ。每个 g 都与其下标变量同形状；本例两个 z 都为正，门控不会截断梯度。','自绘。矩阵转置来自形状与链式法则，不是随意补上。')
    b.table(['所求梯度','通用公式','本例结果 / 形状'],[
        ['输出层 U','g_o hᵀ','[[-0.7405,-1.4810],\n [0.7054,1.4108],\n [0.0351,0.0702]]；3×2'],
        ['输出偏置 b2','g_o','[-0.7405,0.7054,0.0351]；3×1'],
        ['隐藏层 z','g_z=(Uᵀg_o)⊙1[z>0]','[-0.7756,0.7054]；2×1'],
        ['输入层 W','g_z xᵀ','[[-0.7756,-1.5512,0.7756],\n [0.7054,1.4108,-0.7054]]；2×3'],
        ['隐藏偏置 b1','g_z','[-0.7756,0.7054]；2×1'],
        ['输入 x','Wᵀg_z','[-0.7756,0.7054,-1.4810]；3×1'],
    ],[81,161,CW-242],8.7)
    b.p('输入梯度还要按拼接边界拆分，送回实际查到的参数行。若 x 只是外部固定输入，可以停止；若来自可训练 embedding，训练就继续向这些行传播。')
    b.note('统一约定','本讲义的 g 均采用与变量同形状的梯度。不要把行雅可比写法与列梯度公式混用。所有梯度计算应基于本次前向使用的同一组参数，再执行更新。')

    b.page('一次训练更新，与一次推理的区别','第 7 块 · 8/10','对应课件 PDF p.40-41；补充实现视角')
    b.p('现在可以把算法落到实现。训练目标是“参考状态上的参考动作”，实际解析则要沿自己选出的动作运行。两种流程共享网络，但状态来源与执行目的不同。')
    b.table(['阶段','训练','推理'],[['状态来源','由训练样本及参考动作构造规则提供','由之前实际预测的动作产生'],['网络输出','动作 logits 与概率','动作 logits 与概率'],['下一步','用参考标签计算交叉熵并反传','从合法动作中选择并执行'],['参数变化','优化器更新权重和 embedding','通常只读取参数'],['最终用途','学习可靠的动作评分器','连续动作构成依存树']],[85,211,CW-296],9.2)
    b.sub('最小训练流程')
    b.p('1. 清空本次更新的梯度。\n2. 从状态中查表并拼接 x。\n3. 计算 z、h、o 与交叉熵 L。\n4. 反向得到 U、W、偏置与 embedding 行的梯度。\n5. 按学习率与优化器规则更新参数。')
    b.eq('简单 SGD：θ_new = θ_old - α ∇_θ L')
    b.p('例如某个被查到的三维向量就是本例 x，α=0.1 时，根据 g_x 可得新值约 [1.0776,1.9295,-0.8519]。若它来自多个 embedding 切片，则分别更新对应切片所属行。')
    b.note('无需对动作选择求导','基础局部监督训练直接给定状态和标签，求导路径到交叉熵即可。离散 argmax 与栈操作用于构造或执行状态，并不因此要求对它们做普通反向传播。')
    b.p('第 41 页的经验结论来自稠密表示、非线性分类器及实现的共同作用。到这里应能实现完整分类训练链路；不必先掌握完整解析框架才理解这些数学。')

    b.page('08  为什么局部最好不等于整条最好','第 8 块 · 6/10','对应课件 PDF p.42',True)
    b.p('模型评分、搜索与训练目标可以分别改进。更深的网络改善评分；束搜索保留更多部分解；全局目标让完整动作序列参与学习。先用下图看纯粹的搜索问题。')
    b.fig(beam,247,'每条分支标的是该步条件概率，叶子下方是两步概率的乘积。红色是第一步较高的 A 路径，绿色是第一步稍低的 B 路径。不要把叶子处的 0.9 当作整条路径概率。','自绘。所有叶子概率相加为 1；最佳完整路径是 B1，而贪心先选 A。')
    b.eq('log P(a1,...,aT | x) = Σ_t log p(a_t | c_t)')
    b.p('乘积常改成对数求和，便于累计与比较。束搜索保留 k 条部分序列；每步扩展所有保留序列，再从全部扩展结果中取最好的 k 条。有限 k 仍可能提前删掉好路径。')
    b.note('模型最优与任务正确','搜索优化的是定义好的模型分数。找到更高分的序列，也需要评分器与任务目标足够一致，才能改善真实任务结果。搜索扩大不自动等于答案质量必然提高。')

    b.page('局部目标、全局目标与搜索分工','第 8 块 · 6/10','对应课件 PDF p.42')
    b.p('局部分类模型在每个参考状态计算动作交叉熵。课件提到 CRF 风格的全局处理，把完整动作序列的得分纳入比较；下面是其思想的抽象写法，不是完整算法推导。')
    b.eq('P(a | x) = exp S(a,x) / Σ_(a′ 为合法完整序列) exp S(a′,x)')
    b.p('S(a,x) 是整条序列得分。分母涉及其他合法序列，因此训练与推断都可能需要更复杂的搜索或近似。它和“保留 k 条路径”属于不同层面。')
    b.table(['改进项','改变什么','仍不能单独保证什么'],[['更强网络','动作或状态的评分能力','搜索不会提前丢弃好路径'],['束搜索','探索并保留哪些部分序列','评分一定符合真实任务质量'],['全局训练','完整序列之间的学习目标','解码一定能精确找到最优序列']],[100,201,CW-301])
    b.table(['课件历史结果','UAS','LAS'],[['Chen & Manning 2014','92.0','89.7'],['Weiss 等 2015','93.99','92.05'],['Andor 等 2016','94.61','92.79']],[281,112,CW-393])
    b.p('课件介绍这条发展路线带来了 SyntaxNet 等系统。表中是指定 PTB WSJ / Stanford Dependencies 设置下的历史比较，不能将当时的“最准确”宣传语沿用为当前事实。')
    b.note('优先级','掌握“打分、搜索、训练目标可以分别设计”即可。当前无需深入完整 CRF 分区函数计算；后续需要做结构化序列学习时再展开。')

    b.page('图式解析：先打边分，再选整棵树','第 8 块 · 6/10','对应课件 PDF p.43-44')
    b.p('转移解析预测动作。图式解析直接为候选中心词 i 与依存词 j 计算 s(i→j)。边分数不必是概率；单独最高分的边，也不保证与其他高分边组成合法树。')
    b.original(44,190,'图中只在为 big 选择中心词。箭头都指向 big，起点是候选中心词；cat → big 得 2.0，局部最高。其他词也各有一组候选边，原图只是其中一列分数。','不要把“这个词局部选 cat”误读为已经求出整句话的最优树。')
    b.eq('T* = argmax_(T ∈ 合法树集合) Σ_(i→j ∈ T) s(i→j)')
    b.p('为什么不能逐词取最大值？若 A 的最高分中心词是 B，而 B 的最高分中心词是 A，就会得到 A ↔ B 的环。树解码要同时满足根、单一中心词、无环等约束，再优化总分。')
    b.note('MST 的准确理解','这里讨论的是有向、有根的生成树。若边用“分数越高越好”表示，目标是最大权；取负后也可写成最小代价。允许非投射树的解码不会额外禁止交叉边。')
    b.p('n 个真实词每个都有约 n 个候选中心词（含 ROOT、排除自己），候选边量级为 O(n²)；最终只选 n 条入边。候选分数的计算与合法树的选择是两项不同工作。')

    b.page('上下文化表示：这部分最值得保留','第 8 块 · 6/10','对应课件 PDF p.43-45；概念单独优先级较高')
    b.eq('静态查表：e_i = E[w_i]；上下文编码：h_i = Encoder(e_1,...,e_n)_i')
    b.fig(contextual,261,'两句都含 bank，先查到同一张表里的同一行。随后用同一个编码器分别处理两句；它可以利用 river 与 deposited 等上下文，让两个位置得到不同的 h_bank。图中没有给具体向量数值，避免把示意当作实测。','自绘。前句是河岸语境，后句是银行语境；编码器参数共享，但输入上下文不同。')
    b.p('图式解析需要的不只是“两个词通常有什么关系”，还包括“这两个位置在当前句子里承担什么作用”。因此先得到每个词实例的 h_i，再对候选 h_i、h_j 打分。')
    b.p('同一个词在同一句不同位置，也可以有不同的上下文化向量。它与前面把若干静态词向量拼成状态表示不同：这里每个位置的向量本身已经融合了其他位置的信息。')
    b.note('联系后续课程','序列模型与 Attention 等机制会继续回答“怎样把上下文融进位置表示”。这不意味着某一维必须显式代表主语或宾语，也不意味着必须先生成句法树。')

    b.page('双仿射打分与两条路线的边界','第 8 块 · 6/10','对应课件 PDF p.45；公式为通用概念补充')
    b.p('Dozat 与 Manning 的图式神经解析器使用双仿射打分。先把候选中心词与依存词表示成向量 u、v，下面是一种常见的标量形式，用来理解各项的作用。')
    b.eq('s(u,v) = uᵀ B v + aᵀu + bᵀv + c')
    b.p('uᵀBv 学习两者之间的兼容性；线性项与偏置补充单侧倾向。中心词与依存词角色不同，打分不要求交换 u、v 后保持不变。此公式帮助理解名称，不代表课件逐项给出了该实现。')
    b.table(['','转移解析','图式解析'],[['局部评分对象','当前状态下的动作','候选中心词 → 依存词'],['结构形成','沿动作序列逐步执行','对候选边评分后做树解码'],['基础规模','O(n) 个动作','O(n²) 个候选连接'],['非投射性','基础 arc-standard 不支持','相应图解码可以允许'],['关键表示','选定解析状态槽位','每个词实例的上下文表示']],[81,211,CW-292],9)
    b.p('课件报告 Dozat & Manning 2017 的 UAS 为 95.74、LAS 为 94.08，高于所列的早期模型，同时比简单神经转移解析器慢。速度还受编码器、解码和实现影响，不能仅凭阶数断言所有实现的墙钟时间。')
    b.note('真正的保留项','会区分表示、局部打分与整体合法结构选择；理解静态词向量与上下文化表示。MST 的内部步骤与双仿射解析器的专项实现，按后续研究需求再深入。')

    b.page('自测：能解释与能实现分开检查','学习检验','先遮住右列回答；答案是检查要点，不要求逐字背诵')
    b.table(['自测问题','答案要点'],[
        ['1. 词序已知，为何仍可能有歧义？','短语可能附着到不同对象，或存在不同并列、否定范围。'],
        ['2. 一棵树有交叉边就非法吗？','不一定。合法树与投射性是两层约束；交叉不等于环。'],
        ['3. [..., a, b] 做 Left-Arc 后怎样变？','建立 b → a，移除依存词 a，保留 b。'],
        ['4. 标签正确但中心词错误，LAS 得分吗？','不得分。LAS 要求两者都正确；它也不是整句完全正确率。'],
        ['5. 如何计算拼接向量维数？','对每类槽位数量 × 对应向量维数求和；NULL 槽位仍占位置。'],
        ['6. 为什么 embedding 会收到梯度？','输入梯度按拼接边界切片，回到被查到的参数行；重复行贡献求和。'],
        ['7. softmax 会改变动作分数排序吗？','不会。p_a>p_b 等价于 o_a>o_b；非线性特征能力来自隐藏层等变换。'],
        ['8. 为什么逐词选择最高分 head 不够？','局部选择可能形成环或违反根约束，需要整体树解码。'],
    ],[238,CW-238],9.2)
    b.sub('建议完成的一个小练习')
    b.p('用本讲义第 22 页的固定参数，实现一次前向与交叉熵；检查概率和为 1，损失约为 1.3490。再计算第 24 页的梯度，确认所有梯度与对应参数同形状。')
    b.p('随后把 x 换成几行 embedding 的拼接，检查未被查到的行本次梯度为零，重复使用的行梯度会相加。这个练习比反复手算复杂句的 Arc 动作更贴近你后续的学习目标。')

    b.page('覆盖索引、术语与原课件出处','参考与校准','PDF 页码与幻灯片页内编号不同；下表统一使用 PDF 页码')
    b.table(['原 PDF 页','覆盖内容','本讲义页'],[['1-2','标题与课程安排；学习主题在封面说明','1-2'],['3-14','结构、各类歧义、关系抽取路径','3-6'],['15-23','head / 标签 / ROOT、历史、树库、线索','7-8'],['24-25','树约束、投射性、CFG 联系','9'],['26-30','四类方法、转移状态与演算','10-11'],['31-34','分类特征、束搜索、UAS/LAS、非投射处理','12-14'],['35-38','稠密表示、实验、三张表、槽位拼接','15-19'],['39-41','非线性、完整网络、训练与结果含义','20-25'],['42-45','后续搜索、全局目标、上下文、图式与双仿射','26-30']],[83,351,CW-434],8.6)
    b.p('术语：head 中心词；dependent 依存词；configuration 解析状态；treebank 树库；attachment 附着 / 连接；projectivity 投射性；logit 未归一化分数；contextual representation 上下文化表示。',9.2,15,9)
    b.p('历史背景（课件 p.18-19）：依存思想追溯至帕尼尼与阿拉伯语法传统；现代工作提到 Tesnière（1959）与 Hays（1962）。短语结构历史提到 Wells（1947）和 Chomsky（1953）。手稿图来自后世实物，不是公元前原稿；这些内容作背景了解。',9.0,14,9)
    b.p('原课件：Christopher Manning，Stanford CS224N / Ling284，Spring 2024，Lecture 4: Dependency Parsing。源文件：cs224n-spr2024-lecture04-dep-parsing.pdf。原图局部均在图注标出 PDF 页码；自绘图和数值例子已明确标注。',8.7,14,8,MUTED)
    b.note('解释校准','关系箭头统一 head → dependent；梯度统一采用与变量同形状的约定。softmax 分类边界的说明限定给定特征空间中的线性模型；实验速度和排名仅按课件历史设置解读。')
    b.finish()

if __name__=='__main__':build()
