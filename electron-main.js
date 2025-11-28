const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const express = require('express');
const cors = require('cors');

let mainWindow = null;
let pythonProcess = null;
let serverPort = 5000;

// Express server for Python backend communication
const server = express();
server.use(cors());
server.use(express.json());

// Global progress state
let currentProgress = { percent: 0, step: 0, logs: [], status: 'idle' };

// API Routes
server.post('/api/export/start', (req, res) => {
    const { cookies } = req.body;
    
    if (!cookies.skey || !cookies.tfv) {
        return res.status(400).json({ status: 'error', message: 'Missing cookies' });
    }
    
    // Reset progress
    currentProgress = { percent: 0, step: 0, logs: [], status: 'running' };
    
    // Start Python backend
    startPythonExport(cookies);
    
    res.json({ status: 'started' });
});

server.get('/api/export/progress', (req, res) => {
    res.json(currentProgress);
});

server.get('/api/sites', (req, res) => {
    res.json([
        { id: 'mangapark', name: 'MangaPark', url: 'https://mangapark.net', status: 'active' },
        { id: 'mangadex', name: 'MangaDex', url: 'https://mangadex.org', status: 'planned' },
        { id: 'mangasee', name: 'MangaSee', url: 'https://mangasee123.com', status: 'planned' }
    ]);
});

// Start Express server
server.listen(serverPort, () => {
    console.log(`Backend API running on http://localhost:${serverPort}`);
});

function startPythonExport(cookies) {
    // Find Python executable
    const pythonPath = process.platform === 'win32' 
        ? 'C:/Users/leodu/AppData/Local/Microsoft/WindowsApps/python3.11.exe'
        : 'python3';
    
    // Create Python script to run export
    const scriptPath = path.join(__dirname, 'run_export.py');
    
    pythonProcess = spawn(pythonPath, [scriptPath, JSON.stringify(cookies)]);
    
    pythonProcess.stdout.on('data', (data) => {
        const lines = data.toString().split('\n');
        lines.forEach(line => {
            if (line.trim()) {
                try {
                    const update = JSON.parse(line);
                    if (update.percent !== undefined) currentProgress.percent = update.percent;
                    if (update.step !== undefined) currentProgress.step = update.step;
                    if (update.log) currentProgress.logs.push(update.log);
                    if (update.status) currentProgress.status = update.status;
                    
                    // Send to renderer
                    if (mainWindow) {
                        mainWindow.webContents.send('export-progress', currentProgress);
                    }
                } catch (e) {
                    console.log('Python:', line);
                }
            }
        });
    });
    
    pythonProcess.stderr.on('data', (data) => {
        console.error('Python error:', data.toString());
        currentProgress.logs.push({
            type: 'error',
            message: data.toString(),
            time: new Date().toLocaleTimeString()
        });
    });
    
    pythonProcess.on('close', (code) => {
        console.log(`Python process exited with code ${code}`);
        if (code === 0) {
            currentProgress.status = 'completed';
        } else {
            currentProgress.status = 'error';
        }
    });
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        backgroundColor: '#0f172a',
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        icon: path.join(__dirname, 'icon.png'),
        autoHideMenuBar: true,
        title: 'Multi-Site Manga Exporter'
    });

    // Load HTML file
    mainWindow.loadFile('mangapark_gui_web.html');

    // Inject API bridge after load
    mainWindow.webContents.on('did-finish-load', () => {
        mainWindow.webContents.executeJavaScript(`
            // Backend API endpoints
            const API_BASE = 'http://localhost:${serverPort}';
            
            // Override startDemo to use real export
            window.originalStartDemo = window.startDemo;
            window.startDemo = async function() {
                const config = {
                    cookies: {
                        skey: document.getElementById('skeyCookie')?.value || '',
                        tfv: document.getElementById('tfvCookie')?.value || '',
                        theme: document.getElementById('themeCookie')?.value || '',
                        wd: document.getElementById('wdCookie')?.value || ''
                    }
                };
                
                if (!config.cookies.skey || !config.cookies.tfv) {
                    showToast('Please enter at least skey and tfv cookies', 'error');
                    return;
                }
                
                try {
                    const response = await fetch(API_BASE + '/api/export/start', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(config)
                    });
                    const result = await response.json();
                    
                    if (result.status === 'started') {
                        showToast('Export started! Check progress below', 'success');
                        startProgressPolling();
                    } else {
                        showToast('Failed to start export', 'error');
                    }
                } catch (error) {
                    showToast('Error: ' + error.message, 'error');
                }
            };
            
            // Poll for progress updates
            let progressInterval = null;
            function startProgressPolling() {
                if (progressInterval) clearInterval(progressInterval);
                
                progressInterval = setInterval(async () => {
                    try {
                        const response = await fetch(API_BASE + '/api/export/progress');
                        const data = await response.json();
                        
                        if (data.percent !== undefined) {
                            updateProgress(data.percent);
                        }
                        
                        if (data.step !== undefined) {
                            updateStep(data.step, 'active');
                        }
                        
                        // Add new logs
                        if (data.logs && data.logs.length > 0) {
                            const logContainer = document.getElementById('logContainer');
                            const currentLogCount = logContainer?.children.length || 0;
                            
                            for (let i = currentLogCount; i < data.logs.length; i++) {
                                addLog(data.logs[i]);
                            }
                        }
                        
                        // Stop polling if completed or error
                        if (data.status === 'completed' || data.status === 'error') {
                            clearInterval(progressInterval);
                            progressInterval = null;
                            
                            if (data.status === 'completed') {
                                showToast('Export completed successfully!', 'success');
                            }
                        }
                    } catch (error) {
                        console.error('Progress polling error:', error);
                    }
                }, 500);
            }
        `);
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
        if (pythonProcess) {
            pythonProcess.kill();
        }
    });
}

app.whenReady().then(() => {
    createWindow();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (pythonProcess) {
        pythonProcess.kill();
    }
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

// Handle app quit
app.on('before-quit', () => {
    if (pythonProcess) {
        pythonProcess.kill();
    }
});
