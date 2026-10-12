"""Pitch-deck figures derived from saved first-run receipts; no provider requests."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/dealcompass-mpl')
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Patch

HERE=Path(__file__).parent
BASE=HERE.parent
DATA={arm:json.loads((BASE/'results'/f'{arm}.json').read_text()) for arm in ('rules','hybrid')}
SUMMARY={a['arm']:a for a in json.loads((BASE/'results/summary.json').read_text())['arms']}
N=16
INK='#18342C';MUTED='#536A61';GREEN='#167C59';GREY='#AAB8B2';BG='#F5F8F6';LINE='#DFE7E2';AMBER='#A65D16'
plt.rcParams.update({'font.family':'DejaVu Sans','svg.fonttype':'none','pdf.fonttype':42})

def screens(row):
    c=row['checks']
    return [all(c.get(k) is True for k in ('citation_ids_resolve','graph_edges_resolve','supporting_paths_resolve')),c.get('action_family_screen') is True,c.get('approval_gate_screen') is True,not row['error'] and bool(c) and all(c.values())]

VALUES={arm:[sum(screens(r)[i] for r in data['cases']) for i in range(4)] for arm,data in DATA.items()}
for arm in DATA:
    assert len(DATA[arm]['cases'])==N
    assert VALUES[arm][1]==SUMMARY[arm]['metrics']['action_family_screen']['passed']
    assert VALUES[arm][2]==SUMMARY[arm]['metrics']['approval_gate_screen']['passed']
    assert VALUES[arm][3]==SUMMARY[arm]['all_screens_passed']

def frame(title,subtitle):
    fig=plt.figure(figsize=(16,9),facecolor=BG)
    fig.text(.055,.94,'DEALCOMPASS  /  BENCHMARK',fontsize=12,color=GREEN,weight='bold')
    fig.text(.945,.94,'10 OCT 2026',fontsize=11,color=MUTED,ha='right')
    fig.text(.055,.867,title,fontsize=29,color=INK,weight='bold')
    fig.text(.055,.819,subtitle,fontsize=13.5,color=MUTED)
    return fig

def footer(fig):
    fig.text(.055,.095,'16 synthetic cases • AI-authored expectations frozen before testing • Independent human review pending',fontsize=11.5,color=INK)
    fig.text(.055,.063,'Checks cover IDs/path structure and automated action/policy screens. No overall accuracy or closing-uplift claim.',fontsize=10.8,color=MUTED)
    fig.text(.055,.028,'Source: saved rules + production hybrid API receipts · Engine 5ecd9ec8b69f · Frozen input/code 29697df',fontsize=9.5,color=MUTED)

def export(fig,name):
    for ext in ('png','svg','pdf'):
        fig.savefig(HERE/f'{name}.{ext}',dpi=200,facecolor=fig.get_facecolor())
    plt.close(fig)

fig=frame('Tested on 16 new sales cases','Rules-only baseline vs the deployed Rules + Jev workflow · identical case inputs')
ax=fig.add_axes([.315,.22,.62,.51],facecolor=BG)
labels=['Evidence & graph\nstructure checks','Expected action\nfamily screen','Explicit approval\ngate screen','All applicable\nchecks passed']
for i,label in enumerate(labels):
    y=3-i
    ax.text(-.7,y,label,ha='right',va='center',fontsize=15.5,color=INK,weight='medium')
    for arm,off,color in [('rules',.16,GREY),('hybrid',-.16,GREEN)]:
        v=VALUES[arm][i]
        ax.barh(y+off,16,height=.24,color='#E8EEEA',zorder=1)
        ax.barh(y+off,v,height=.24,color=color,zorder=2)
        ax.text(v-.22,y+off,f'{v}/16',ha='right',va='center',fontsize=14,weight='bold',color='white' if arm=='hybrid' else INK,zorder=3)
ax.set_xlim(0,16);ax.set_ylim(-.55,3.55);ax.set_yticks([]);ax.set_xticks([0,4,8,12,16]);ax.tick_params(axis='x',length=0,labelsize=11,colors=MUTED,pad=9)
ax.set_xlabel('Cases passing the stated check',fontsize=11.5,color=MUTED,labelpad=12)
ax.grid(axis='x',color=LINE,zorder=0);ax.set_axisbelow(True)
for s in ax.spines.values():s.set_visible(False)
fig.legend(handles=[Patch(facecolor=GREY,label='Rules only'),Patch(facecolor=GREEN,label='Rules + Jev workflow')],loc='upper left',bbox_to_anchor=(.31,.795),ncol=2,frameon=False,fontsize=12,handlelength=1.4,columnspacing=2.5,labelcolor=INK)
footer(fig);export(fig,'benchmark-overview')

fig=frame('Every case stays in the result','Case-level audit · P = pass, F = fail · empty/fallback cases remain in the denominator')
ax=fig.add_axes([.35,.155,.585,.56]);ax.set_xlim(-.1,8.6);ax.set_ylim(16,0);ax.axis('off')
short=['15% request; no decision','10% discount boundary','Valid VP approval','Wrong approver role','Approval for another deal','10% approval; 15% request','Unlogged approval claim','Reference requested','Reference request negated','English discount request','Price paraphrase','No conversations','Old request withdrawn','Instruction inside transcript','Rejected prior decision','10-outlet pilot; 30 outlets']
for i,(rule,hybrid) in enumerate(zip(DATA['rules']['cases'],DATA['hybrid']['cases'])):
    assert rule['id']==hybrid['id']
    ax.text(-.24,i+.5,f"{rule['id']}  {short[i]}",ha='right',va='center',fontsize=11.5,color=INK)
    for arm_index,row in enumerate((rule,hybrid)):
        for k,ok in enumerate(screens(row)):
            x=arm_index*4.55+k
            ax.add_patch(FancyBboxPatch((x,i+.11),.83,.78,boxstyle='round,pad=0.01,rounding_size=0.08',facecolor='#DFEFE7' if ok else '#F9E8D8',edgecolor='none'))
            ax.text(x+.415,i+.51,'P' if ok else 'F',ha='center',va='center',fontsize=11.5,weight='bold',color=GREEN if ok else AMBER)
for group,label in enumerate(('RULES ONLY','RULES + JEV WORKFLOW')):
    ax.text(group*4.55+1.9,-1.24,label,ha='center',va='center',fontsize=12,weight='bold',color=GREEN if group else MUTED,clip_on=False)
    for k,label in enumerate(('Evidence','Action','Gate','All checks')):
        ax.text(group*4.55+k+.415,-.45,label,ha='center',fontsize=10.5,color=MUTED,clip_on=False)
footer(fig);export(fig,'benchmark-case-matrix')
print('Created 3200×1800 PNG, editable SVG and PDF for both charts. Counts:',VALUES)
