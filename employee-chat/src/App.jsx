
import React, { useState, useRef, useEffect } from 'react';
import {
    Box,
    Paper,
    TextField,
    IconButton,
    Typography,
    List,
    ListItem,
    Avatar,
    CircularProgress,
    Button
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PersonIcon from '@mui/icons-material/Person';

function App() {
    const [token, setToken] = useState(localStorage.getItem('chat_token'));
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loginError, setLoginError] = useState('');
    const [messages, setMessages] = useState([
        { id: 1, text: "Hello! I am your AI Assistant. Use me to upload documents or ask questions.", sender: 'bot' }
    ]);
    const [inputText, setInputText] = useState('');
    const [selectedFile, setSelectedFile] = useState(null);
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);
    const fileInputRef = useRef(null);

    const handleLogin = async (e) => {
        e.preventDefault();
        try {
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);

            const response = await fetch('/api/v1/auth/token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData,
            });

            if (!response.ok) {
                throw new Error('Login failed');
            }

            const data = await response.json();
            localStorage.setItem('chat_token', data.access_token);
            setToken(data.access_token);
            setLoginError('');
        } catch (err) {
            setLoginError('Invalid credentials');
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('chat_token');
        setToken(null);
        setMessages([{ id: 1, text: "Hello! I am your AI Assistant. Use me to upload documents or ask questions.", sender: 'bot' }]);
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        if (token) scrollToBottom();
    }, [messages, token]);

    const handleFileSelect = (event) => {
        if (event.target.files && event.target.files[0]) {
            setSelectedFile(event.target.files[0]);
        }
    };

    const handleSend = async () => {
        if (!inputText.trim() && !selectedFile) return;

        const userMessage = {
            id: Date.now(),
            text: inputText,
            file: selectedFile ? selectedFile.name : null,
            sender: 'user'
        };

        setMessages(prev => [...prev, userMessage]);

        const formData = new FormData();
        if (inputText) formData.append('message', inputText);
        if (selectedFile) formData.append('file', selectedFile);

        setLoading(true);
        setInputText('');
        setSelectedFile(null);
        if (fileInputRef.current) fileInputRef.current.value = '';

        try {
            const response = await fetch('/api/v1/chat/message', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });

            if (!response.ok) {
                if (response.status === 401) {
                    handleLogout();
                    throw new Error("Session expired");
                }
                throw new Error(`Error: ${response.statusText}`);
            }

            const data = await response.json();

            const botMessage = {
                id: Date.now() + 1,
                text: data.response || "I processed your request.",
                sender: 'bot'
            };

            setMessages(prev => [...prev, botMessage]);

        } catch (error) {
            console.error("Chat error:", error);
            setMessages(prev => [...prev, {
                id: Date.now() + 1,
                text: "Sorry, I encountered an error. Please try again.",
                sender: 'bot',
                error: true
            }]);
        } finally {
            setLoading(false);
        }
    };

    if (!token) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh" bgcolor="#f5f5f5">
                <Paper elevation={3} sx={{ p: 4, width: 300, textAlign: 'center' }}>
                    <Typography variant="h5" gutterBottom>Employee Login</Typography>
                    <form onSubmit={handleLogin}>
                        <TextField
                            label="Username"
                            fullWidth
                            margin="normal"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                        />
                        <TextField
                            label="Password"
                            type="password"
                            fullWidth
                            margin="normal"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                        {loginError && <Typography color="error" variant="caption">{loginError}</Typography>}
                        <Button type="submit" variant="contained" fullWidth sx={{ mt: 2 }}>Login</Button>
                    </form>
                </Paper>
            </Box>
        );
    }

    return (
        <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', bgcolor: '#fff' }}>
            <Box p={2} bgcolor="primary.main" color="white" display="flex" justifyContent="space-between" alignItems="center">
                <Typography variant="h6">Employee Assistant 🤖</Typography>
                <Button color="inherit" onClick={handleLogout}>Logout</Button>
            </Box>

            <Box sx={{ flexGrow: 1, p: 2, overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
                <List>
                    {messages.map((msg) => (
                        <ListItem key={msg.id} sx={{ justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start' }}>
                            <Paper
                                elevation={1}
                                sx={{
                                    p: 2,
                                    maxWidth: '80%',
                                    bgcolor: msg.sender === 'user' ? 'primary.light' : 'grey.100',
                                    color: msg.sender === 'user' ? 'white' : 'text.primary',
                                    borderRadius: 2
                                }}
                            >
                                <Typography variant="body1" style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</Typography>
                                {msg.file && (
                                    <Box mt={1} p={1} bgcolor="rgba(0,0,0,0.1)" borderRadius={1}>
                                        <Typography variant="caption">📎 Attached: {msg.file}</Typography>
                                    </Box>
                                )}
                            </Paper>
                        </ListItem>
                    ))}
                    <div ref={messagesEndRef} />
                </List>
            </Box>

            <Paper elevation={3} sx={{ p: 2, display: 'flex', alignItems: 'center' }}>
                <input
                    type="file"
                    hidden
                    ref={fileInputRef}
                    onChange={handleFileSelect}
                />
                <IconButton color={selectedFile ? "secondary" : "default"} onClick={() => fileInputRef.current.click()}>
                    <AttachFileIcon />
                </IconButton>

                {selectedFile && (
                    <Typography variant="caption" sx={{ mr: 1, maxWidth: 100, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {selectedFile.name}
                    </Typography>
                )}

                <TextField
                    fullWidth
                    variant="outlined"
                    placeholder="Type a message..."
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    disabled={loading}
                    size="small"
                    sx={{ mx: 1 }}
                />

                <IconButton color="primary" onClick={handleSend} disabled={loading || (!inputText && !selectedFile)}>
                    <SendIcon />
                </IconButton>
            </Paper>
        </Box>
    );
}

export default App;
