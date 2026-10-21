import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';
const target=process.env.MESA_API_TARGET||'http://127.0.0.1:58000';
export default defineConfig({plugins:[react()],server:{hmr:process.env.MESA_E2E_URL?false:undefined,watch:process.env.MESA_E2E_URL?null:undefined,proxy:{'/api':target,'/admin':target,'/static':target}}});
