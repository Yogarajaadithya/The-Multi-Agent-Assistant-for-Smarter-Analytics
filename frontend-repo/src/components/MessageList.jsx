function MessageList({ messages, isSending }) {
  if (!messages.length) {
    return (
      <section className="message-list empty">
        <p>Start the conversation to see responses here.</p>
      </section>
    );
  }

  return (
    <section className="message-list">
      {messages.map((message, index) => (
        <article className={`message ${message.role}`} key={index}>
          <span className="role-label">
            {message.role === "user" ? "You" : "Assistant"}
          </span>
          <p>{message.content}</p>
        </article>
      ))}
      {isSending && (
        <article className="message assistant typing">
          <span className="role-label">Assistant</span>
          <p>Thinking…</p>
        </article>
      )}
    </section>
  );
}

export default MessageList;
