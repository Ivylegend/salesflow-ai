import type { Metadata } from "next";
import "./globals.css";
import Providers from "./providers";
export const metadata:Metadata={title:{default:"SalesFlow AI — Intelligent sales automation",template:"%s · SalesFlow AI"},description:"Capture, qualify and nurture every sales opportunity automatically."};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body><Providers>{children}</Providers></body></html>}

