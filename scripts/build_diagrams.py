"""Render compact design diagrams from the implemented module boundaries."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT=Path('docs/figures')
OUT.mkdir(parents=True,exist_ok=True)


def diagram(name,nodes,edges,title,size=(10,4)):
    fig,ax=plt.subplots(figsize=size)
    ax.set_xlim(0,10);ax.set_ylim(0,5);ax.axis('off')
    for key,(x,y,w,h,text) in nodes.items():
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.06',facecolor='#f1f5f9',edgecolor='#475569',lw=1.1))
        ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=10,color='#0f172a',linespacing=1.4)
    for u,v,label in edges:
        a,b=nodes[u],nodes[v]
        if b[0]>a[0]+a[2]/2:
            p1=(a[0]+a[2],a[1]+a[3]/2);p2=(b[0],b[1]+b[3]/2)
        else:
            p1=(a[0]+a[2]/2,a[1]);p2=(b[0]+b[2]/2,b[1]+b[3])
        ax.add_patch(FancyArrowPatch(p1,p2,arrowstyle='-|>',mutation_scale=12,color='#2563eb'))
        if label: ax.text((p1[0]+p2[0])/2,(p1[1]+p2[1])/2+.15,label,ha='center',fontsize=8,color='#334155')
    ax.set_title(title,loc='left',fontsize=14,pad=12,color='#0f172a')
    fig.tight_layout();fig.savefig(OUT/(name+'.png'),dpi=180,bbox_inches='tight');plt.close(fig)


def build_diagrams():
    diagram('architecture',{
      'd':(.1,3,2.2,1,'CSV validation\nsrc/pipeline'),
      'm':(3,3,2.3,1,'Scenario features\nsrc/model'),
      'r':(6.1,3,3.5,1,'Expanded station and line search\nsrc/routing'),
      'g':(.1,.7,2.2,1,'Station and route CSV\nMultiDiGraph'),
      'u':(6.1,.7,3.5,1,'Streamlit view\nItineraries and comparisons')},
      [('d','m','history'),('m','r','predictions'),('g','r','network'),('r','u','results')],
      'Component architecture and data flow')
    from matplotlib.patches import Ellipse, Rectangle, Circle
    fig,ax=plt.subplots(figsize=(10,4))
    ax.set_xlim(0,10);ax.set_ylim(0,5);ax.axis('off')
    ax.add_patch(Rectangle((2.7,.15),4.6,4.6,fill=False,edgecolor='#475569'))
    ax.text(5,4.5,'Transport simulation',ha='center',fontsize=12,fontweight='bold')
    for x,label in [(1.1,'Commuter'),(8.9,'Developer')]:
        ax.add_patch(Circle((x,3.3),.17,fill=False,edgecolor='#334155'))
        ax.plot([x,x],[3.13,2.55],color='#334155');ax.plot([x-.3,x+.3],[2.9,2.9],color='#334155')
        ax.plot([x-.3,x,x+.3],[2.2,2.55,2.2],color='#334155')
        ax.text(x,1.8,label,ha='center',fontsize=10)
    for y,label in [(3.7,'Select trip and scenario'),(2.65,'Compare route and metrics'),(1.6,'Inspect interactive network'),(.6,'Reproduce benchmark')]:
        ax.add_patch(Ellipse((5,y),3.8,.7,facecolor='#f1f5f9',edgecolor='#475569'))
        ax.text(5,y,label,ha='center',va='center',fontsize=10)
        x0=8.6 if y==.6 else 1.4
        ax.plot([x0,6.9 if y==.6 else 3.1],[2.7,y],color='#64748b',lw=1)
    ax.set_title('Use case diagram',loc='left',fontsize=14)
    fig.tight_layout();fig.savefig(OUT/'use_cases.png',dpi=180,bbox_inches='tight');plt.close(fig)
    diagram('workflow',{
      'i':(.1,2,1.7,1,'Trip and scenario'),
      'v':(2.2,2,1.7,1,'Validate inputs'),
      'p':(4.3,2,1.7,1,'Predict network'),
      'r':(6.4,2,1.7,1,'Search twice'),
      'o':(8.5,2,1.3,1,'Compare\nand display')},
      [('i','v',''),('v','p',''),('p','r',''),('r','o','')],
      'Activity flow for one scenario')
    diagram('data_flow',{
      'h':(.1,3,2.2,.8,'Synthetic history'),
      't':(3,3,2.2,.8,'Offline training'),
      'a':(6,3,3,.8,'Versioned model artifact'),
      'q':(.1,.7,2.2,.8,'Scenario and graph'),
      'p':(3,.7,2.2,.8,'Predict and optimize'),
      'o':(6,.7,3,.8,'Comparison data and charts')},
      [('h','t',''),('t','a',''),('q','p',''),('a','p','load'),('p','o','')],
      'Data flow separates offline training and trip queries')
    # Sequence uses a purpose-built diagram to avoid diagonal connectors through labels.
    fig,ax=plt.subplots(figsize=(10,4.2));ax.set_xlim(0,10);ax.set_ylim(0,6);ax.axis('off')
    xs=[.8,3.4,6.1,9];labels=['Commuter','Streamlit','Predictor','Router']
    for x,l in zip(xs,labels):
        ax.text(x,5.7,l,ha='center',fontsize=11,fontweight='bold');ax.plot([x,x],[.4,5.4],ls='--',color='#94a3b8')
    for y,i,j,label in [(4.8,0,1,'Select scenario'),(4,1,2,'predict_network'),(3.2,2,1,'station congestion'),(2.4,1,3,'compare_routes'),(1.6,3,1,'two itineraries and metrics'),(.8,1,0,'render comparison')]:
        ax.annotate('',xy=(xs[j],y),xytext=(xs[i],y),arrowprops=dict(arrowstyle='->',color='#2563eb'))
        ax.text((xs[i]+xs[j])/2,y+.12,label,ha='center',fontsize=9)
    fig.tight_layout();fig.savefig(OUT/'sequence.png',dpi=180);plt.close(fig)

if __name__=='__main__':
    build_diagrams()
