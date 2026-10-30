import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Undo2,
  Play,
  Settings,
  Key,
  Cpu,
  X
} from 'lucide-react';
import { getLLMProviders } from '../api';

export default function AIChatbotPanel({
  chatMessages,
  onSendCommand,
  isProcessing,
  onSelectSuggestion,
  onApplyProposal,
  onCancelProposal
}) {
  const [inputText, setInputText] = useState('');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [llmProvider, setLlmProvider] = useState(() => localStorage.getItem('editmind_llm_provider') || 'auto');
  const [geminiKey, setGeminiKey] = useState(() => localStorage.getItem('editmind_gemini_key') || '');
  const [openaiKey, setOpenaiKey] = useState(() => localStorage.getItem('editmind_openai_key') || '');
  const [availableProviders, setAvailableProviders] = useState(null);

  const messagesEndRef = useRef(null);

  useEffect(() => {
    async function loadProviders() {
      try {
        const info = await getLLMProviders();
        setAvailableProviders(info);
      } catch (e) {
        // ignore
      }
    }
    loadProviders();
  }, []);

  const handleSaveSettings = () => {
    localStorage.setItem('editmind_llm_provider', llmProvider);
    localStorage.setItem('editmind_gemini_key', geminiKey);
    localStorage.setItem('editmind_openai_key', openaiKey);
    setIsSettingsOpen(false);
  };

  const quickPrompts = [
    'Split the second clip in half',
    'Remove the first 4 seconds',
    'Delete the selected segment',
    'Speed up clip 1 to 1.5x',
    'Mute audio',
    'Select clip from 00:10 to 00:25',
    'Jump to scene 2',
    'Export the edited video'
  ];

  const handleSend = (e) => {
    e?.preventDefault();
    if (!inputText.trim() || isProcessing) return;

    const config = {
      provider: llmProvider,
      api_key: geminiKey.trim() || undefined,
      openai_api_key: openaiKey.trim() || undefined
    };

    onSendCommand(inputText.trim(), config);
    setInputText('');
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const activeBadgeLabel =
    llmProvider === 'gemini' && geminiKey
      ? 'Gemini Flash'
      : llmProvider === 'openai' && openaiKey
      ? 'OpenAI/Groq'
      : availableProviders?.ollama_ready
      ? `Ollama (${availableProviders.ollama_models?.[0] || 'Local'})`
      : 'Smart Semantic AI';

  return (
    <div className="h-full flex flex-col bg-[#141518] text-[#a0a4ae] select-none text-[11px] relative">
      {/* 1. Header with LLM indicator & settings */}
      <div className="h-7 px-3 border-b border-[#212328] flex items-center justify-between bg-[#18191d] text-[10px]">
        <div className="flex items-center gap-1.5 text-[#d0d3dc] font-medium">
          <Sparkles className="w-3 h-3 text-[#d48b3b]" />
          <span>EditMind Assistant</span>
        </div>

        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setIsSettingsOpen(!isSettingsOpen)}
            className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-[#1e2026] hover:bg-[#282a32] text-[#868a96] hover:text-[#d0d3dc] border border-[#2b2d35] transition"
            title="Configure LLM Provider (Gemini / OpenAI / Ollama / Semantic)"
          >
            <Cpu className="w-2.5 h-2.5 text-[#7ea5dc]" />
            <span className="text-[9px] font-mono">{activeBadgeLabel}</span>
            <Settings className="w-2.5 h-2.5 ml-0.5" />
          </button>
        </div>
      </div>

      {/* LLM Configuration Popover Modal */}
      {isSettingsOpen && (
        <div className="absolute top-8 inset-x-2 bg-[#18191e] border border-[#2e313c] rounded-lg shadow-2xl p-3 z-40 space-y-2.5 text-[11px]">
          <div className="flex items-center justify-between border-b border-[#24262f] pb-1.5">
            <span className="font-semibold text-[#d8dbe4] flex items-center gap-1.5">
              <Sparkles className="w-3 h-3 text-[#d48b3b]" />
              <span>LLM Engine Settings</span>
            </span>
            <button
              onClick={() => setIsSettingsOpen(false)}
              className="text-[#6c707d] hover:text-white"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-2">
            <div>
              <label className="block text-[10px] text-[#868a96] mb-1">Provider:</label>
              <select
                value={llmProvider}
                onChange={(e) => setLlmProvider(e.target.value)}
                className="w-full bg-[#121316] text-[#d8dbe4] border border-[#272932] rounded px-2 py-1 text-[11px] focus:outline-none"
              >
                <option value="auto">Smart Semantic Reasoner (Fast & Local)</option>
                <option value="gemini">Google Gemini (Gemini 1.5/2.0 Flash)</option>
                <option value="openai">OpenAI / Groq API</option>
                <option value="ollama">Ollama Local ({availableProviders?.ollama_models?.[0] || 'Auto-detect'})</option>
              </select>
            </div>

            {llmProvider === 'gemini' && (
              <div>
                <label className="block text-[10px] text-[#868a96] mb-1">
                  Gemini API Key:
                </label>
                <input
                  type="password"
                  value={geminiKey}
                  onChange={(e) => setGeminiKey(e.target.value)}
                  placeholder="Paste Google AI Studio API Key..."
                  className="w-full bg-[#121316] text-[#d8dbe4] border border-[#272932] rounded px-2 py-1 text-[10px] focus:outline-none"
                />
              </div>
            )}

            {llmProvider === 'openai' && (
              <div>
                <label className="block text-[10px] text-[#868a96] mb-1">
                  OpenAI or Groq API Key:
                </label>
                <input
                  type="password"
                  value={openaiKey}
                  onChange={(e) => setOpenaiKey(e.target.value)}
                  placeholder="Paste gsk_ or sk- key..."
                  className="w-full bg-[#121316] text-[#d8dbe4] border border-[#272932] rounded px-2 py-1 text-[10px] focus:outline-none"
                />
              </div>
            )}
          </div>

          <div className="flex items-center justify-end gap-2 pt-1 border-t border-[#24262f]">
            <button
              onClick={() => setIsSettingsOpen(false)}
              className="px-2.5 py-1 rounded bg-[#202227] hover:bg-[#282a30] text-[#9da1ad] text-[10px]"
            >
              Cancel
            </button>
            <button
              onClick={handleSaveSettings}
              className="px-3 py-1 rounded bg-[#2b3a4e] hover:bg-[#344863] text-[#e0e3eb] font-medium text-[10px] border border-[#3f5778]"
            >
              Save Engine
            </button>
          </div>
        </div>
      )}

      {/* 2. Chat Log Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2.5">
        {chatMessages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-[90%] rounded p-2 text-[11px] leading-relaxed ${
                msg.sender === 'user'
                  ? 'bg-[#272932] text-[#e0e3eb] border border-[#373a46]'
                  : msg.isError
                  ? 'bg-[#251b1d] border border-[#442327] text-[#e28b8b]'
                  : 'bg-[#1a1b20] border border-[#262830] text-[#b5b9c4]'
              }`}
            >
              {/* Header */}
              <div className="flex items-center gap-1.5 mb-1 text-[9px] text-[#6b707e]">
                <span className="font-semibold text-[#8b90a0]">
                  {msg.sender === 'assistant' ? 'EditMind AI' : 'Editor'}
                </span>
                <span>• {msg.timestamp}</span>
              </div>

              {/* Message text */}
              <p className="whitespace-pre-wrap">{msg.text}</p>

              {/* Action Proposal Card */}
              {msg.actionProposal && (
                <div className="mt-2 pt-1.5 border-t border-[#2d303a] bg-[#141519] p-2 rounded border border-[#242630] space-y-1.5">
                  <div className="flex items-center justify-between text-[10px] text-[#d0d3dc] font-medium">
                    <span className="flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3 text-[#3b9a55]" />
                      <span>{msg.actionProposal.title || 'Proposed Timeline Edit'}</span>
                    </span>
                  </div>
                  {msg.actionProposal.details && (
                    <p className="text-[10px] text-[#8a8f9e]">
                      {msg.actionProposal.details}
                    </p>
                  )}
                </div>
              )}

              {/* Action Description notification */}
              {msg.actionDescription && !msg.actionProposal && (
                <div className="mt-1.5 pt-1 border-t border-[#262832] flex items-center gap-1 text-[10px] text-[#5bb676] font-mono">
                  <CheckCircle2 className="w-3 h-3" />
                  <span>{msg.actionDescription}</span>
                </div>
              )}
            </div>
          </div>
        ))}

        {isProcessing && (
          <div className="text-[10px] text-[#717582] italic bg-[#1a1b20] px-2 py-1.5 rounded border border-[#24262f] w-fit flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#d48b3b] animate-ping" />
            <span>Reasoning and executing edit...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 3. Suggested Prompt Chips */}
      <div className="px-2.5 py-1.5 border-t border-[#1f2025] bg-[#121316]">
        <div className="flex gap-1 overflow-x-auto pb-1 scrollbar-thin">
          {quickPrompts.map((cmd, idx) => (
            <button
              key={idx}
              onClick={() => onSelectSuggestion(cmd)}
              className="text-[10px] whitespace-nowrap bg-[#1a1b20] hover:bg-[#252730] text-[#868a96] hover:text-[#d0d3dc] border border-[#272932] px-2 py-0.5 rounded transition shrink-0"
            >
              {cmd}
            </button>
          ))}
        </div>
      </div>

      {/* 4. Natural-Language Input Box */}
      <form onSubmit={handleSend} className="p-2 border-t border-[#212328] bg-[#16171b] flex items-center gap-1.5">
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder='e.g. "Split second clip in half", "Remove the first 4s"...'
          disabled={isProcessing}
          className="flex-1 bg-[#1a1c22] text-[11px] text-[#d8dbe4] placeholder-[#555a66] rounded px-2.5 py-1.5 border border-[#282b34] focus:outline-none focus:border-[#424653] transition"
        />
        <button
          type="submit"
          disabled={!inputText.trim() || isProcessing}
          className="px-2.5 py-1.5 bg-[#252830] hover:bg-[#323642] disabled:opacity-30 text-[#e0e3eb] rounded border border-[#343844] transition flex items-center justify-center"
          title="Send command"
        >
          <Send className="w-3 h-3" />
        </button>
      </form>
    </div>
  );
}
