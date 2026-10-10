import { useEffect, useRef, useState } from 'react';
import { placeTour, tourSteps } from '../lib/tour';
import type { Box } from '../lib/tour';

export function Onboarding({ onClose }: { onClose: () => void }) {
  const [step,setStep]=useState(0);
  const [anchor,setAnchor]=useState<Box|null>(null);
  const [position,setPosition]=useState<Box|null>(null);
  const card=useRef<HTMLDivElement>(null), heading=useRef<HTMLHeadingElement>(null);
  const close=useRef(onClose); close.current=onClose;
  const current=tourSteps[step];
  useEffect(()=>{
    const previous=document.activeElement as HTMLElement|null;
    return ()=>{ if(previous?.isConnected)previous.focus(); };
  },[]);
  useEffect(()=>{
    let frame=0, found:Element|null=null, focused=false, completed=false;
    const same=(a:Box|null,b:Box)=>a&&Math.abs(a.left-b.left)<.5&&Math.abs(a.top-b.top)<.5&&Math.abs(a.width-b.width)<.5&&Math.abs(a.height-b.height)<.5;
    const measure=()=>{
      frame=0;
      const target=document.querySelector(current.target);
      if(!target||!target.getClientRects().length){setAnchor(null);return;}
      if(target!==found){
        found=target;
        const before=target.getBoundingClientRect();
        target.scrollIntoView({block:before.bottom>innerHeight-80||before.top<60?'center':'nearest',inline:'nearest',behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});
        size.observe(target);
      }
      const rect=target.getBoundingClientRect();
      const left=Math.max(6,rect.left-5),top=Math.max(6,rect.top-5);
      const box={left,top,width:Math.max(0,Math.min(innerWidth-6,rect.right+5)-left),height:Math.max(0,Math.min(innerHeight-6,rect.bottom+5)-top)};
      if(!box.width||!box.height){setAnchor(null);return;}
      setAnchor(old=>same(old,box)?old:box);
      const next=placeTour(box,{width:336,height:card.current?.offsetHeight??280},{width:innerWidth,height:innerHeight},current.side);
      setPosition(old=>same(old,next)?old:next);
      if(!focused){focused=true;heading.current?.focus({preventScroll:true});}
    };
    const schedule=()=>{if(!frame)frame=requestAnimationFrame(measure);};
    const mutation=new MutationObserver(schedule),size=new ResizeObserver(schedule);
    mutation.observe(document.body,{childList:true,subtree:true});
    if(card.current)size.observe(card.current);
    window.addEventListener('resize',schedule);window.addEventListener('scroll',schedule,true);
    const advance=()=>{
      if(completed)return;
      completed=true;
      // Run after the real control's event handler and React state update.
      requestAnimationFrame(()=>step===tourSteps.length-1?close.current():setStep(value=>value+1));
    };
    const click=(event:MouseEvent)=>{
      const element=event.target instanceof Element?event.target:null;
      if(!element||card.current?.contains(element))return;
      const action=element.closest(current.action);
      const target=document.querySelector(current.target);
      if(!action||!target?.contains(action)||action.getAttribute('aria-disabled')==='true'||action.hasAttribute('disabled')){
        event.preventDefault();event.stopPropagation();return;
      }
      advance();
    };
    const keys=(event:KeyboardEvent)=>{
      if(event.key==='Escape'){event.preventDefault();close.current();return;}
      // SVG buttons implement keyboard activation themselves (no native click).
      if((event.key==='Enter'||event.key===' ')&&event.target instanceof Element&&event.target.matches('.focus-node')&&event.target.matches(current.action))advance();
      if(event.key!=='Tab')return;
      const target=document.querySelector(current.target);
      const actions=[...document.querySelectorAll<HTMLElement>(current.action)].filter(el=>target?.contains(el)&&el.getClientRects().length>0&&!el.hasAttribute('disabled'));
      const controls=[...card.current?.querySelectorAll<HTMLElement>('button')??[]];
      const options=[...actions,...controls];if(!options.length)return;
      event.preventDefault();const index=options.indexOf(document.activeElement as HTMLElement);
      const next=index<0?(event.shiftKey?options.length-1:0):(index+(event.shiftKey?-1:1)+options.length)%options.length;
      options[next].focus({preventScroll:true});
    };
    document.addEventListener('click',click,true);document.addEventListener('keydown',keys,true);schedule();
    return ()=>{cancelAnimationFrame(frame);mutation.disconnect();size.disconnect();document.removeEventListener('click',click,true);document.removeEventListener('keydown',keys,true);window.removeEventListener('resize',schedule);window.removeEventListener('scroll',schedule,true);};
  },[step,current]);
  const right=anchor?anchor.left+anchor.width:0,bottom=anchor?anchor.top+anchor.height:0;
  return <div className="tour-layer">
    {anchor ? <>
      <div className="tour-spotlight" style={anchor} aria-hidden="true"/>
      <div className="tour-blocker" style={{inset:`0 0 auto 0`,height:anchor.top}}/>
      <div className="tour-blocker" style={{left:0,top:anchor.top,width:anchor.left,height:anchor.height}}/>
      <div className="tour-blocker" style={{left:right,right:0,top:anchor.top,height:anchor.height}}/>
      <div className="tour-blocker" style={{left:0,right:0,top:bottom,bottom:0}}/>
    </> : <div className="tour-wait-overlay"/>}
    <div ref={card} className={`tour-dialog ${position?'placed':'waiting'}`} role="dialog" aria-modal="false" aria-labelledby="tour-title" aria-describedby="tour-description" style={position?{width:position.width,transform:`translate3d(${position.left}px, ${position.top}px, 0)`}:undefined}>
      <div className="tour-top"><span>LEARN BY DOING · {step+1} / {tourSteps.length}</span><button aria-label="Close tour" onClick={onClose}>×</button></div>
      <div aria-live="polite"><h2 ref={heading} tabIndex={-1} id="tour-title">{current.title}</h2><p id="tour-description">{current.body}</p></div>
      <div className="tour-action-hint"><span aria-hidden="true">↗</span>{anchor?current.hint:'Waiting for this part of the page to load…'}</div>
      <footer><button className="text-button" onClick={onClose}>Skip tour</button><span className="tour-dots" aria-hidden="true">{tourSteps.map((_,i)=><i key={i} className={i===step?'active':i<step?'complete':''}/>)}</span></footer>
    </div>
  </div>;
}
