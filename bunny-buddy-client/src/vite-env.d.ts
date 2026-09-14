/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_BUNNY_API_URL?: string;
}
interface ImportMeta {
  readonly env: ImportMetaEnv;
}
