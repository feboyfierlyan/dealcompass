const {test}=require('node:test');
const assert=require('node:assert/strict');
const {placeTour}=require(`${process.env.TOUR_TEST_BUILD}/tour.js`);
const overlap=(a,b)=>a.left<b.left+b.width&&a.left+a.width>b.left&&a.top<b.top+b.height&&a.top+a.height>b.top;
for(const viewport of [{width:1280,height:720},{width:1440,height:900},{width:1920,height:1080}]){
 for(const [label,anchor,side] of [
  ['deal queue',{left:224,top:112,width:246,height:398},'right'],
  ['evidence tab',{left:650,top:145,width:108,height:40},'bottom'],
  ['rightmost node',{left:viewport.width-260,top:300,width:235,height:90},'right'],
  ['bottom node',{left:500,top:viewport.height-120,width:235,height:90},'bottom'],
  ['sidebar item',{left:10,top:144,width:195,height:40},'right'],
 ])test(`${viewport.width} desktop: ${label} stays adjacent, readable and inside the viewport`,()=>{
  const box=placeTour(anchor,{width:336,height:312},viewport,side);
  assert.ok(box.left>=16&&box.top>=16);
  assert.ok(box.left+box.width<=viewport.width-16&&box.top+box.height<=viewport.height-16);
  assert.ok(!overlap(anchor,box),'Popover must not cover the action required to continue');
  const gaps=[Math.abs(box.left-(anchor.left+anchor.width)),Math.abs(anchor.left-(box.left+box.width)),Math.abs(box.top-(anchor.top+anchor.height)),Math.abs(anchor.top-(box.top+box.height))];
  assert.ok(gaps.includes(16),'At least one side must remain anchored at the intended gap');
 });
}
