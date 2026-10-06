import {API_BASE} from './config';
async function request<T>(path:string,init?:RequestInit):Promise<T>{
  const r=await fetch(`${API_BASE}${path}`,{headers:{'Content-Type':'application/json',...(init?.headers||{})},...init});
  const d=await r.json().catch(()=>({})); if(!r.ok) throw new Error(d.message||d.error||`HTTP ${r.status}`); return d as T;
}
export const api={
 createPassport:(body:any)=>request<{passportId:string;chainVerified?:boolean}>('/api/passports',{method:'POST',body:JSON.stringify(body)}),
 recoverPassport:(body:any)=>request<{passportId:string;recovered:boolean}>('/api/passports/recover',{method:'POST',body:JSON.stringify(body)}),
 challenge:(body:any)=>request<{message:string,nonce:string,expiresAt:number}>('/api/auth/challenge',{method:'POST',body:JSON.stringify(body)}),
 verify:(body:any)=>request<{ok:boolean,address:string,chainId:number}>('/api/auth/verify',{method:'POST',body:JSON.stringify(body)}),
 passport:(id:string)=>request<PassportData>(`/api/passports/${id}`),
 sync:(id:string)=>request<any>(`/api/passports/${id}/sync`,{method:'POST'}),
 score:(id:string)=>request<ScoreResponse>(`/api/passports/${id}/score`,{method:'POST'}),
 risk:(id:string)=>request<RiskResponse>(`/api/passports/${id}/risk`),
 publish:(id:string)=>request<AttestationResponse>(`/api/passports/${id}/publish`,{method:'POST',body:JSON.stringify({chainId:11155111})}),
 attestation:(id:string)=>request<AttestationResponse>(`/api/passports/${id}/attestation`),
 portableAttestation:(id:string)=>request<AttestationResponse>(`/api/passports/${id}/portable-attestation`,{method:'POST'}),
 bundle:(id:string)=>request<any>(`/api/passports/${id}/bundle`),
 history:(id:string)=>request<{history:ScoreHistory[]}>(`/api/passports/${id}/history`),
 receipt:(id:string)=>request<Receipt>(`/api/passports/${id}/receipt`),
 published:(id:string,body:any)=>request<any>(`/api/passports/${id}/published`,{method:'POST',body:JSON.stringify(body)}),
 whatIf:(id:string,action:string)=>request<any>(`/api/passports/${id}/what-if`,{method:'POST',body:JSON.stringify({action})}),
};
export type Activity={id:string;passportId:string;chainId:number;chainName:string;address:string;txHash:string;blockNumber:number;timestamp:number;activityType:string;source:string;contractAddress:string;amount:number;qualityGrade:string;details:Record<string,any>};
export type WalletLink={address:string;chainId:number;verifiedAt:string};
export type PassportData={passportId:string;ownerAddress:string;score:number;confidence:number;sybilRisk:number;tier:number;inputHash:string;linksHash:string;modelVersion:number;version:number;updatedAt:string;lastSyncAt:string;publishedTxHash:string;publishedChain:string;wallets:WalletLink[];activityCount:number;activities:Activity[];genericMetrics:Record<string,any>;lastBreakdown:Record<string,{points:number;max:number;reason:string}>;lastRisk:RiskResponse};
export type ScoreResponse={score:number;baseScore:number;sybilRisk:number;freshnessMultiplier:number;breakdown:Record<string,{points:number;max:number;reason:string}>;confidence:number;risk:RiskResponse;inputHash:string;linksHash:string;modelVersion:number;evidenceCount:number;tier:number};
export type RiskResponse={risk:number;label:string;reasons:string[];rules?:Record<string,number>;features:Record<string,number>};
export type ScoreHistory={score:number;confidence:number;modelVersion:number;inputHash:string;createdAt:string};
export type AttestationResponse={message:any;signature:string;typedData:any;attestor:string};
export type Receipt={passportId:string;score:number;confidence:number;sybilRisk:number;tier:number;modelVersion:number;version:number;inputHash:string;linksHash:string;evidenceCount:number;chains:string[];wallets:number;publishedTxHash:string;publishedChain:string};
