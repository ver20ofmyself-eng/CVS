import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
    plugins: [vue()],
    resolve: {
        alias: {
            '@': path.resolve(__dirname, './src')
        }
    },
    server: {
        port: 3004,
        proxy: {
            '/api': {
                target: 'http://127.0.0.1:8000',  // Используем IPv4 вместо localhost
                changeOrigin: true,
                secure: false,
                rewrite: (path) => path,
                configure: (proxy, options) => {
                    proxy.on('error', (err, req, res) => {
                        console.log('❌ Прокси ошибка:', err)
                    })
                    proxy.on('proxyReq', (proxyReq, req, res) => {
                        console.log('➡️ Прокси запрос:', req.method, req.url, '→', proxyReq.path)
                    })
                    proxy.on('proxyRes', (proxyRes, req, res) => {
                        console.log('⬅️ Прокси ответ:', proxyRes.statusCode, req.url)
                    })
                }
            }
        }
    }
})
