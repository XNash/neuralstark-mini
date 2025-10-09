import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

function App() {
  const [currentPage, setCurrentPage] = useState('chat');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [apiKey, setApiKey] = useState('');
  const [apiKeySaved, setApiKeySaved] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const [docStatus, setDocStatus] = useState(null);
  const [documentsList, setDocumentsList] = useState({ documents_by_type: {}, total_count: 0 });
  const [chatHistory, setChatHistory] = useState([]);
  const messagesEndRef = useRef(null);

  // Generate session ID on mount
  useEffect(() => {
    const newSessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substring(7);
    setSessionId(newSessionId);
    loadSettings();
    loadDocumentStatus();
    loadDocumentsList();
    
    // Add initial session to history
    setChatHistory([{
      id: newSessionId,
      title: 'New Conversation',
      timestamp: new Date().toISOString(),
      messageCount: 0
    }]);
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

  const loadDocumentsList = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/documents/list`);
      const data = await response.json();
      setDocumentsList(data);
    } catch (error) {
      console.error('Error loading documents list:', error);
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
        
        // Update chat history
        updateChatHistory();
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
        setTimeout(() => {
          loadDocumentStatus();
          loadDocumentsList();
        }, 2000);
      }
    } catch (error) {
      console.error('Error reindexing:', error);
    }
  };

  const newChat = () => {
    setMessages([]);
    const newSessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substring(7);
    setSessionId(newSessionId);
    
    // Add new session to history
    const newSession = {
      id: newSessionId,
      title: 'New Conversation',
      timestamp: new Date().toISOString(),
      messageCount: 0
    };
    setChatHistory(prev => [newSession, ...prev]);
  };

  const updateChatHistory = () => {
    setChatHistory(prev => prev.map(session => 
      session.id === sessionId 
        ? { ...session, messageCount: messages.length + 2 }
        : session
    ));
  };

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <div className="app">
      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <div className="brand">
            <span className="brand-icon">🤖</span>
            {sidebarOpen && <h1 className="brand-title">RAG Platform</h1>}
          </div>
        </div>

        {sidebarOpen && (
          <>
            <button className="new-chat-btn" onClick={newChat}>
              <span className="btn-icon">✨</span>
              <span>New Chat</span>
            </button>

            <nav className="sidebar-nav">
              <button
                className={`nav-item ${currentPage === 'chat' ? 'active' : ''}`}
                onClick={() => setCurrentPage('chat')}
              >
                <span className="nav-icon">💬</span>
                <span className="nav-label">Chat</span>
              </button>
              
              <button
                className={`nav-item ${currentPage === 'documents' ? 'active' : ''}`}
                onClick={() => setCurrentPage('documents')}
              >
                <span className="nav-icon">📚</span>
                <span className="nav-label">Documents</span>
              </button>

              <button
                className={`nav-item ${currentPage === 'settings' ? 'active' : ''}`}
                onClick={() => setCurrentPage('settings')}
              >
                <span className="nav-icon">⚙️</span>
                <span className="nav-label">Settings</span>
              </button>
            </nav>

            <div className="sidebar-footer">
              <div className="doc-status-mini">
                <span className="status-icon">📊</span>
                <div className="status-text">
                  <p className="status-label">Documents Indexed</p>
                  <p className="status-value">
                    {docStatus ? `${docStatus.indexed_documents} chunks` : 'Loading...'}
                  </p>
                </div>
              </div>
            </div>
          </>
        )}
      </aside>

      {/* Main Content */}
      <main className="main-container">
        {/* Header */}
        <header className="top-header">
          <button className="menu-toggle" onClick={toggleSidebar}>
            <span className="hamburger"></span>
          </button>
          
          <div className="header-info">
            <h2 className="page-title">
              {currentPage === 'chat' && '💬 Chat'}
              {currentPage === 'documents' && '📚 Documents'}
              {currentPage === 'settings' && '⚙️ Settings'}
            </h2>
            {currentPage === 'chat' && docStatus && (
              <p className="header-subtitle">
                {docStatus.total_documents} documents • {docStatus.indexed_documents} indexed chunks
              </p>
            )}
          </div>

          <div className="header-actions">
            {apiKeySaved && <span className="status-badge success">✓ API Configured</span>}
            {!apiKeySaved && <span className="status-badge warning">⚠ API Key Required</span>}
          </div>
        </header>

        {/* Page Content */}
        <div className="page-content">
          {currentPage === 'chat' && (
            <div className="chat-container">
              <div className="messages-area">
                {messages.length === 0 && (
                  <div className="welcome-screen">
                    <div className="welcome-icon">🤖</div>
                    <h2 className="welcome-title">Welcome to RAG Platform</h2>
                    <p className="welcome-subtitle">
                      Start a conversation with your documents
                    </p>
                    
                    <div className="feature-grid">
                      <div className="feature-card">
                        <span className="feature-icon">📄</span>
                        <h3>PDF Support</h3>
                        <p>OCR-enabled document processing</p>
                      </div>
                      <div className="feature-card">
                        <span className="feature-icon">🌐</span>
                        <h3>Multilingual</h3>
                        <p>English & French optimized</p>
                      </div>
                      <div className="feature-card">
                        <span className="feature-icon">🔍</span>
                        <h3>Smart Search</h3>
                        <p>Vector-based retrieval</p>
                      </div>
                      <div className="feature-card">
                        <span className="feature-icon">💡</span>
                        <h3>AI-Powered</h3>
                        <p>Gemini 2.5 Flash</p>
                      </div>
                    </div>

                    <div className="quick-tips">
                      <h4>Quick Tips:</h4>
                      <ul>
                        <li>Add documents to <code>/app/files</code> directory</li>
                        <li>Configure your Gemini API key in Settings</li>
                        <li>Ask questions about your documents in natural language</li>
                      </ul>
                    </div>
                  </div>
                )}

                {messages.map((msg, index) => (
                  <div key={index} className={`message ${msg.role}`}>
                    <div className="message-avatar">
                      {msg.role === 'user' ? '👤' : '🤖'}
                    </div>
                    <div className="message-bubble">
                      <div className="message-header-info">
                        <span className="message-sender">
                          {msg.role === 'user' ? 'You' : 'AI Assistant'}
                        </span>
                        <span className="message-time">
                          {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                      <div className={`message-text ${msg.isError ? 'error' : ''}`}>
                        {msg.content}
                      </div>
                      {msg.sources && msg.sources.length > 0 && (
                        <div className="message-sources">
                          <p className="sources-title">📎 Sources</p>
                          <div className="sources-list">
                            {msg.sources.map((source, idx) => (
                              <div key={idx} className="source-chip">
                                <span className="source-name">{source.source}</span>
                                <span className="source-relevance">
                                  {Math.round(source.relevance_score * 100)}%
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                {isLoading && (
                  <div className="message assistant">
                    <div className="message-avatar">🤖</div>
                    <div className="message-bubble loading">
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

              <div className="input-area">
                <div className="input-wrapper">
                  <textarea
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Type your message..."
                    rows="1"
                    disabled={isLoading}
                    className="message-input"
                  />
                  <button
                    onClick={sendMessage}
                    disabled={isLoading || !inputMessage.trim()}
                    className="send-btn"
                  >
                    <span className="send-icon">📤</span>
                  </button>
                </div>
              </div>
            </div>
          )}

          {currentPage === 'documents' && (
            <div className="documents-page">
              <div className="page-header">
                <h2>Document Management</h2>
                <button className="btn-primary" onClick={reindexDocuments}>
                  <span className="btn-icon">🔄</span>
                  Reindex Documents
                </button>
              </div>

              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-icon">📚</div>
                  <div className="stat-content">
                    <p className="stat-label">Total Documents</p>
                    <p className="stat-value">{docStatus?.total_documents || 0}</p>
                  </div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-icon">📊</div>
                  <div className="stat-content">
                    <p className="stat-label">Indexed Chunks</p>
                    <p className="stat-value">{docStatus?.indexed_documents || 0}</p>
                  </div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-icon">⏰</div>
                  <div className="stat-content">
                    <p className="stat-label">Last Updated</p>
                    <p className="stat-value">
                      {docStatus?.last_updated 
                        ? new Date(docStatus.last_updated).toLocaleDateString()
                        : 'Never'}
                    </p>
                  </div>
                </div>
              </div>

              <div className="info-section">
                <h3>Supported Document Formats</h3>
                <div className="format-grid">
                  <div className="format-item">
                    <span className="format-icon">📄</span>
                    <span className="format-name">PDF</span>
                    <span className="format-desc">With OCR support</span>
                  </div>
                  <div className="format-item">
                    <span className="format-icon">📝</span>
                    <span className="format-name">Word</span>
                    <span className="format-desc">.doc, .docx</span>
                  </div>
                  <div className="format-item">
                    <span className="format-icon">📊</span>
                    <span className="format-name">Excel</span>
                    <span className="format-desc">.xls, .xlsx</span>
                  </div>
                  <div className="format-item">
                    <span className="format-icon">📋</span>
                    <span className="format-name">Text</span>
                    <span className="format-desc">.txt, .md</span>
                  </div>
                  <div className="format-item">
                    <span className="format-icon">💾</span>
                    <span className="format-name">Data</span>
                    <span className="format-desc">.json, .csv</span>
                  </div>
                  <div className="format-item">
                    <span className="format-icon">📃</span>
                    <span className="format-name">ODT</span>
                    <span className="format-desc">OpenDocument</span>
                  </div>
                </div>
              </div>

              <div className="info-section">
                <h3>How to Add Documents</h3>
                <div className="instructions-card">
                  <ol className="instructions-list">
                    <li>Place your documents in the <code>/app/files</code> directory</li>
                    <li>The system automatically monitors for new files</li>
                    <li>Documents are indexed within 5-10 seconds</li>
                    <li>Use the "Reindex Documents" button to manually trigger indexing</li>
                  </ol>
                </div>
              </div>
            </div>
          )}

          {currentPage === 'settings' && (
            <div className="settings-page">
              <div className="settings-section">
                <div className="section-header">
                  <h3>🔑 API Configuration</h3>
                  <p className="section-desc">Configure your Google Gemini API key</p>
                </div>
                <div className="settings-card">
                  <div className="form-group">
                    <label className="form-label">Gemini API Key</label>
                    <div className="input-with-button">
                      <input
                        type="password"
                        value={apiKey}
                        onChange={(e) => setApiKey(e.target.value)}
                        placeholder="Enter your API key..."
                        className="form-input"
                      />
                      <button onClick={saveSettings} className="btn-primary">
                        Save
                      </button>
                    </div>
                    {apiKeySaved && (
                      <p className="form-help success">✓ API key is configured and working</p>
                    )}
                    <p className="form-help">
                      Get your free API key from{' '}
                      <a 
                        href="https://aistudio.google.com/app/apikey" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="link"
                      >
                        Google AI Studio
                      </a>
                    </p>
                  </div>
                </div>
              </div>

              <div className="settings-section">
                <div className="section-header">
                  <h3>🤖 Model Information</h3>
                  <p className="section-desc">Current AI model configuration</p>
                </div>
                <div className="settings-card">
                  <div className="info-grid">
                    <div className="info-item">
                      <span className="info-label">Language Model</span>
                      <span className="info-value">Gemini 2.5 Flash</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Embedding Model</span>
                      <span className="info-value">BAAI/bge-base-en-v1.5</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Vector Database</span>
                      <span className="info-value">ChromaDB</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Languages</span>
                      <span className="info-value">English, French</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="settings-section">
                <div className="section-header">
                  <h3>ℹ️ System Information</h3>
                  <p className="section-desc">Platform details and version</p>
                </div>
                <div className="settings-card">
                  <div className="info-grid">
                    <div className="info-item">
                      <span className="info-label">Platform Version</span>
                      <span className="info-value">2.0.0</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Backend URL</span>
                      <span className="info-value">{BACKEND_URL || 'localhost:8001'}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Document Directory</span>
                      <span className="info-value">/app/files</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Auto-indexing</span>
                      <span className="info-value">Enabled (5s interval)</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;