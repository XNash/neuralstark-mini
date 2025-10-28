import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
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
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [showTooltip, setShowTooltip] = useState(null);
  const [saveStatus, setSaveStatus] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

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
      title: 'Nouvelle Conversation',
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
      if (data.cerebras_api_key) {
        setApiKey(data.cerebras_api_key);
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
    if (!apiKey || apiKey.trim().length < 10) {
      setErrorMessage('Veuillez entrer une clé API valide (minimum 10 caractères)');
      setSaveStatus('error');
      setTimeout(() => {
        setErrorMessage('');
        setSaveStatus(null);
      }, 3000);
      return;
    }

    setSaveStatus('saving');
    try {
      const response = await fetch(`${BACKEND_URL}/api/settings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ cerebras_api_key: apiKey }),
      });

      if (response.ok) {
        setApiKeySaved(true);
        setSaveStatus('success');
        setErrorMessage('');
        setTimeout(() => setSaveStatus(null), 3000);
      } else {
        setSaveStatus('error');
        setErrorMessage('Échec de l\'enregistrement de la clé API. Veuillez réessayer.');
        setTimeout(() => {
          setSaveStatus(null);
          setErrorMessage('');
        }, 3000);
      }
    } catch (error) {
      console.error('Error saving settings:', error);
      setSaveStatus('error');
      setErrorMessage('Erreur réseau. Veuillez vérifier votre connexion.');
      setTimeout(() => {
        setSaveStatus(null);
        setErrorMessage('');
      }, 3000);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    if (!apiKeySaved) {
      setErrorMessage('⚠️ Veuillez configurer votre clé API Cerebras dans les Paramètres d\'abord');
      setTimeout(() => setErrorMessage(''), 4000);
      setCurrentPage('settings');
      return;
    }

    const userMessage = { role: 'user', content: inputMessage };
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    setErrorMessage('');

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
        const errorMsg = data.detail || 'Échec de l\'obtention de la réponse';
        setMessages(prev => [
          ...prev,
          {
            role: 'assistant',
            content: `❌ Erreur: ${errorMsg}`,
            isError: true,
          },
        ]);
        setErrorMessage(`Erreur: ${errorMsg}`);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMsg = 'Échec de la communication avec le serveur. Veuillez vérifier votre connexion.';
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `❌ ${errorMsg}`,
          isError: true,
        },
      ]);
      setErrorMessage(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
    // Ctrl+Enter for new line
    if (e.key === 'Enter' && e.ctrlKey) {
      setInputMessage(prev => prev + '\n');
    }
  };

  const reindexDocuments = async (fullReindex = false) => {
    setShowConfirmDialog(false);
    setSaveStatus('indexing');
    setErrorMessage('');
    
    try {
      const url = fullReindex 
        ? `${BACKEND_URL}/api/documents/reindex?clear_cache=true`
        : `${BACKEND_URL}/api/documents/reindex`;
        
      const response = await fetch(url, {
        method: 'POST',
      });
      
      if (response.ok) {
        setSaveStatus('success');
        setTimeout(() => {
          loadDocumentStatus();
          loadDocumentsList();
          setSaveStatus(null);
        }, 2000);
      } else {
        setSaveStatus('error');
        setErrorMessage('Échec du démarrage de la réindexation. Veuillez réessayer.');
        setTimeout(() => setSaveStatus(null), 3000);
      }
    } catch (error) {
      console.error('Error reindexing:', error);
      setSaveStatus('error');
      setErrorMessage('Erreur réseau lors de la réindexation.');
      setTimeout(() => setSaveStatus(null), 3000);
    }
  };

  const handleReindexClick = () => {
    setShowConfirmDialog(true);
  };

  const newChat = () => {
    setMessages([]);
    setErrorMessage('');
    const newSessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substring(7);
    setSessionId(newSessionId);
    
    // Add new session to history
    const newSession = {
      id: newSessionId,
      title: 'Nouvelle Conversation',
      timestamp: new Date().toISOString(),
      messageCount: 0
    };
    setChatHistory(prev => [newSession, ...prev]);
    
    // Focus input after new chat
    setTimeout(() => inputRef.current?.focus(), 100);
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
            <span className="brand-icon">🧠</span>
            {sidebarOpen && <h1 className="brand-title">Neuralstark AI</h1>}
          </div>
        </div>

        {sidebarOpen && (
          <>
            <button 
              className="new-chat-btn" 
              onClick={newChat}
              onMouseEnter={() => setShowTooltip('new-chat')}
              onMouseLeave={() => setShowTooltip(null)}
              title="Démarrer une nouvelle conversation (Ctrl+N)"
            >
              <span className="btn-icon">✨</span>
              <span>Nouvelle Discussion</span>
            </button>

            <nav className="sidebar-nav" role="navigation" aria-label="Navigation principale">
              <button
                className={`nav-item ${currentPage === 'chat' ? 'active' : ''}`}
                onClick={() => setCurrentPage('chat')}
                aria-current={currentPage === 'chat' ? 'page' : undefined}
                title="Aller à l'interface de discussion"
              >
                <span className="nav-icon">💬</span>
                <span className="nav-label">Discussion</span>
                {messages.length > 0 && <span className="nav-badge">{messages.length}</span>}
              </button>
              
              <button
                className={`nav-item ${currentPage === 'documents' ? 'active' : ''}`}
                onClick={() => setCurrentPage('documents')}
                aria-current={currentPage === 'documents' ? 'page' : undefined}
                title="Gérer vos documents"
              >
                <span className="nav-icon">📚</span>
                <span className="nav-label">Documents</span>
                {docStatus && <span className="nav-badge">{docStatus.total_documents}</span>}
              </button>

              <button
                className={`nav-item ${currentPage === 'settings' ? 'active' : ''}`}
                onClick={() => setCurrentPage('settings')}
                aria-current={currentPage === 'settings' ? 'page' : undefined}
                title="Configurer les paramètres"
              >
                <span className="nav-icon">⚙️</span>
                <span className="nav-label">Paramètres</span>
                {!apiKeySaved && <span className="nav-badge warning">!</span>}
              </button>
            </nav>

            <div className="sidebar-footer">
              <div className="doc-status-mini">
                <span className="status-icon">📊</span>
                <div className="status-text">
                  <p className="status-label">Documents Indexés</p>
                  <p className="status-value">
                    {docStatus ? `${docStatus.indexed_documents} fragments` : 'Chargement...'}
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
        <header className="top-header" role="banner">
          <button 
            className="menu-toggle" 
            onClick={toggleSidebar}
            aria-label={sidebarOpen ? 'Fermer la barre latérale' : 'Ouvrir la barre latérale'}
            title={sidebarOpen ? 'Fermer la barre latérale' : 'Ouvrir la barre latérale'}
          >
            <span className="hamburger"></span>
          </button>
          
          <div className="header-info">
            <h2 className="page-title">
              {currentPage === 'chat' && '💬 Discussion'}
              {currentPage === 'documents' && '📚 Documents'}
              {currentPage === 'settings' && '⚙️ Paramètres'}
            </h2>
            {currentPage === 'chat' && docStatus && (
              <p className="header-subtitle" aria-label="Statut des documents">
                {docStatus.total_documents} documents • {docStatus.indexed_documents} fragments indexés
              </p>
            )}
          </div>

          <div className="header-actions">
            {apiKeySaved && <span className="status-badge success" title="Clé API configurée">✓ API Configurée</span>}
            {!apiKeySaved && <span className="status-badge warning" title="Clé API requise">⚠ Clé API Requise</span>}
          </div>
        </header>

        {/* Global Error Message */}
        {errorMessage && (
          <div className="global-error" role="alert">
            <span className="error-icon">⚠️</span>
            <span className="error-text">{errorMessage}</span>
            <button 
              className="error-close" 
              onClick={() => setErrorMessage('')}
              aria-label="Fermer le message d'erreur"
            >
              ✕
            </button>
          </div>
        )}

        {/* Page Content */}
        <div className="page-content">
          {currentPage === 'chat' && (
            <div className="chat-container">
              <div className="messages-area">
                {messages.length === 0 && (
                  <div className="welcome-screen">
                    <div className="welcome-icon">🧠</div>
                    <h2 className="welcome-title">Bienvenue sur Neuralstark AI</h2>
                    <p className="welcome-subtitle">
                      Commencez une conversation avec vos documents
                    </p>
                    
                    <div className="feature-grid">
                      <div className="feature-card">
                        <span className="feature-icon">📄</span>
                        <h3>Support PDF</h3>
                        <p>Traitement de documents avec OCR</p>
                      </div>
                      <div className="feature-card">
                        <span className="feature-icon">🌐</span>
                        <h3>Multilingue</h3>
                        <p>Optimisé pour anglais et français</p>
                      </div>
                      <div className="feature-card">
                        <span className="feature-icon">🔍</span>
                        <h3>Recherche Intelligente</h3>
                        <p>Récupération basée sur les vecteurs</p>
                      </div>
                      <div className="feature-card">
                        <span className="feature-icon">💡</span>
                        <h3>Propulsé par IA</h3>
                        <p>Cerebras Llama 3.3 70B</p>
                      </div>
                    </div>

                    <div className="quick-tips">
                      <h4>Conseils Rapides:</h4>
                      <ul>
                        <li>Ajoutez des documents dans le répertoire <code>/app/files</code></li>
                        <li>Configurez votre clé API Cerebras dans les Paramètres</li>
                        <li>Posez des questions sur vos documents en langage naturel</li>
                      </ul>
                    </div>
                  </div>
                )}

                {messages.map((msg, index) => (
                  <div key={index} className={`message ${msg.role}`}>
                    <div className="message-avatar">
                      {msg.role === 'user' ? '👤' : '🧠'}
                    </div>
                    <div className="message-bubble">
                      <div className="message-header-info">
                        <span className="message-sender">
                          {msg.role === 'user' ? 'Vous' : 'Neuralstark AI'}
                        </span>
                        <span className="message-time">
                          {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                      <div className={`message-text ${msg.isError ? 'error' : ''}`}>
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                      {msg.sources && msg.sources.length > 0 && (
                        <div className="message-sources">
                          <p className="sources-title">📎 Sources</p>
                          <div className="sources-list">
                            {(() => {
                              // Group sources by name and calculate average relevance
                              const groupedSources = msg.sources.reduce((acc, source) => {
                                if (!acc[source.source]) {
                                  acc[source.source] = {
                                    name: source.source,
                                    scores: [],
                                    count: 0
                                  };
                                }
                                acc[source.source].scores.push(source.relevance_score);
                                acc[source.source].count++;
                                return acc;
                              }, {});

                              // Calculate average and create final array
                              const finalSources = Object.values(groupedSources).map(group => ({
                                name: group.name,
                                avgScore: group.scores.reduce((sum, score) => sum + score, 0) / group.count,
                                count: group.count
                              }));

                              return finalSources.map((source, idx) => (
                                <div key={idx} className="source-chip">
                                  <span className="source-name">
                                    {source.name}
                                    {source.count > 1 && <span className="source-count"> (×{source.count})</span>}
                                  </span>
                                  <span className="source-relevance">
                                    {Math.round(source.avgScore * 100)}%
                                  </span>
                                </div>
                              ));
                            })()}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                {isLoading && (
                  <div className="message assistant">
                    <div className="message-avatar">🧠</div>
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
                    ref={inputRef}
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Tapez votre message... (Entrée pour envoyer, Ctrl+Entrée pour nouvelle ligne)"
                    rows="1"
                    disabled={isLoading}
                    className="message-input"
                    aria-label="Saisie du message"
                    maxLength="2000"
                  />
                  <div className="input-actions">
                    <span className="char-count" aria-label="Nombre de caractères">
                      {inputMessage.length}/2000
                    </span>
                    <button
                      onClick={sendMessage}
                      disabled={isLoading || !inputMessage.trim()}
                      className="send-btn"
                      aria-label="Envoyer le message"
                      title="Envoyer le message (Entrée)"
                    >
                      <span className="send-icon">
                        {isLoading ? '⏳' : '📤'}
                      </span>
                    </button>
                  </div>
                </div>
                <div className="input-help">
                  <span className="help-text">💡 Astuce: Appuyez sur Entrée pour envoyer, Maj+Entrée pour nouvelle ligne</span>
                </div>
              </div>
            </div>
          )}

          {currentPage === 'documents' && (
            <div className="documents-page">
              <div className="page-header">
                <h2>Gestion des Documents</h2>
                <div className="header-actions-group">
                  <button 
                    className="btn-secondary" 
                    onClick={() => {
                      loadDocumentStatus();
                      loadDocumentsList();
                    }}
                    title="Actualiser la liste des documents"
                  >
                    <span className="btn-icon">🔄</span>
                    Actualiser
                  </button>
                  <button 
                    className="btn-primary" 
                    onClick={handleReindexClick}
                    disabled={saveStatus === 'indexing'}
                    title="Réindexer tous les documents"
                  >
                    <span className="btn-icon">
                      {saveStatus === 'indexing' ? '⏳' : '🔄'}
                    </span>
                    {saveStatus === 'indexing' ? 'Indexation...' : 'Réindexer les Documents'}
                  </button>
                </div>
              </div>

              {/* Confirmation Dialog */}
              {showConfirmDialog && (
                <div className="modal-overlay" onClick={() => setShowConfirmDialog(false)}>
                  <div className="modal-dialog" onClick={(e) => e.stopPropagation()} role="dialog" aria-labelledby="confirm-title">
                    <div className="modal-header">
                      <h3 id="confirm-title">Confirmer la Réindexation des Documents</h3>
                      <button 
                        className="modal-close" 
                        onClick={() => setShowConfirmDialog(false)}
                        aria-label="Fermer la boîte de dialogue"
                      >
                        ✕
                      </button>
                    </div>
                    <div className="modal-body">
                      <p>Choisissez l'option de réindexation:</p>
                      <div className="reindex-options">
                        <button 
                          className="option-btn"
                          onClick={() => reindexDocuments(false)}
                        >
                          <span className="option-icon">⚡</span>
                          <div className="option-content">
                            <strong>Réindexation Rapide</strong>
                            <small>Traiter uniquement les fichiers nouveaux ou modifiés</small>
                          </div>
                        </button>
                        <button 
                          className="option-btn"
                          onClick={() => reindexDocuments(true)}
                        >
                          <span className="option-icon">🔄</span>
                          <div className="option-content">
                            <strong>Réindexation Complète</strong>
                            <small>Retraiter tous les fichiers (plus lent)</small>
                          </div>
                        </button>
                      </div>
                    </div>
                    <div className="modal-footer">
                      <button 
                        className="btn-secondary" 
                        onClick={() => setShowConfirmDialog(false)}
                      >
                        Annuler
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {saveStatus === 'success' && (
                <div className="success-banner" role="status">
                  ✓ Documents réindexés avec succès!
                </div>
              )}

              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-icon">📚</div>
                  <div className="stat-content">
                    <p className="stat-label">Total des Documents</p>
                    <p className="stat-value">{docStatus?.total_documents || 0}</p>
                  </div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-icon">📊</div>
                  <div className="stat-content">
                    <p className="stat-label">Fragments Indexés</p>
                    <p className="stat-value">{docStatus?.indexed_documents || 0}</p>
                  </div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-icon">⏰</div>
                  <div className="stat-content">
                    <p className="stat-label">Dernière Mise à Jour</p>
                    <p className="stat-value">
                      {docStatus?.last_updated 
                        ? new Date(docStatus.last_updated).toLocaleDateString('fr-FR')
                        : 'Jamais'}
                    </p>
                  </div>
                </div>
              </div>

              <div className="info-section">
                <h3>Formats de Documents Supportés</h3>
                <div className="format-grid">
                  <div className="format-item">
                    <span className="format-icon">📄</span>
                    <span className="format-name">PDF</span>
                    <span className="format-desc">Avec support OCR</span>
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
                    <span className="format-name">Texte</span>
                    <span className="format-desc">.txt, .md</span>
                  </div>
                  <div className="format-item">
                    <span className="format-icon">💾</span>
                    <span className="format-name">Données</span>
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
                <h3>Comment Ajouter des Documents</h3>
                <div className="instructions-card">
                  <ol className="instructions-list">
                    <li>Placez vos documents dans le répertoire <code>/app/files</code></li>
                    <li>Le système surveille automatiquement les nouveaux fichiers</li>
                    <li>Les documents sont indexés en 5-10 secondes</li>
                    <li>Utilisez le bouton "Réindexer les Documents" pour déclencher manuellement l'indexation</li>
                  </ol>
                </div>
              </div>

              {documentsList.total_count > 0 && (
                <div className="info-section">
                  <h3>📁 Fichiers Indexés ({documentsList.total_count})</h3>
                  <div className="files-by-type">
                    {Object.entries(documentsList.documents_by_type).map(([category, files]) => (
                      <div key={category} className="file-category">
                        <h4 className="category-header">
                          {category === 'PDF' && '📄'}
                          {category === 'Word' && '📝'}
                          {category === 'Excel' && '📊'}
                          {category === 'Text' && '📋'}
                          {category === 'Data' && '💾'}
                          {category === 'OpenDocument' && '📃'}
                          {' '}{category} ({files.length})
                        </h4>
                        <div className="file-list">
                          {files.map((file, index) => (
                            <div key={index} className="file-item">
                              <div className="file-info">
                                <span className="file-name">{file.name}</span>
                                <span className="file-size">{file.size_formatted}</span>
                              </div>
                              <span className="file-extension">{file.extension}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {currentPage === 'settings' && (
            <div className="settings-page">
              <div className="settings-section">
                <div className="section-header">
                  <h3>🔑 Configuration de l'API</h3>
                  <p className="section-desc">Configurez votre clé API Google Gemini pour des réponses alimentées par l'IA</p>
                </div>
                <div className="settings-card">
                  <div className="form-group">
                    <label className="form-label" htmlFor="api-key-input">
                      Clé API Gemini
                      <span className="required-indicator" title="Champ requis">*</span>
                    </label>
                    <div className="input-with-button">
                      <input
                        id="api-key-input"
                        type="password"
                        value={apiKey}
                        onChange={(e) => {
                          setApiKey(e.target.value);
                          setErrorMessage('');
                        }}
                        placeholder="Entrez votre clé API (min. 10 caractères)..."
                        className={`form-input ${errorMessage && !apiKey ? 'input-error' : ''}`}
                        aria-required="true"
                        aria-invalid={errorMessage && !apiKey ? 'true' : 'false'}
                        aria-describedby="api-key-help"
                        minLength="10"
                      />
                      <button 
                        onClick={saveSettings} 
                        className="btn-primary"
                        disabled={saveStatus === 'saving'}
                      >
                        {saveStatus === 'saving' ? '⏳ Enregistrement...' : '💾 Enregistrer'}
                      </button>
                    </div>
                    {saveStatus === 'success' && (
                      <p className="form-help success" role="status">
                        ✓ Clé API enregistrée avec succès et fonctionne
                      </p>
                    )}
                    {saveStatus === 'error' && errorMessage && (
                      <p className="form-help error" role="alert">
                        ✕ {errorMessage}
                      </p>
                    )}
                    {apiKeySaved && !saveStatus && (
                      <p className="form-help success">
                        ✓ La clé API est configurée et fonctionne
                      </p>
                    )}
                    <p className="form-help" id="api-key-help">
                      Obtenez votre clé API gratuite depuis{' '}
                      <a 
                        href="https://aistudio.google.com/app/apikey" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="link"
                      >
                        Google AI Studio
                      </a>
                      . Votre clé est stockée en toute sécurité et n'est jamais partagée.
                    </p>
                  </div>
                </div>
              </div>

              <div className="settings-section">
                <div className="section-header">
                  <h3>🧠 Informations sur le Modèle</h3>
                  <p className="section-desc">Configuration actuelle du modèle d'IA</p>
                </div>
                <div className="settings-card">
                  <div className="info-grid">
                    <div className="info-item">
                      <span className="info-label">Modèle de Langage</span>
                      <span className="info-value">Gemini 2.5 Flash</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Modèle d'Embedding</span>
                      <span className="info-value">BAAI/bge-base-en-v1.5</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Base de Données Vectorielle</span>
                      <span className="info-value">ChromaDB</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Langues</span>
                      <span className="info-value">Anglais, Français</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="settings-section">
                <div className="section-header">
                  <h3>ℹ️ Informations Système</h3>
                  <p className="section-desc">Détails de la plateforme et version</p>
                </div>
                <div className="settings-card">
                  <div className="info-grid">
                    <div className="info-item">
                      <span className="info-label">Version de la Plateforme</span>
                      <span className="info-value">2.0.0</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">URL du Backend</span>
                      <span className="info-value">{BACKEND_URL || 'localhost:8001'}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Répertoire de Documents</span>
                      <span className="info-value">/app/files</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Auto-indexation</span>
                      <span className="info-value">Activée (intervalle de 5s)</span>
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