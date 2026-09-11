"use client";
import {useQuery} from "@tanstack/react-query";
import {Mail,MessageSquare} from "lucide-react";
import {api,Lead} from "@/lib/api";
import {Empty,PageHeader} from "@/components/dashboard-ui";
export default function Conversations(){const {data=[]}=useQuery({queryKey:['leads','emails'],queryFn:()=>api<Lead[]>('/api/leads')});const sent=data.flatMap(l=>(l.emails||[]).map(e=>({...e,lead:l})));return <><PageHeader eyebrow="Engagement" title="Conversations" description="Outbound messages logged by the automation engine."/>{sent.length===0?<Empty>No email activity yet. Qualification follow-ups and confirmations will appear here.</Empty>:<div className="panel">{sent.map(e=><div className="flex items-center gap-4 border-b border-[#eceeec] p-4" key={e.id}><div className="grid h-9 w-9 place-items-center rounded-full bg-[#eef2ef]"><Mail size={15}/></div><div className="min-w-0 flex-1"><div className="truncate text-sm font-bold">{e.subject}</div><div className="text-xs text-[#7a837f]">To {e.lead.full_name} · {e.lead.email}</div></div><span className="pill bg-[#e5f2eb] text-[#236450]">{e.status}</span></div>)}</div>}</>}

