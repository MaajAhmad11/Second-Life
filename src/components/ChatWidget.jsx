import React, { useEffect, useRef, useState } from 'react';

import api from '../services/api';

import {
  Bot,
  X,
  Send,
  User,
  RotateCcw,
  Sparkles
} from 'lucide-react';

const INITIAL_MESSAGE = {
  id: 'welcome-message',
  sender: 'bot',
  text: 'Hi! 👋 I’m SecondLife AI. How can I help you?'
};

const DEFAULT_SUGGESTIONS = [
  'What is SecondLife?',
  'Who developed SecondLife?',
  'What can I donate?',
  'How do I donate an item?',
  'How do I request an item?',
  'How does matching work?'
];

// Helper: Safely renders bot responses supporting bold text,
// bullet points, numbered lists, and line breaks
function renderFormattedMessage(text) {
  if (!text) return null;

  const lines = text.split('\n');

  return (
    <div className="space-y-1.5">
      {lines.map((line, lineIdx) => {
        if (!line.trim()) {
          return <div key={lineIdx} className="h-1.5" />;
        }

        const bulletMatch = line.match(
          /^\s*[•\-*]\s+(.*)$/
        );

        const numberMatch = line.match(
          /^\s*(\d+\.)\s+(.*)$/
        );

        let prefix = null;
        let content = line;

        if (bulletMatch) {
          prefix = (
            <span className="font-bold text-[#087A3F] mr-1.5 shrink-0">
              •
            </span>
          );

          content = bulletMatch[1];
        } else if (numberMatch) {
          prefix = (
            <span className="font-bold text-[#087A3F] mr-1.5 shrink-0">
              {numberMatch[1]}
            </span>
          );

          content = numberMatch[2];
        }

        const parts = content.split(/(\*\*.*?\*\*)/g);

        return (
          <div
            key={lineIdx}
            className={
              bulletMatch || numberMatch
                ? 'flex items-start pl-0.5'
                : ''
            }
          >
            {prefix}

            <span className="flex-1">
              {parts.map((part, partIdx) => {
                if (
                  part.startsWith('**') &&
                  part.endsWith('**') &&
                  part.length >= 4
                ) {
                  return (
                    <strong
                      key={partIdx}
                      className="font-bold text-slate-900"
                    >
                      {part.slice(2, -2)}
                    </strong>
                  );
                }

                return part;
              })}
            </span>
          </div>
        );
      })}
    </div>
  );
}

// --------------------------------------------------
// Character-by-character bot response streaming
// --------------------------------------------------
function streamBotMessage(text, setMessages) {
  const botId = `bot-${Date.now()}-${Math.random()}`;

  setMessages((prev) => [
    ...prev,
    {
      id: botId,
      sender: 'bot',
      text: ''
    }
  ]);

  let index = 0;
  const step = Math.max(1, Math.ceil(text.length / 50));

  const streamNextCharacter = () => {
    if (index >= text.length) {
      return;
    }

    index = Math.min(text.length, index + step);

    setMessages((prev) =>
      prev.map((message) =>
        message.id === botId
          ? {
              ...message,
              text: text.slice(0, index)
            }
          : message
      )
    );

    if (index < text.length) {
      setTimeout(streamNextCharacter, 16);
    }
  };

  streamNextCharacter();
}

