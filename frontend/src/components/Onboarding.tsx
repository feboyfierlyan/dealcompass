import { useEffect, useRef, useState } from 'react';
const steps = [
  { selector: '.queue', title: 'Start with your next opportunity', body: 'The list puts deals needing attention first. Choose a company to see its next step.' },
  { selector: '.next-move', title: 'Know what to do next', body: 'Review the suggested action, its owner and any conditions. Prepare follow-up creates a plan you can copy—it does not send anything.' },
  { selector: '.tabs', title: 'See why it is recommended', body: 'Evidence opens the original records. Context graph connects the people, conversations and decisions behind the recommendation.' },
  { selector: '[data-tour="import"]', title: 'Try your own case', body: 'Open Your data to download a template and upload CRM records plus conversations. Your dataset gets its own workspace.' },
];
export function Onboarding({ onClose }: { onClose: () => void }) {
  const [step, setStep] = useState(0);
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(()=>{ const dialog=ref.current; dialog?.showModal(); return ()=>dialog?.close(); },[]);
  useEffect(()=>{
    const element=document.querySelector(steps[step].selector);
    element?.classList.add('tour-highlight'); element?.scrollIntoView({block:'nearest',behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});
    return ()=>element?.classList.remove('tour-highlight');
  },[step]);
  return <dialog ref={ref} className="tour-dialog" onCancel={onClose} aria-labelledby="tour-title">
    <div className="tour-top"><span>QUICK TOUR · {step+1} / {steps.length}</span><button aria-label="Close tour" onClick={onClose}>×</button></div>
    <h2 id="tour-title">{steps[step].title}</h2><p>{steps[step].body}</p>
    <div className="tour-dots" aria-hidden="true">{steps.map((_,i)=><i key={i} className={i===step?'active':''}/>)}</div>
    <footer><button className="text-button" onClick={step ? ()=>setStep(step-1) : onClose}>{step ? 'Back' : 'Skip tour'}</button><button autoFocus className="button primary" onClick={()=>step===steps.length-1?onClose():setStep(step+1)}>{step===steps.length-1?'Start exploring':'Next'}</button></footer>
  </dialog>;
}
