from pathlib import Path
import html,xml.etree.ElementTree as ET
import markdown,pypdfium2 as pdfium
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
out=Path('docs/PED/exports/PED_v3.0-review.pdf')
if Path('C:/Windows/Fonts/arial.ttf').exists():
 pdfmetrics.registerFont(TTFont('Body','C:/Windows/Fonts/arial.ttf'));pdfmetrics.registerFont(TTFont('Body-Bold','C:/Windows/Fonts/arialbd.ttf'))
else:
 from reportlab.pdfbase.pdfmetrics import Font
 pdfmetrics.registerFont(Font('Body','Helvetica','WinAnsiEncoding'));pdfmetrics.registerFont(Font('Body-Bold','Helvetica-Bold','WinAnsiEncoding'))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Body-Bold',italic='Body',boldItalic='Body-Bold')
styles=getSampleStyleSheet()
for n in ['Normal','BodyText','Heading1','Heading2','Heading3','Title']:
 styles[n].fontName='Body-Bold' if n in ['Heading1','Heading2','Heading3','Title'] else 'Body'
styles['BodyText'].fontSize=9.5;styles['BodyText'].leading=12.5;styles['BodyText'].spaceAfter=7
styles['Heading1'].fontSize=17;styles['Heading1'].leading=22;styles['Heading1'].textColor=colors.HexColor('#123b4a')
styles['Heading2'].fontSize=12.5;styles['Heading2'].leading=16;styles['Heading2'].spaceBefore=12;styles['Heading2'].spaceAfter=7;styles['Heading2'].textColor=colors.HexColor('#123b4a')
styles.add(ParagraphStyle(name='Cell',fontName='Body',fontSize=8.1,leading=10,spaceAfter=0,splitLongWords=True))
styles.add(ParagraphStyle(name='TableHead',fontName='Body-Bold',fontSize=8.1,leading=10,textColor=colors.white))
def norm(s):
 return s.replace('→',' -&gt; ').replace('×',' x ').replace('–','-').replace('—','-').replace('≤','&lt;=').replace('≥','&gt;=')
def inline(el):
 s=html.escape(el.text or '')
 for ch in el:
  tag={'strong':'b','em':'i','code':'font'}.get(ch.tag,ch.tag)
  attrs=' face="Courier" size="7.6"' if ch.tag=='code' else (' href="'+html.escape(ch.get('href',''),quote=True)+'" color="#125f78"' if ch.tag=='a' else '')
  s+=('<br/>' if ch.tag=='br' else '<'+tag+attrs+'>'+inline(ch)+'</'+tag+'>')+html.escape(ch.tail or '')
 return norm(s)
story=[]
for text,style in [('CivicConnect','Title'),('Project Engineering Document v3.0','Heading1'),('Construction, verification and release evidence index','BodyText')]:story.append(Paragraph(text,styles[style]))
for text in ['<b>MERGED - 17 OCTOBER 2026 (commit c7e92de8f818b66ca1ecc0faf88b0987c4b17b40)</b><br/>M3 evaluation-slice status: APPROVED by Don and Masego, merged to main. Release decision: NOT READY for final baseline/public production release - these are separate questions; see the residual-risk table.<br/>Prepared for Emile, Don and Masego.','This continues the repository PED: M1 sections 01-15 and M2 sections 16/17/19/20/21 remain the historical sources. This export indexes those sources and adds section 22; historical sign-offs retain their original scope.','Candidate evidence: 60 automated tests passed; two live HTTP journeys; p95 0.422 seconds over five minutes with 10 users/500 requests; local restart and backup/restore passed. Evidence boundaries and remaining gaps follow.']:
 story.append(Paragraph(text,styles['BodyText']))
story.append(Spacer(1,10))
root=ET.fromstring('<root>'+markdown.markdown(Path('docs/PED/22-m3-construction-verification-release.md').read_text(encoding='utf8'),extensions=['tables'])+'</root>')
width=A4[0]-84
for el in root:
 if el.tag in ['h1','h2','h3']:
  if (el.text or '').startswith(('22.3 ','22.5 ')):story.append(PageBreak())
  story.append(Paragraph(inline(el),styles[{'h1':'Heading1','h2':'Heading2','h3':'Heading3'}[el.tag]]))
 elif el.tag=='p':story.append(Paragraph(inline(el),styles['BodyText']))
 elif el.tag in ('ol','ul'):
  for i,item in enumerate(el):story.append(Paragraph((str(i+1)+'. ' if el.tag=='ol' else '- ')+inline(item),styles['BodyText']))
 elif el.tag=='table':
  rows=[[Paragraph(inline(td),styles['TableHead'] if td.tag=='th' else styles['Cell']) for td in tr] for tr in el.findall('.//tr')]
  n=len(rows[0]);widths=[width*.26,width*.31,width*.43] if n==3 else [width*.35,width*.65] if n==2 else [width/n]*n
  table=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT');table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#123b4a')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),4.5),('BOTTOMPADDING',(0,0),(-1,-1),4.5),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#f0f5f6'),colors.white]),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#ccd7dc'))]));story.extend([table,Spacer(1,9)])
def footer(c,d):
 c.saveState();c.setStrokeColor(colors.HexColor('#ccd7dc'));c.line(42,35,A4[0]-42,35);c.setFont('Body',8);c.setFillColor(colors.HexColor('#52636b'));c.drawString(42,23,'CivicConnect PED v3.0 | Merged to main | 17 October 2026');c.drawRightString(A4[0]-42,23,str(d.page));c.restoreState()
doc=SimpleDocTemplate(str(out),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=40,bottomMargin=48,title='CivicConnect PED v3.0 - Merged',author='CivicConnect team');doc.build(story,onFirstPage=footer,onLaterPages=footer)
pdf=pdfium.PdfDocument(str(out));render=Path('.m3-local/pdf-review');render.mkdir(parents=True,exist_ok=True)
for i in range(len(pdf)):pdf[i].render(scale=1.1).to_pil().save(render/f'final-page-{i+1}.png')
print('Rendered pages:',len(pdf))
