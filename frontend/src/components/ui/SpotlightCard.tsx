import {HTMLAttributes,useRef} from 'react';
export function SpotlightCard({className='',children,...props}:HTMLAttributes<HTMLDivElement>){
 const ref=useRef<HTMLDivElement>(null);
 const move=(e:React.PointerEvent<HTMLDivElement>)=>{const r=ref.current?.getBoundingClientRect();if(!r)return;ref.current!.style.setProperty('--mx',`${e.clientX-r.left}px`);ref.current!.style.setProperty('--my',`${e.clientY-r.top}px`)};
 return <div ref={ref} onPointerMove={move} className={`spotlight-card ${className}`} {...props}>{children}</div>
}
