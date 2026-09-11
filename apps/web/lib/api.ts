export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export type Lead = {id:string;full_name:string;email:string;company:string;job_title:string;company_size:string;industry:string;interest:string;budget:string;timeline:string;message?:string;source:string;is_demo:boolean;stage:string;score:number|null;classification:string|null;estimated_value:number;created_at:string;updated_at:string;qualification?:Qualification;activities?:Activity[];notes?:{id:string;body:string;created_at:string}[];emails?:{id:string;subject:string;status:string;sent_at?:string}[];appointments?:{id:string;starts_at:string;status:string;booking_url?:string}[]};
export type Qualification={score:number;classification:string;intent:string;fit:string;urgency:string;conversion_likelihood:number;summary:string;needs:string[];objections:string[];recommended_action:string;follow_up:string};
export type Activity={id:string;type:string;title:string;description?:string;created_at:string};
export async function api<T>(path:string, options:RequestInit={}):Promise<T>{
  const token=typeof window!=="undefined"?localStorage.getItem("sf_token"):null;
  const response=await fetch(`${API_URL}${path}`,{...options,headers:{"Content-Type":"application/json",...(token?{Authorization:`Bearer ${token}`}:{...options.headers})}});
  if(!response.ok) throw new Error((await response.json().catch(()=>({}))).detail||"Request failed");
  return response.json();
}

