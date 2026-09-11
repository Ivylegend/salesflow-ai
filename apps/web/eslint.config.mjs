import { FlatCompat } from "@eslint/eslintrc";
import path from "path";
import { fileURLToPath } from "url";
const __filename=fileURLToPath(import.meta.url), __dirname=path.dirname(__filename);
const compat=new FlatCompat({baseDirectory:__dirname});
export default [...compat.extends("next/core-web-vitals","next/typescript"),{rules:{"@typescript-eslint/no-explicit-any":"off","@next/next/no-html-link-for-pages":"off"}}];
