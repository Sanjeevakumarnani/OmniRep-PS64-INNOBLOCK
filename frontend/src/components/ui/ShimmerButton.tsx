import {ButtonHTMLAttributes} from 'react';
export function ShimmerButton({className='',children,type='button',...props}:ButtonHTMLAttributes<HTMLButtonElement>){return <button className={`shimmer-btn ${className}`} type={type} {...props}><span className="shimmer-ring" aria-hidden/>{children}</button>}
