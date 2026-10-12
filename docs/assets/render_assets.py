"""Render repository-native brand and architecture assets (optional: matplotlib)."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Polygon

OUT = Path(__file__).resolve().parent
plt.rcParams.update({'font.family': 'DejaVu Sans', 'svg.fonttype': 'none'})
INK='#19372E'; GREEN='#28664D'; MUTED='#60766E'; LINE='#CCDAD3'; PALE='#EDF4EF'

def canvas(w,h,bg):
    fig=plt.figure(figsize=(w/100,h/100),dpi=160,facecolor=bg)
    ax=fig.add_axes([0,0,1,1]); ax.set_xlim(0,w); ax.set_ylim(h,0); ax.axis('off')
    return fig,ax

def box(ax,x,y,w,h,fill,stroke=None,r=16):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle=f'round,pad=0,rounding_size={r}',facecolor=fill,edgecolor=stroke or fill,linewidth=1.2))

def txt(ax,x,y,s,size=18,color=INK,weight='normal',**kw):
    ax.text(x,y,s,fontsize=size,color=color,weight=weight,va='top',**kw)

def arrow(ax,a,b,color=GREEN,dashed=False):
    ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=15,color=color,linewidth=1.8,linestyle='--' if dashed else '-'))

def save(fig,name):
    for ext in ('png','svg'):
        fig.savefig(OUT/f'{name}.{ext}',facecolor=fig.get_facecolor())
        if ext == 'svg':
            path=OUT/f'{name}.{ext}'
            path.write_text(path.read_text().replace("font-family: 'DejaVu Sans'", "font-family: 'DejaVu Sans', Arial, sans-serif"))
    plt.close(fig)

fig,ax=canvas(1600,560,INK)
for r in [105,175,250]: ax.add_patch(Circle((1300,278),r,fill=False,edgecolor='#2B493F',linewidth=1))
box(ax,64,53,205,32,'#2D4E40',r=16)
txt(ax,81,60,'CONTEXT TO ACTION',11,'#C9E4D4','bold')
ax.add_patch(Circle((90,163),25,fill=False,edgecolor='#9DE0BA',linewidth=2))
ax.add_patch(Polygon([[80,176],[105,146],[97,169]],facecolor='#9DE0BA'))
txt(ax,133,132,'DealCompass',42,'#FFFFFF','bold')
txt(ax,64,236,'Know which deal needs you.\nSee the evidence. Take the next step.',27,'#FFFFFF','bold',linespacing=1.4)
txt(ax,64,355,'Sales priorities grounded in conversations,\nrelationships and past decisions.',17,'#BDD1C6',linespacing=1.5)
txt(ax,64,484,'HACKATHON PENS 2026     /     BOY · BIMA · ICAL',11,'#BDD1C6')
# Conceptual product flow, not a dataset graph or fabricated result.
for a,b in [((1115,164),(1285,256)),((1460,164),(1330,256)),((1300,324),(1300,401))]:
 arrow(ax,a,b,'#79AB91')
for x,y,w,label,sub in [(965,98,275,'Conversations','Customer context'),(1280,98,265,'Decision history','Precedents & constraints'),(1140,251,310,'Context graph','Traceable relationships'),(1140,411,310,'Next best step','Owner · target · evidence')]:
 box(ax,x,y,w,82,'#24483A','#547C65',14)
 txt(ax,x+23,y+16,label,16,'#FFFFFF','bold'); txt(ax,x+23,y+46,sub,12,'#BBD6C7')
save(fig,'banner')

fig,ax=canvas(1600,1030,'#FAFCFA')
txt(ax,60,45,'From source records to a defensible next step',30,INK,'bold')
txt(ax,60,101,'DealCompass system architecture  /  implemented flow',15,MUTED)
# Three columns: data / backend / UI, with external provider beneath the backend.
box(ax,55,169,345,702,'#F0F5F1',LINE)
txt(ax,80,194,'01   SOURCE CONTEXT',13,GREEN,'bold')
for y,title,sub in [(246,'CRM & people','Accounts, deals, contacts, history'),(340,'Conversations','Email and meeting transcripts'),(434,'Product & support','Usage, tickets, bugs, roadmap'),(528,'Billing & decisions','Contracts and canonical decision log')]:
 box(ax,78,y,298,76,'white',LINE,10); txt(ax,96,y+14,title,16,INK,'bold'); txt(ax,96,y+44,sub,10.7,MUTED)
txt(ax,82,638,'Built-in demo',15,INK,'bold'); txt(ax,82,670,'P01–P05 · snapshot 2026-10-01',12,MUTED)
txt(ax,82,730,'Or validated uploads',15,INK,'bold'); txt(ax,82,762,'JSON / CSV + JSONL ZIP\nSeparate temporary workspaces',12,MUTED,linespacing=1.6)
box(ax,466,169,610,702,'white',LINE)
txt(ax,490,194,'02   FASTAPI BACKEND',13,GREEN,'bold')
for y,title,sub in [(246,'Validate & normalize','Stable IDs · dates · source rows'),(367,'Build context graph','NetworkX · direct / inferred edges · provenance'),(488,'Rank & diagnose','Deterministic heuristic · factors · supporting paths'),(609,'Analyze the next step','Rules → optional Jev → evidence / policy checks')]:
 box(ax,490,y,562,88,PALE,LINE,10); txt(ax,513,y+15,title,19,INK,'bold'); txt(ax,513,y+51,sub,12,MUTED)
for y in (334,455,576): arrow(ax,(770,y),(770,y+31))
box(ax,490,746,562,88,'#F6F7F2',LINE,10)
txt(ax,513,762,'One persistent volume',17,INK,'bold')
txt(ax,513,797,'Separate SQLite cache + usage ledger; upload files',11.5,MUTED)
box(ax,1142,169,403,702,INK)
txt(ax,1168,194,'03   REACT WORKSPACE',13,'#A5D6B9','bold')
for y,title,sub in [(259,'Prioritize','Choose a deal and its next action'),(393,'Understand','Read evidence and approval needs'),(527,'Explore','Follow nodes, edges and sources'),(661,'Prepare','Review and copy a follow-up plan')]:
 txt(ax,1171,y,title,23,'white','bold'); txt(ax,1171,y+49,sub,12,'#C1D9CB')
arrow(ax,(400,290),(464,290)); arrow(ax,(1076,531),(1140,531))
box(ax,466,908,1079,77,'#E7F2EA',LINE,12)
txt(ax,490,921,'Optional TypeSafe / Jev',16,INK,'bold')
txt(ax,820,922,'Backend only · guarded token budget · upload opt-in',13,INK)
txt(ax,820,951,'Failure / ineligible context → explicit rules fallback',12,MUTED)
arrow(ax,(1052,655),(1103,655)); arrow(ax,(1103,655),(1103,904),dashed=True)
txt(ax,61,917,'Single service / worker\nSame-origin UI + API',13,MUTED,linespacing=1.6)
save(fig,'architecture')
print('Rendered banner and architecture: PNG + SVG')
