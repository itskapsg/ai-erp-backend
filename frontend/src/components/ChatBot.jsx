/**
 * ChatBot - Voice-First AI Assistant Component
 * Integrates with backend chat API for natural language processing
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  Box,
  TextField,
  IconButton,
  Typography,
  Paper,
  Chip,
  CircularProgress,
  Fab,
  Slide,
  Alert,
  Divider
} from '@mui/material';
import {
  Send,
  Mic,
  MicOff,
  Close,
  SmartToy,
  Person,
  VolumeUp
} from '@mui/icons-material';
import api from '../services/api';

const Transition = React.forwardRef(function Transition(props, ref) {
  return <Slide direction="up" ref={ref} {...props} />;
});

const ChatBot = ({ open, onClose }) => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      content: 'Hi! I\'m your AI assistant. You can ask me about pending approvals, partners, or say "help" to see what I can do.',
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [error, setError] = useState(null);
  
  const messagesEndRef = useRef(null);
  const recognition = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Initialize speech recognition
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognition.current = new SpeechRecognition();
      recognition.current.continuous = false;
      recognition.current.interimResults = false;
      recognition.current.lang = 'en-US';

      recognition.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInputMessage(transcript);
        setIsListening(false);
      };

      recognition.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
        setError('Speech recognition failed. Please try typing instead.');
      };

      recognition.current.onend = () => {
        setIsListening(false);
      };
    }
  }, []);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.post('/chat/', {
        message: userMessage.content
      });

      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: response.data.response,
        intent: response.data.intent,
        count: response.data.count,
        data: response.data.data,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Chat API error:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
      setError('Failed to connect to AI assistant. Please check your connection.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  const startListening = () => {
    if (recognition.current && !isListening) {
      setIsListening(true);
      setError(null);
      recognition.current.start();
    }
  };

  const stopListening = () => {
    if (recognition.current && isListening) {
      recognition.current.stop();
      setIsListening(false);
    }
  };

  const speakMessage = (text) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9;
      utterance.pitch = 1;
      speechSynthesis.speak(utterance);
    }
  };

  const quickCommands = [
    'Show pending approvals',
    'List partners',
    'Help',
    'What needs approval?'
  ];

  const handleQuickCommand = (command) => {
    setInputMessage(command);
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      TransitionComponent={Transition}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          height: '80vh',
          maxHeight: '600px',
          display: 'flex',
          flexDirection: 'column'
        }
      }}
    >
      <DialogTitle sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        pb: 1
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <SmartToy color="primary" />
          <Typography variant="h6">AI Assistant</Typography>
          <Chip 
            label="Voice-First" 
            size="small" 
            color="secondary" 
            variant="outlined"
          />
        </Box>
        <IconButton onClick={onClose} size="small">
          <Close />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ 
        flex: 1, 
        display: 'flex', 
        flexDirection: 'column',
        p: 0
      }}>
        {/* Error Alert */}
        {error && (
          <Alert severity="error" sx={{ m: 2, mb: 1 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Quick Commands */}
        <Box sx={{ p: 2, pb: 1 }}>
          <Typography variant="caption" color="text.secondary" gutterBottom>
            Quick Commands:
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 1 }}>
            {quickCommands.map((command, index) => (
              <Chip
                key={index}
                label={command}
                size="small"
                variant="outlined"
                clickable
                onClick={() => handleQuickCommand(command)}
                sx={{ fontSize: '0.75rem' }}
              />
            ))}
          </Box>
        </Box>

        <Divider />

        {/* Messages */}
        <Box sx={{ 
          flex: 1, 
          overflowY: 'auto', 
          p: 2,
          display: 'flex',
          flexDirection: 'column',
          gap: 2
        }}>
          {messages.map((message) => (
            <Box
              key={message.id}
              sx={{
                display: 'flex',
                justifyContent: message.type === 'user' ? 'flex-end' : 'flex-start',
                alignItems: 'flex-start',
                gap: 1
              }}
            >
              {message.type === 'bot' && (
                <SmartToy 
                  sx={{ 
                    color: 'primary.main', 
                    mt: 0.5,
                    fontSize: '1.2rem'
                  }} 
                />
              )}
              
              <Paper
                elevation={1}
                sx={{
                  p: 2,
                  maxWidth: '80%',
                  backgroundColor: message.type === 'user' 
                    ? 'primary.main' 
                    : 'grey.100',
                  color: message.type === 'user' 
                    ? 'primary.contrastText' 
                    : 'text.primary',
                  borderRadius: 2,
                  position: 'relative'
                }}
              >
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                  {message.content}
                </Typography>
                
                {/* Bot message metadata */}
                {message.type === 'bot' && message.intent && (
                  <Box sx={{ mt: 1, display: 'flex', gap: 1, alignItems: 'center' }}>
                    <Chip 
                      label={message.intent} 
                      size="small" 
                      variant="outlined"
                      sx={{ fontSize: '0.7rem', height: '20px' }}
                    />
                    {message.count > 0 && (
                      <Chip 
                        label={`${message.count} items`} 
                        size="small" 
                        color="info"
                        sx={{ fontSize: '0.7rem', height: '20px' }}
                      />
                    )}
                    <IconButton 
                      size="small" 
                      onClick={() => speakMessage(message.content)}
                      sx={{ ml: 'auto', p: 0.5 }}
                    >
                      <VolumeUp sx={{ fontSize: '1rem' }} />
                    </IconButton>
                  </Box>
                )}
                
                <Typography 
                  variant="caption" 
                  sx={{ 
                    display: 'block', 
                    mt: 1, 
                    opacity: 0.7,
                    fontSize: '0.7rem'
                  }}
                >
                  {message.timestamp.toLocaleTimeString()}
                </Typography>
              </Paper>
              
              {message.type === 'user' && (
                <Person 
                  sx={{ 
                    color: 'text.secondary', 
                    mt: 0.5,
                    fontSize: '1.2rem'
                  }} 
                />
              )}
            </Box>
          ))}
          
          {/* Loading indicator */}
          {isLoading && (
            <Box sx={{ display: 'flex', justifyContent: 'flex-start', alignItems: 'center', gap: 1 }}>
              <SmartToy sx={{ color: 'primary.main', fontSize: '1.2rem' }} />
              <Paper elevation={1} sx={{ p: 2, borderRadius: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CircularProgress size={16} />
                  <Typography variant="body2" color="text.secondary">
                    Thinking...
                  </Typography>
                </Box>
              </Paper>
            </Box>
          )}
          
          <div ref={messagesEndRef} />
        </Box>

        {/* Input Area */}
        <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
            <TextField
              fullWidth
              multiline
              maxRows={3}
              placeholder="Ask me about approvals, partners, or say 'help'..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
              variant="outlined"
              size="small"
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 3
                }
              }}
            />
            
            {/* Voice Input Button */}
            {recognition.current && (
              <IconButton
                color={isListening ? "secondary" : "default"}
                onClick={isListening ? stopListening : startListening}
                disabled={isLoading}
                sx={{ 
                  borderRadius: 2,
                  border: isListening ? 2 : 1,
                  borderColor: isListening ? 'secondary.main' : 'divider'
                }}
              >
                {isListening ? <MicOff /> : <Mic />}
              </IconButton>
            )}
            
            {/* Send Button */}
            <IconButton
              color="primary"
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isLoading}
              sx={{ borderRadius: 2 }}
            >
              <Send />
            </IconButton>
          </Box>
          
          {isListening && (
            <Typography 
              variant="caption" 
              color="secondary.main" 
              sx={{ display: 'block', mt: 1, textAlign: 'center' }}
            >
              🎤 Listening... Speak now
            </Typography>
          )}
        </Box>
      </DialogContent>
    </Dialog>
  );
};

export default ChatBot;