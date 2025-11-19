import { useState } from "react";

function ChatInput({ disabled, onSend }) {
  const [value, setValue] = useState("");

  const handleSubmit = (event) => {
    event.preventDefault();
    if (!value.trim()) {
      return;
    }

    onSend(value);
    setValue("");
  };

  return (
    <form className="chat-input" onSubmit={handleSubmit}>
      <label htmlFor="chat-text" className="sr-only">
        Ask the assistant
      </label>
      <input
        id="chat-text"
        type="text"
        placeholder="Ask me about your analytics data..."
        value={value}
        onChange={(event) => setValue(event.target.value)}
        disabled={disabled}
      />
      <button type="submit" disabled={disabled}>
        {disabled ? "Sending..." : "Send"}
      </button>
    </form>
  );
}

export default ChatInput;
