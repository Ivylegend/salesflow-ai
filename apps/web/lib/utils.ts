import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
export function cn(...inputs:ClassValue[]){return twMerge(clsx(inputs))}
export function initials(name:string){return name.split(" ").map(x=>x[0]).join("").slice(0,2).toUpperCase()}
export function relativeDate(date:string){const days=Math.floor((Date.now()-new Date(date).getTime())/86400000);return days===0?"Today":days===1?"Yesterday":`${days}d ago`}

