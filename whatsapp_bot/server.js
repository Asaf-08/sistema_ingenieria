const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode');
const express = require('express');
const app = express();

app.use(express.json());

// 💥 VARIABLES GLOBALES PARA EL ESTADO
let qrImageBase64 = null;
let whatsappConectado = false;

const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-extensions'],
        timeout: 60000,
        protocolTimeout: 300000
    }
});

// 1. Cuando WhatsApp pide QR, lo convertimos en imagen
client.on('qr', async (qr) => {
    console.log('\n=========================================');
    console.log('📲 NUEVO CÓDIGO QR GENERADO (Visible en la web)');
    console.log('=========================================\n');
    try {
        qrImageBase64 = await qrcode.toDataURL(qr);
        whatsappConectado = false;
    } catch (err) {
        console.error("❌ Error generando imagen QR", err);
    }
});

// 2. Cuando se conecta exitosamente
client.on('ready', () => {
    console.log('✅ ¡Robot de WhatsApp conectado!');
    whatsappConectado = true;
    qrImageBase64 = null; // Limpiamos el QR
});

// 3. Cuando se desconecta
client.on('disconnected', (reason) => {
    console.log('❌ WhatsApp Desconectado', reason);
    whatsappConectado = false;
    qrImageBase64 = null;
});

console.log('Iniciando navegador invisible... (espera unos segundos)');
client.initialize();

// Función auxiliar anti-spam
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// ==============================================================
// 💥 LA API AHORA INICIA DESDE EL PRINCIPIO (NO ESPERA A WHATSAPP)
// ==============================================================

// Ruta modificada para espiar qué está pasando en vivo
app.get('/api/estado', (req, res) => {
    console.log(`🔍 [ALERTA] Django acaba de consultar el estado.`);
    console.log(`   ¿WhatsApp Conectado?: ${whatsappConectado}`);
    console.log(`   ¿Tiene el QR en memoria?: ${qrImageBase64 ? 'SÍ (Enviando Base64...)' : 'NO (Está nulo)'}`);
    
    res.json({
        conectado: whatsappConectado,
        qr: qrImageBase64
    });
});

// Ruta para que Django ordene el cierre de sesión
app.post('/api/desconectar', async (req, res) => {
    try {
        if (whatsappConectado) {
            await client.logout(); // Esto cierra la sesión y borra la carpeta automáticamente
            whatsappConectado = false;
            qrImageBase64 = null;
            console.log("🛑 Sesión cerrada desde la web.");
            
            // Reiniciamos el cliente para que genere un nuevo QR de inmediato
            setTimeout(() => {
                client.initialize();
            }, 2000);
        }
        res.json({ success: true });
    } catch (error) {
        console.error("❌ Error al desconectar:", error);
        res.status(500).json({ error: "No se pudo cerrar sesión" });
    }
});

// Ruta para enviar mensajes
app.post('/api/enviar-mensaje', async (req, res) => {
    try {
        const { telefono, mensaje } = req.body;

        if (!telefono || !mensaje) {
            return res.status(400).json({ error: "Faltan datos." });
        }

        let chatId = telefono;
        if (!chatId.includes('@g.us') && !chatId.includes('@c.us')) {
            let numeroLimpio = telefono.replace(/\D/g, '');
            if (!numeroLimpio.startsWith('51')) {
                numeroLimpio = '51' + numeroLimpio;
            }
            chatId = `${numeroLimpio}@c.us`;
        }

        // Pausa humana anti-baneo
        await sleep(Math.floor(Math.random() * 2000) + 1000); 

        await client.sendMessage(chatId, mensaje);
        console.log(`✉️ Mensaje enviado exitosamente a: ${telefono}`);

        res.status(200).json({ success: true, message: "Mensaje enviado" });

    } catch (error) {
        console.error("❌ Error al enviar:", error);
        res.status(500).json({ error: "Error del bot." });
    }
});

// 💥 RAILWAY ASIGNA EL PUERTO AUTOMÁTICAMENTE, SI NO, USA EL 3000
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`🚀 Servidor puente de WhatsApp escuchando en el puerto ${PORT}...`);
});