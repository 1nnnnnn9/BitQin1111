/* Local mesh deformation of the selected artwork. One shared animation clock;
   no timer survives the original sequence or runs on the ChatGPT page. */
window.createShinchanMotion=(canvas,image)=>{
  if(!canvas)return null;
  const ctx=canvas.getContext('2d'),w=canvas.width,h=canvas.height;
  const cols=22,rows=12,points=[],cells=[];let enabled=true,lastTime=-1;
  for(let y=0;y<=rows;y++)for(let x=0;x<=cols;x++){
    const u=x/cols,v=y/rows;
    const weight=(cx,cy,rx,ry)=>Math.exp(-(((u-cx)/rx)**2)-(((v-cy)/ry)**2));
    points.push({x:u*w,y:v*h,head:weight(.42,.30,.20,.20),left:weight(.405,.775,.055,.075),right:weight(.472,.65,.045,.06)});
  }
  for(let y=0;y<rows;y++)for(let x=0;x<cols;x++){
    const a=y*(cols+1)+x,b=a+1,c=a+cols+1,d=c+1;cells.push([a,b,d],[a,d,c]);
  }
  function triangle(a,b,c,source,vertices=points){
    const p=vertices[a],q=vertices[b],r=vertices[c],A=source[a],B=source[b],C=source[c];
    const det=p.x*(q.y-r.y)+q.x*(r.y-p.y)+r.x*(p.y-q.y);
    const m11=(A.x*(q.y-r.y)+B.x*(r.y-p.y)+C.x*(p.y-q.y))/det;
    const m12=(A.y*(q.y-r.y)+B.y*(r.y-p.y)+C.y*(p.y-q.y))/det;
    const m21=(A.x*(r.x-q.x)+B.x*(p.x-r.x)+C.x*(q.x-p.x))/det;
    const m22=(A.y*(r.x-q.x)+B.y*(p.x-r.x)+C.y*(q.x-p.x))/det;
    const dx=(A.x*(q.x*r.y-r.x*q.y)+B.x*(r.x*p.y-p.x*r.y)+C.x*(p.x*q.y-q.x*p.y))/det;
    const dy=(A.y*(q.x*r.y-r.x*q.y)+B.y*(r.x*p.y-p.x*r.y)+C.y*(p.x*q.y-q.x*p.y))/det;
    ctx.save();ctx.beginPath();ctx.moveTo(A.x,A.y);ctx.lineTo(B.x,B.y);ctx.lineTo(C.x,C.y);ctx.closePath();ctx.clip();
    ctx.transform(m11,m12,m21,m22,dx,dy);ctx.drawImage(image,0,0,w,h);ctx.restore();
  }
  const hands=[
    {box:[.365,.705,.095,.14],tips:[[.392,.794],[.414,.806],[.431,.806],[.44,.786]],offset:0},
    {box:[.433,.585,.068,.12],tips:[[.459,.666],[.47,.668],[.48,.659]],offset:2}
  ].map(hand=>{
    const vertices=[],cells=[],n=15,m=13;
    for(let y=0;y<=m;y++)for(let x=0;x<=n;x++){const u=hand.box[0]+x/n*hand.box[2],v=hand.box[1]+y/m*hand.box[3];vertices.push({x:u*w,y:v*h,weights:hand.tips.map(([cx,cy])=>Math.exp(-(((u-cx)/.010)**2)-(((v-cy)/.018)**2)))});}
    for(let y=0;y<m;y++)for(let x=0;x<n;x++){const a=y*(n+1)+x,b=a+1,c=a+n+1,d=c+1;cells.push([a,b,d],[a,d,c]);}
    return {...hand,vertices,cells};
  });
  return {canvas,setEnabled(value){enabled=value;lastTime=-1;if(!value)canvas.style.opacity='0';},
    paint(t,opacity,reduced){
      if(!enabled||!image.complete||!image.naturalWidth){canvas.style.opacity='0';return false;}
      canvas.style.opacity=String(opacity);
      if(opacity<=0)return true;
      if(lastTime===t)return true;lastTime=t;
      // Paint an intact underlay first to avoid seams between antialiased triangles.
      ctx.drawImage(image,0,0,w,h);
      if(!reduced){
        const clock=Math.max(0,t-7.42),head=Math.sin(clock*2.8)*3.2;
        const pointsNow=points.map(p=>({x:p.x+p.head*Math.sin(clock*2.1)*1.1,y:p.y+p.head*head}));
        for(const cell of cells)triangle(...cell,pointsNow);
        // Each fingertip presses a different key in sequence; wrists stay anchored.
        for(const hand of hands){
          const presses=hand.tips.map((_,i)=>Math.pow(Math.max(0,Math.sin(clock*15-i*1.8+hand.offset)),3));
          const deformed=hand.vertices.map(p=>({x:p.x,y:p.y+p.weights.reduce((sum,weight,i)=>sum+weight*presses[i]*6.5,0)}));
          for(const cell of hand.cells)triangle(...cell,deformed,hand.vertices);
        }
        // A restrained reflected light crosses the glasses while he types.
        const phase=(clock*.24)%1,alpha=Math.sin(phase*Math.PI)*.23;
        ctx.save();ctx.beginPath();ctx.moveTo(w*.34,h*.30+head);ctx.lineTo(w*.52,h*.22+head);ctx.lineTo(w*.535,h*.31+head);ctx.lineTo(w*.35,h*.40+head);ctx.closePath();ctx.clip();
        const x=w*(.29+phase*.3);const glint=ctx.createLinearGradient(x-8,0,x+16,0);
        glint.addColorStop(0,'transparent');glint.addColorStop(.5,`rgba(205,235,255,${alpha})`);glint.addColorStop(1,'transparent');
        ctx.fillStyle=glint;ctx.fillRect(x-8,h*.2,24,h*.25);ctx.restore();
      }
      return true;
    }
  };
};