export default function ChatWidget() {
  const [open, setOpen] = useState(false);

  const [input, setInput] = useState('');

  const [sending, setSending] = useState(false);

  const [messages, setMessages] = useState([
    INITIAL_MESSAGE
  ]);

  const [suggestions, setSuggestions] = useState(
    DEFAULT_SUGGESTIONS
  );

  const messagesEndRef = useRef(null);

  // --------------------------------------------------
  // Auto scroll
  // --------------------------------------------------

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: 'smooth'
    });
  }, [messages, sending]);

  // --------------------------------------------------
  // Reset / New Chat
  // --------------------------------------------------

  const resetChat = () => {
    setMessages([
      {
        ...INITIAL_MESSAGE,
        id: `welcome-${Date.now()}`
      }
    ]);

    setSuggestions(DEFAULT_SUGGESTIONS);

    setInput('');

    setSending(false);
  };

  // --------------------------------------------------
  // Send message directly to Render production backend
  // --------------------------------------------------

  const sendMessage = async (messageOverride = null) => {
    const text = (
      messageOverride !== null
        ? messageOverride
        : input
    ).trim();

    if (!text || sending) return;

    const userMessage = {
      id: `user-${Date.now()}-${Math.random()}`,
      sender: 'user',
      text
    };

    setMessages((prev) => [
      ...prev,
      userMessage
    ]);

    setInput('');

    setSending(true);

    try {
      let data = null;

      try {
        const response = await api.post('/chat/', { message: text });
        data = response.data;
      } catch (apiErr) {
        console.warn('[SecondLife Chatbot] Primary api call failed, attempting fallback...', apiErr);

        // Fallback strategies:
        // 1. Same-origin proxy /api/chat/
        // 2. Direct Render URL https://second-life-e45t.onrender.com/api/chat/
        const fallbackUrls = [
          '/api/chat/',
          'https://second-life-e45t.onrender.com/api/chat/'
        ];

        let success = false;
        for (const url of fallbackUrls) {
          try {
            const fetchRes = await fetch(url, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ message: text })
            });
            if (fetchRes.ok) {
              data = await fetchRes.json();
              success = true;
              break;
            }
          } catch (fetchErr) {
            console.warn(`[SecondLife Chatbot] Fallback fetch failed for ${url}:`, fetchErr);
          }
        }

        if (!success || !data) {
          throw apiErr;
        }
      }

      const reply =
        typeof data?.reply === 'string'
          ? data.reply
          : typeof data?.answer === 'string'
          ? data.answer
          : typeof data?.response === 'string'
          ? data.response
          : typeof data?.message === 'string'
          ? data.message
          : typeof data?.text === 'string'
          ? data.text
          : '';

      console.log(
        '[SecondLife Chatbot] User message:',
        text
      );

      console.log(
        '[SecondLife Chatbot] API response:',
        data
      );

      console.log(
        '[SecondLife Chatbot] Reply:',
        reply
      );

      if (!reply) {
        throw new Error(
          'Empty response received from chatbot.'
        );
      }

      // --------------------------------------------------
      // Stream bot response character by character
      // --------------------------------------------------

      streamBotMessage(reply, setMessages);

      const nextSuggestions =
        Array.isArray(data?.suggestions) &&
        data.suggestions.length > 0
          ? data.suggestions
          : DEFAULT_SUGGESTIONS;

      setSuggestions(nextSuggestions);
    } catch (error) {
      console.error(
        '[SecondLife Chatbot] error:',
        error
      );

      const errorMessage = {
        id: `bot-err-${Date.now()}-${Math.random()}`,
        sender: 'bot',
        text:
          'Sorry, I am unable to connect with SecondLife right now. Please try again in a moment.'
      };

      setMessages((prev) => [
        ...prev,
        errorMessage
      ]);

      setSuggestions(DEFAULT_SUGGESTIONS);
    } finally {
      setSending(false);
    }
  };

  // --------------------------------------------------
  // Enter key
  // --------------------------------------------------

  const handleKeyDown = (e) => {
    if (
      e.key === 'Enter' &&
      !e.shiftKey
    ) {
      e.preventDefault();

      sendMessage();
    }
  };

  // --------------------------------------------------
  // Suggestion click
  // --------------------------------------------------

  const handleSuggestionClick = (suggestion) => {
    sendMessage(suggestion);
  };

  return (
    <div className="fixed bottom-4 right-4 sm:bottom-6 sm:right-6 z-[9999]">

      {/* ==================================================
          CHAT WINDOW
      ================================================== */}

      {open && (
        <div
          className="
            absolute
            bottom-[68px]
            right-0
            w-[360px]
            max-w-[calc(100vw-24px)]
            sm:max-w-[calc(100vw-32px)]
            h-[min(560px,calc(100vh-100px))]
            bg-white
            rounded-2xl
            shadow-2xl
            border
            border-slate-200
            overflow-hidden
            flex
            flex-col
          "
        >

          {/* ==================================================
              HEADER
          ================================================== */}

          <div className="bg-[#087A3F] px-4 py-3 flex items-center justify-between text-white shrink-0">

            <div className="flex items-center gap-3 min-w-0">

              <div className="w-9 h-9 rounded-full bg-white/15 flex items-center justify-center shrink-0">
                <Bot className="w-5 h-5" />
              </div>

              <div className="min-w-0">

                <div className="font-bold text-sm">
                  SecondLife AI
                </div>

                <div className="text-[11px] text-green-100 flex items-center gap-1">

                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-300" />

                  Online

                </div>

              </div>

            </div>

            <div className="flex items-center gap-1">

              {/* New Chat */}

              <button
                type="button"
                onClick={resetChat}
                title="New chat"
                className="
                  w-8
                  h-8
                  rounded-lg
                  hover:bg-white/10
                  flex
                  items-center
                  justify-center
                  transition
                "
              >
                <RotateCcw className="w-4 h-4" />
              </button>

              {/* Close */}

              <button
                type="button"
                onClick={() => setOpen(false)}
                title="Close"
                className="
                  w-8
                  h-8
                  rounded-lg
                  hover:bg-white/10
                  flex
                  items-center
                  justify-center
                  transition
                "
              >
                <X className="w-5 h-5" />
              </button>

            </div>

          </div>

          {/* ==================================================
              MESSAGES
          ================================================== */}

          <div className="flex-1 overflow-y-auto bg-slate-50 p-3 sm:p-4 space-y-4">

            {messages.map((message) => (

              <div
                key={message.id}
                className={`flex ${
                  message.sender === 'user'
                    ? 'justify-end'
                    : 'justify-start'
                }`}
              >

                <div
                  className={`flex items-end gap-2 max-w-[88%] ${
                    message.sender === 'user'
                      ? 'flex-row-reverse'
                      : ''
                  }`}
                >

                  {/* Avatar */}

                  <div
                    className={`
                      w-7
                      h-7
                      rounded-full
                      shrink-0
                      flex
                      items-center
                      justify-center
                      ${
                        message.sender === 'user'
                          ? 'bg-slate-200 text-slate-600'
                          : 'bg-[#087A3F] text-white'
                      }
                    `}
                  >

                    {message.sender === 'user' ? (
                      <User className="w-4 h-4" />
                    ) : (
                      <Bot className="w-4 h-4" />
                    )}

                  </div>

                  {/* Bubble */}

                  <div
                    className={`
                      px-3.5
                      py-2.5
                      rounded-2xl
                      text-sm
                      leading-relaxed
                      whitespace-pre-wrap
                      break-words
                      ${
                        message.sender === 'user'
                          ? 'bg-[#087A3F] text-white rounded-br-md whitespace-pre-wrap'
                          : 'bg-white text-slate-700 border border-slate-200 rounded-bl-md shadow-xs'
                      }
                    `}
                  >

                    {message.sender === 'bot'
                      ? renderFormattedMessage(
                          message.text
                        )
                      : message.text}

                  </div>

                </div>

              </div>

            ))}

            {/* Backend waiting indicator */}

            {sending && (
              <div className="flex justify-start">

                <div className="flex items-end gap-2">

                  <div className="w-7 h-7 rounded-full bg-[#087A3F] text-white flex items-center justify-center">
                    <Bot className="w-4 h-4" />
                  </div>

                  <div className="bg-white border border-slate-200 rounded-2xl rounded-bl-md px-4 py-3 shadow-xs">

                    <div className="flex items-center gap-1.5">

                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-bounce" />

                      <span
                        className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-bounce"
                        style={{
                          animationDelay: '150ms'
                        }}
                      />

                      <span
                        className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-bounce"
                        style={{
                          animationDelay: '300ms'
                        }}
                      />

                    </div>

                  </div>

                </div>

              </div>
            )}

            <div ref={messagesEndRef} />

          </div>

          {/* ==================================================
              SUGGESTIONS
          ================================================== */}

          {!sending &&
            suggestions.length > 0 && (

              <div className="px-3 sm:px-4 pt-2 pb-2 bg-white border-t border-slate-100 shrink-0">

                <div className="flex items-center gap-1.5 mb-2">

                  <Sparkles className="w-3.5 h-3.5 text-[#087A3F]" />

                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">
                    Suggested questions
                  </span>

                </div>

                <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-thin">

                  {suggestions
                    .slice(0, 5)
                    .map((suggestion, index) => (

                      <button
                        key={`${suggestion}-${index}`}
                        type="button"
                        onClick={() =>
                          handleSuggestionClick(
                            suggestion
                          )
                        }
                        className="
                          shrink-0
                          text-[11px]
                          font-semibold
                          text-[#087A3F]
                          bg-emerald-50
                          border
                          border-emerald-100
                          hover:bg-emerald-100
                          rounded-full
                          px-3
                          py-1.5
                          transition
                        "
                      >
                        {suggestion}
                      </button>

                    ))}

                </div>

              </div>

            )}

          {/* ==================================================
              INPUT
          ================================================== */}

          <div className="p-3 bg-white border-t border-slate-200 shrink-0">

            <div className="flex items-center gap-2">

              <input
                type="text"
                value={input}
                onChange={(e) =>
                  setInput(e.target.value)
                }
                onKeyDown={handleKeyDown}
                disabled={sending}
                placeholder={
                  sending
                    ? 'SecondLife AI is typing...'
                    : 'Ask SecondLife AI...'
                }
                className="
                  flex-1
                  min-w-0
                  h-11
                  px-4
                  rounded-xl
                  border
                  border-slate-200
                  text-sm
                  outline-none
                  focus:border-[#087A3F]
                  focus:ring-2
                  focus:ring-green-100
                  disabled:bg-slate-50
                  disabled:text-slate-400
                "
              />

              <button
                type="button"
                onClick={() => sendMessage()}
                disabled={
                  !input.trim() || sending
                }
                className="
                  w-11
                  h-11
                  rounded-xl
                  bg-[#087A3F]
                  text-white
                  flex
                  items-center
                  justify-center
                  hover:bg-[#066832]
                  disabled:opacity-40
                  disabled:cursor-not-allowed
                  transition
                  shrink-0
                "
              >
                <Send className="w-4 h-4" />
              </button>

            </div>

          </div>

        </div>
      )}

      {/* ==================================================
          FLOATING CHAT BUTTON
      ================================================== */}

      <button
        type="button"
        onClick={() =>
          setOpen((prev) => !prev)
        }
        aria-label={
          open
            ? 'Close SecondLife AI'
            : 'Open SecondLife AI'
        }
        className="
          h-14
          px-4
          sm:px-5
          rounded-full
          bg-[#087A3F]
          text-white
          shadow-lg
          hover:bg-[#066832]
          hover:scale-[1.02]
          active:scale-95
          transition-all
          flex
          items-center
          gap-2
          sm:gap-3
        "
      >

        <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center shrink-0">

          {open ? (
            <X className="w-4 h-4" />
          ) : (
            <Bot className="w-4 h-4" />
          )}

        </div>

        <span className="font-bold text-sm whitespace-nowrap">
          SecondLife AI
        </span>

        <span className="w-2 h-2 rounded-full bg-emerald-300 shrink-0" />

      </button>

    </div>
  );
}