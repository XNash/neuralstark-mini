import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

function App() {
  const [currentPage, setCurrentPage] = useState('chat');
  const [apiKey, setApiKey] = useState('');
  const [apiKeySaved, setApiKeySaved] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const [docStatus, setDocStatus] = useState(null);
  const messagesEndRef = useRef(null);

  // Generate session ID on mount
  useEffect(() => {
    const newSessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substring(7);
    setSessionId(newSessionId);
    loadSettings();
    loadDocumentStatus();
  }, []);

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadSettings = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/settings`);
      const data = await response.json();
      if (data.gemini_api_key) {
        setApiKey(data.gemini_api_key);
        setApiKeySaved(true);
      }
    } catch (error) {
      console.error('Error loading settings:', error);
    }
  };

  const loadDocumentStatus = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/documents/status`);
      const data = await response.json();
      setDocStatus(data);
    } catch (error) {
      console.error('Error loading document status:', error);
    }
  };

  const saveSettings = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/settings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ gemini_api_key: apiKey }),
      });

      if (response.ok) {
        setApiKeySaved(true);
        alert('API key saved successfully!');
      } else {
        alert('Failed to save API key');
      }
    } catch (error) {
      console.error('Error saving settings:', error);
      alert('Error saving API key');
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    if (!apiKeySaved) {
      alert('Please configure your Gemini API key in Settings first');
      setCurrentPage('settings');
      return;
    }

    const userMessage = { role: 'user', content: inputMessage };
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await fetch(`${BACKEND_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputMessage,
          session_id: sessionId,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        const assistantMessage = {
          role: 'assistant',
          content: data.response,
          sources: data.sources,
        };
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        setMessages(prev => [
          ...prev,
          {
            role: 'assistant',
            content: `Error: ${data.detail || 'Failed to get response'}`,
            isError: true,
          },
        ]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: 'Error: Failed to communicate with the server',
          isError: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const reindexDocuments = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/documents/reindex`, {
        method: 'POST',
      });
      if (response.ok) {
        alert('Document reindexing started. This may take a few moments.');
        setTimeout(loadDocumentStatus, 2000);
      }
    } catch (error) {
      console.error('Error reindexing:', error);
    }
  };

  const newChat = () => {
    setMessages([]);
    const newSessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substring(7);
    setSessionId(newSessionId);
  };

  return (
    <div className="app">
      {/* Navigation */}
      <nav className="navbar">
        <div className="navbar-brand">
          <h1>🤖 RAG Platform</h1>
        </div>
        <div className="navbar-menu">
          <button
            className={`nav-button ${currentPage === 'chat' ? 'active' : ''}`}
            onClick={() => setCurrentPage('chat')}
          >
            💬 Chat
          </button>
          <button
            className={`nav-button ${currentPage === 'settings' ? 'active' : ''}`}
            onClick={() => setCurrentPage('settings')}
          >
            ⚙️ Settings
          </button>
        </div>
      </nav>

      {/* Main Content */}
      <div className="main-content">
        {currentPage === 'chat' ? (
          <div className="chat-page">
            <div className="chat-header">
              <div className="header-info">
                <h2>Chat with AI Agent</h2>
                {docStatus && (
                  <p className="doc-status">
                    📚 {docStatus.indexed_documents} documents indexed
                  </p>
                )}
              </div>
              <button className="new-chat-button" onClick={newChat}>
                ✨ New Chat
              </button>
            </div>

            <div className="chat-container">
              <div className="messages">
                {messages.length === 0 && (
                  <div className="welcome-message">
                    <h3>👋 Welcome to RAG Platform</h3>
                    <p>Ask me anything about your indexed documents!</p>
                    <div className="info-box">
                      <p>💡 I can answer questions based on:</p>
                      <ul>
                        <li>PDF files (with OCR support)</li>
                        <li>Word documents (.doc, .docx)</li>
                        <li>Excel spreadsheets (.xls, .xlsx)</li>
                        <li>OpenDocument files (.odt)</li>
                        <li>Text and Markdown files</li>
                        <li>JSON and CSV data</li>
                      </ul>
                      <p className="note">📁 Add files to <code>/app/files</code> directory</p>
                    </div>
                  </div>
                )}

                {messages.map((msg, index) => (
                  <div key={index} className={`message ${msg.role}`}>
                    <div className="message-header">
                      <span className="message-icon">
                        {msg.role === 'user' ? '👤' : '🤖'}
                      </span>
                      <span className="message-role">
                        {msg.role === 'user' ? 'You' : 'AI Assistant'}
                      </span>
                    </div>
                    <div className={`message-content ${msg.isError ? 'error' : ''}`}>
                      {msg.content}
                    </div>
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="message-sources">
                        <p className="sources-title">📄 Sources:</p>
                        {msg.sources.map((source, idx) => (
                          <div key={idx} className="source-item">
                            <span className="source-name">{source.source}</span>
                            <span className="source-score">
                              {Math.round(source.relevance_score * 100)}% relevant
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}

                {isLoading && (
                  <div className="message assistant">
                    <div className="message-header">
                      <span className="message-icon">🤖</span>
                      <span className="message-role">AI Assistant</span>
                    </div>
                    <div className="message-content loading">
                      <div className="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              <div className="input-container">
                <textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask a question about your documents..."
                  rows="3"
                  disabled={isLoading}
                />
                <button
                  onClick={sendMessage}
                  disabled={isLoading || !inputMessage.trim()}
                  className="send-button"
                >
                  {isLoading ? '⏳' : '🚀'} Send
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="settings-page">
            <div className="settings-container">
              <h2>⚙️ Settings</h2>

              <div className="settings-section">
                <h3>🔑 Gemini API Key</h3>
                <p className="settings-description">
                  Configure your Google Gemini API key to enable AI-powered responses.
                  The platform uses <strong>gemini-2.5-flash</strong> model.
                </p>
                <div className="input-group">
                  <input
                    type="password"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="Enter your Gemini API key"
                    className="api-key-input"
                  />
                  <button onClick={saveSettings} className="save-button">
                    💾 Save
                  </button>
                </div>
                {apiKeySaved && (
                  <p className="success-message">✅ API key is configured</p>
                )}
                <div className="help-box">
                  <p><strong>Where to get API key?</strong></p>
                  <p>Get your free API key from: <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer">Google AI Studio</a></p>
                </div>
              </div>

              <div className="settings-section">
                <h3>📚 Document Status</h3>
                {docStatus ? (
                  <div className="status-info">
                    <div className="status-item">
                      <span className="status-label">Total Documents:</span>
                      <span className="status-value">{docStatus.total_documents}</span>
                    </div>
                    <div className="status-item">
                      <span className="status-label">Indexed Chunks:</span>
                      <span className="status-value">{docStatus.indexed_documents}</span>
                    </div>
                    {docStatus.last_updated && (
                      <div className="status-item">
                        <span className="status-label">Last Updated:</span>
                        <span className="status-value">
                          {new Date(docStatus.last_updated).toLocaleString()}
                        </span>
                      </div>
                    )}
                  </div>
                ) : (
                  <p>Loading document status...</p>
                )}
                <button onClick={reindexDocuments} className="reindex-button">
                  🔄 Reindex Documents
                </button>
              </div>

              <div className="settings-section">
                <h3>📁 File Management</h3>
                <p className="settings-description">
                  Documents are automatically indexed from: <code>/app/files</code>
                </p>
                <div className="supported-formats">
                  <p><strong>Supported Formats:</strong></p>
                  <ul>
                    <li>📄 PDF (with OCR for scanned documents)</li>
                    <li>📝 Word: .doc, .docx (with image OCR)</li>
                    <li>📊 Excel: .xls, .xlsx</li>
                    <li>📃 OpenDocument: .odt</li>
                    <li>📋 Text: .txt, .md (Markdown)</li>
                    <li>💾 Data: .json, .csv</li>
                  </ul>
                </div>
              </div>

              <div className="settings-section">
                <h3>🌐 Language Support</h3>
                <p className="settings-description">
                  The platform supports multilingual documents with BAAI/bge-base-en-v1.5 embeddings.
                  Optimized for English and French content.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;