export type Box = { left: number; top: number; width: number; height: number };
export const tourSteps = [
  { target: '.queue-list:has(.queue-item)', action: '.queue-item', title: 'Choose a deal', body: 'Select a company in the highlighted list. Its deal details appear on the right.', hint: 'Select a deal to continue', side: 'right' },
  { target: '[data-tour="tab-reasons"]', action: '[data-tour="tab-reasons"]', title: 'Check the evidence', body: 'Recommendations need a reason. Open Evidence to see the records behind this deal’s next step.', hint: 'Open Evidence to continue', side: 'bottom' },
  { target: '[data-tour="tab-explore"]', action: '[data-tour="tab-explore"]', title: 'Connect the dots', body: 'Open Context graph to see how the people, conversations and decisions connect.', hint: 'Open Context graph to continue', side: 'bottom' },
  { target: '.focus-node.root', action: '.focus-node.root', title: 'Explore a real connection', body: 'Select the highlighted deal card. The graph selects its recorded connections; View evidence opens the underlying source.', hint: 'Select the deal card to continue', side: 'right' },
  { target: '[data-tour="import"]', action: '[data-tour="import"]', title: 'Bring your own case', body: 'Your data opens a separate workspace for CRM records and transcripts. The demo stays available.', hint: 'Open Your data to continue', side: 'right' },
  { target: '[data-tour="template"]', action: '[data-tour="template"]', title: 'Start with a working example', body: 'Download the example, replace its fictional records, then upload and validate it here. You can replay this tour anytime.', hint: 'Download the example to finish', side: 'bottom' },
] as const;

/** Choose an adjacent side that fits; clamp only when no side fits the viewport. */
export function placeTour(anchor: Box, card: {width: number; height: number}, viewport: {width: number; height: number}, preferred = 'right'): Box {
  const gap=16, margin=16, w=Math.min(card.width, viewport.width-2*margin), h=card.height;
  const x=anchor.left, y=anchor.top, r=x+anchor.width, b=y+anchor.height;
  const positions: Record<string, Box>={
    right:{left:r+gap,top:y+(anchor.height-h)/2,width:w,height:h},
    left:{left:x-w-gap,top:y+(anchor.height-h)/2,width:w,height:h},
    bottom:{left:x+(anchor.width-w)/2,top:b+gap,width:w,height:h},
    top:{left:x+(anchor.width-w)/2,top:y-h-gap,width:w,height:h},
  };
  const sides=[preferred,...['right','left','bottom','top'].filter(s=>s!==preferred)];
  const fits=(p:Box)=>p.left>=margin&&p.top>=margin&&p.left+w<=viewport.width-margin&&p.top+h<=viewport.height-margin;
  // Cross-axis clamping preserves adjacency on the chosen side.
  const candidates=sides.map(side=>{
    const p={...positions[side]};
    if(side==='right'||side==='left') p.top=Math.max(margin,Math.min(p.top,viewport.height-h-margin));
    else p.left=Math.max(margin,Math.min(p.left,viewport.width-w-margin));
    return p;
  });
  const p=candidates.find(fits)??candidates[0];
  return {...p,left:Math.max(margin,Math.min(p.left,viewport.width-w-margin)),top:Math.max(margin,Math.min(p.top,viewport.height-h-margin))};
}
