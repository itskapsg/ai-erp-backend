
import React, { useState, useRef, useEffect } from 'react';
import {
    Box,
    Paper,
    TextField,
    IconButton,
    Typography,
    List,
    ListItem,
    ListItemText,
    Avatar,
    CircularProgress,
    Button
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PersonIcon from '@mui/icons-material/Person';

const EmployeeAssistant = () => {
    const [messages, setMessages] = useState([
        { id: 1, text: "Hello! I am your AI Assistant. You can ask me questions or upload documents (invoices, receipts) for processing.", sender: 'bot' }
    ]);
    const [inputText, setInputText] = useState('');
    const [selectedFile, setSelectedFile] = useState(null);
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);
    const fileInputRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

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

        // Prepare FormData
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
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: formData
            });

            if (!response.ok) {
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

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <Box sx={{ height: 'calc(100vh - 100px)', display: 'flex', flexDirection: 'column', p: 2 }}>
            <Typography variant="h4" gutterBottom>
                Employee Assistant 🤖
            </Typography>

            <Paper elevation={3} sx={{ flexGrow: 1, mb: 2, p: 2, overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
                <List>
                    {messages.map((msg) => (
                        <ListItem key={msg.id} sx={{ justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start' }}>
                            <Paper
                                elevation={1}
                                sx={{
                                    p: 2,
                                    maxWidth: '70%',
                                    bgcolor: msg.sender === 'user' ? 'primary.light' : 'grey.100',
                                    color: msg.sender === 'user' ? 'white' : 'text.primary',
                                    borderRadius: 2
                                }}
                            >
                                <Box display="flex" alignItems="center" mb={1}>
                                    <Avatar sx={{ width: 24, height: 24, mr: 1, bgcolor: msg.sender === 'user' ? 'secondary.main' : 'primary.main' }}>
                                        {msg.sender === 'user' ? <PersonIcon fontSize="small" /> : <SmartToyIcon fontSize="small" />}
                                    </Avatar>
                                    <Typography variant="subtitle2" fontWeight="bold">
                                        {msg.sender === 'user' ? 'You' : 'Assistant'}
                                    </Typography>
                                </Box>
                                <Typography variant="body1" style={{ whiteSpace: 'pre-wrap' }}>
                                    {msg.text}
                                </Typography>
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
            </Paper>

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
                    onKeyPress={handleKeyPress}
                    disabled={loading}
                    multiline
                    maxRows={4}
                    sx={{ mx: 1 }}
                />

                <Box position="relative">
                    <IconButton color="primary" onClick={handleSend} disabled={loading || (!inputText && !selectedFile)}>
                        <SendIcon />
                    </IconButton>
                    {loading && (
                        <CircularProgress
                            size={24}
                            sx={{
                                position: 'absolute',
                                top: '50%',
                                left: '50%',
                                marginTop: '-12px',
                                marginLeft: '-12px',
                            }}
                        />
                    )}
                </Box>
            </Paper>
        </Box>
    );
};

export default EmployeeAssistant;
